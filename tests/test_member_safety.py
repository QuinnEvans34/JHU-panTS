import tarfile
import unicodedata
import zipfile

import pytest

from scripts.acquisition.member_safety import (MAX_COMPONENT_BYTES, Inspector, collision_key,
                                               from_tar, from_zip, path_issues)
from scripts.diagnostics.scan_pants_archives import inspect_member

pytestmark = pytest.mark.unit

UNSAFE_NAMES = ['../bad', 'a/../../bad', '/bad', 'C:/bad', 'a\\bad', 'bad\x01name', '']


def tar_member(name, kind=tarfile.REGTYPE, size=3):
    member = tarfile.TarInfo(name or '.')
    member.name = name
    member.type = kind
    member.size = size if kind == tarfile.REGTYPE else 0
    return member


def zip_member(name, *, mode=None, size=3, system=3):
    info = zipfile.ZipInfo(name)
    info.file_size = size
    info.create_system = system
    if mode is not None:
        info.external_attr = mode << 16
    return info


@pytest.mark.parametrize('name', UNSAFE_NAMES)
def test_unsafe_names_rejected(name):
    assert 'unsafe_path' in path_issues(name)


@pytest.mark.parametrize('name', ['folder/file.nii.gz', 'PanTS_00000001/ct.nii.gz', 'a.b/c-d_e'])
def test_ordinary_names_accepted(name):
    assert path_issues(name) == set()


def test_over_long_component():
    assert 'name_too_long' in path_issues('a/' + 'x' * (MAX_COMPONENT_BYTES + 1))
    assert 'name_too_long' not in path_issues('a/' + 'x' * MAX_COMPONENT_BYTES)


def test_multibyte_component_measured_in_bytes():
    # 200 three-byte characters is 600 bytes: legal as characters, illegal as a component.
    assert 'name_too_long' in path_issues('\u4e2d' * 200)


def test_duplicate_and_case_collision():
    inspector = Inspector()
    assert inspector.inspect('A', is_file=True, is_dir=False, size=1) == set()
    issues = inspector.inspect('a', is_file=True, is_dir=False, size=1)
    assert 'duplicate_or_case_unicode_collision' in issues


def test_unicode_normalisation_collision():
    composed, decomposed = 'caf\u00e9', unicodedata.normalize('NFD', 'caf\u00e9')
    assert composed != decomposed
    assert collision_key(composed) == collision_key(decomposed)
    inspector = Inspector()
    inspector.inspect(composed, is_file=True, is_dir=False, size=1)
    issues = inspector.inspect(decomposed, is_file=True, is_dir=False, size=1)
    assert 'duplicate_or_case_unicode_collision' in issues


def test_file_as_parent():
    inspector = Inspector()
    inspector.inspect('a', is_file=True, is_dir=False, size=1)
    inspector.inspect('a/child', is_file=True, is_dir=False, size=1)
    assert inspector.structural_issues()['file_as_parent'] == 1


def test_directory_parent_is_not_a_conflict():
    inspector = Inspector()
    inspector.inspect('a', is_file=False, is_dir=True, size=0)
    inspector.inspect('a/child', is_file=True, is_dir=False, size=1)
    assert inspector.structural_issues() == {}


@pytest.mark.parametrize('kind', [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE,
                                  tarfile.CHRTYPE, tarfile.BLKTYPE])
def test_link_and_special_entries(kind):
    inspector = Inspector()
    assert 'link_or_special_entry' in inspector.inspect(**from_tar(tar_member('x', kind)))


def test_sparse_and_negative_size():
    inspector = Inspector()
    assert 'sparse_entry' in inspector.inspect('s', is_file=True, is_dir=False, size=1,
                                               is_sparse=True)
    assert 'negative_size' in inspector.inspect('n', is_file=True, is_dir=False, size=-1)


def test_member_ceiling():
    inspector = Inspector(max_members=2)
    inspector.inspect('a', is_file=True, is_dir=False, size=1)
    inspector.inspect('b', is_file=True, is_dir=False, size=1)
    with pytest.raises(ValueError, match='ceiling'):
        inspector.inspect('c', is_file=True, is_dir=False, size=1)


def test_zip_symlink_detected_through_external_attr():
    # zipfile exposes no issym(); without the mode check this extracts as an ordinary file.
    info = zip_member('link', mode=0o120777)
    assert 'link_or_special_entry' in Inspector().inspect(**from_zip(info))


def test_zip_regular_and_directory_entries():
    assert Inspector().inspect(**from_zip(zip_member('f.txt', mode=0o100644))) == set()
    assert Inspector().inspect(**from_zip(zip_member('d/', mode=0o040755, size=0))) == set()


def test_zip_without_unix_attributes_is_treated_as_regular():
    assert Inspector().inspect(**from_zip(zip_member('f.txt', system=0))) == set()


def test_zip_zero_length_file_is_safe():
    assert Inspector().inspect(**from_zip(zip_member('empty', mode=0o100644, size=0))) == set()


# --- the property that keeps the two tools from diverging -------------------------------------

AGREEMENT_CORPUS = ([(name, tarfile.REGTYPE) for name in UNSAFE_NAMES] +
                    [('folder', tarfile.DIRTYPE), ('folder/a', tarfile.REGTYPE),
                     ('A', tarfile.REGTYPE), ('a', tarfile.REGTYPE),
                     ('a/child', tarfile.REGTYPE), ('link', tarfile.SYMTYPE),
                     ('hard', tarfile.LNKTYPE), ('pipe', tarfile.FIFOTYPE),
                     ('caf\u00e9', tarfile.REGTYPE),
                     (unicodedata.normalize('NFD', 'caf\u00e9'), tarfile.REGTYPE)])


def test_shared_module_is_a_superset_of_the_existing_scan():
    """member_safety may be stricter than scan_pants_archives; it may never be more permissive."""
    members = [tar_member(name, kind) for name, kind in AGREEMENT_CORPUS]

    scan_seen, scan_issues = {}, __import__('collections').Counter()
    for member in members:
        inspect_member(member, scan_seen, scan_issues)
    for key in scan_seen:
        for parent in __import__('pathlib').PurePosixPath(key).parents:
            if str(parent) in scan_seen and not scan_seen[str(parent)]:
                scan_issues['file_as_parent'] += 1

    inspector = Inspector()
    shared = __import__('collections').Counter()
    for member in members:
        for issue in inspector.inspect(**from_tar(member)):
            shared[issue] += 1
    shared.update(inspector.structural_issues())

    for issue, count in scan_issues.items():
        assert shared[issue] >= count, f'{issue}: shared module raised {shared[issue]} < scan {count}'
