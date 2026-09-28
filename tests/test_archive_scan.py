import hashlib
import gzip
import io
import tarfile

import pytest

from scripts.diagnostics.scan_pants_archives import scan

pytestmark = pytest.mark.unit


def make_archive(tmp_path, entries):
    path = tmp_path/'synthetic.tar.gz'
    with tarfile.open(path, 'w:gz') as out:
        for name, kind in entries:
            member = tarfile.TarInfo(name)
            member.type = kind
            if kind == tarfile.REGTYPE:
                member.size = 3
                out.addfile(member, io.BytesIO(b'abc'))
            else:
                member.linkname = 'target'
                out.addfile(member)
    return path


def test_counts_and_compressed_hash(tmp_path):
    p = make_archive(tmp_path, [('folder', tarfile.DIRTYPE), ('folder/a', tarfile.REGTYPE)])
    result = scan(p)
    assert result['expanded_bytes'] == 3
    assert result['files'] == result['directories'] == 1
    assert result['sha256'] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert result['issues'] == {}


@pytest.mark.parametrize('name', ['../bad', '/bad', 'C:/bad', 'a\\bad'])
def test_unsafe_paths(tmp_path, name):
    assert scan(make_archive(tmp_path, [(name, tarfile.REGTYPE)]))['issues']['unsafe_path'] == 1


def test_links_and_collisions(tmp_path):
    p = make_archive(tmp_path, [('A', tarfile.REGTYPE), ('a', tarfile.REGTYPE),
                                ('a/child', tarfile.REGTYPE), ('link', tarfile.SYMTYPE)])
    issues = scan(p)['issues']
    assert issues['duplicate_or_case_unicode_collision'] == 1
    assert issues['file_as_parent'] == 1
    assert issues['link_or_special_entry'] == 1


def test_truncated_gzip_rejected(tmp_path):
    p = make_archive(tmp_path, [('a', tarfile.REGTYPE)])
    p.write_bytes(p.read_bytes()[:-5])
    with pytest.raises((EOFError, tarfile.ReadError)):
        scan(p)


def test_resource_ceiling(tmp_path):
    p = make_archive(tmp_path, [('a', tarfile.REGTYPE)])
    with pytest.raises(ValueError, match='ceiling'):
        scan(p, max_expanded=2)


@pytest.mark.parametrize('fmt', [tarfile.USTAR_FORMAT, tarfile.GNU_FORMAT, tarfile.PAX_FORMAT])
def test_valid_tar_formats_and_extra_zero_blocks(tmp_path, fmt):
    p = tmp_path / 'format.tar.gz'
    with tarfile.open(p, 'w:gz', format=fmt) as out:
        member = tarfile.TarInfo('a' if fmt == tarfile.USTAR_FORMAT else 'a' * 150)
        member.size = 3
        out.addfile(member, io.BytesIO(b'abc'))
    p.write_bytes(p.read_bytes() + gzip.compress(bytes(10240)))
    assert scan(p)['files'] == 1


@pytest.mark.parametrize('mutation', ['append', 'padding', 'missing_terminator'])
def test_tar_end_validation_includes_read_ahead(tmp_path, mutation):
    p = make_archive(tmp_path, [('a', tarfile.REGTYPE)])
    raw = gzip.decompress(p.read_bytes())
    if mutation == 'append':
        p.write_bytes(p.read_bytes() + gzip.compress(b'extra'))
    elif mutation == 'padding':
        p.write_bytes(gzip.compress(raw[:2048] + b'x' + raw[2049:]))
    else:
        p.write_bytes(gzip.compress(raw[:1024]))
    with pytest.raises(ValueError, match='after tar end'):
        scan(p)
