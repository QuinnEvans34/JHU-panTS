import gzip
import io
import json
import tarfile
import zipfile

import pytest

from scripts.acquisition import extract_sources as ex

UNIT = pytest.mark.unit
COMPONENT = pytest.mark.component
INJECT = pytest.mark.failure_injection

PAYLOAD = {'PanTS_00000001/ct.nii.gz': b'volume-one', 'PanTS_00000002/ct.nii.gz': b'volume-two'}


@pytest.fixture(autouse=True)
def stub_mount(monkeypatch):
    """The real mounted() shells out to diskutil; identity checking is covered by its own tool."""
    monkeypatch.setattr(ex, 'mounted', lambda mount, uuid, device=None: 1)
    # Synthetic archives use laptop temp storage, not the 4 TB external volume.
    # Model healthy capacity explicitly; failure tests override this value.
    monkeypatch.setattr(ex, 'free_bytes', lambda _: 4 * 1024**4)


@pytest.fixture
def guard(tmp_path):
    return ex.Guard(tmp_path, device=1, floor=0, interval=10**6)


def noop(*args):
    pass


@COMPONENT
def test_promotion_never_replaces_existing_empty_directory(tmp_path):
    partial, final = tmp_path / 'partial', tmp_path / 'final'
    partial.mkdir()
    final.mkdir()
    (partial / 'evidence').write_bytes(b'keep')
    with pytest.raises(FileExistsError):
        ex.promote_exclusive(partial, final)
    assert (partial / 'evidence').read_bytes() == b'keep'
    assert not list(final.iterdir())


@COMPONENT
def test_zip_change_during_extraction_is_rejected(tmp_path, guard, monkeypatch):
    archive = make_zip(tmp_path / 'a.zip')
    real = ex.archive_identity
    calls = 0
    def changed(path):
        nonlocal calls
        calls += 1
        value = real(path)
        return value if calls == 1 else (*value[:-1], value[-1] + 1)
    monkeypatch.setattr(ex, 'archive_identity', changed)
    with pytest.raises(ValueError, match='Archive changed'):
        ex.extract_zip(archive, tmp_path / 'out', guard, noop)


@UNIT
def test_budget_includes_all_reserves_and_rounds_up(tmp_path, monkeypatch):
    required = 11 + 2 + ex.CACHE_RESERVE + ex.RETRY_RESERVE + ex.FLOOR
    monkeypatch.setattr(ex, 'free_bytes', lambda _: required)
    assert ex.require_budget(tmp_path, 11) == required
    monkeypatch.setattr(ex, 'free_bytes', lambda _: required - 1)
    with pytest.raises(RuntimeError, match='budget'):
        ex.require_budget(tmp_path, 11)


def make_tar(path, payload=PAYLOAD, dirs=True):
    with tarfile.open(path, 'w:gz') as out:
        for name, body in payload.items():
            if dirs:
                directory = tarfile.TarInfo(name.split('/')[0])
                directory.type = tarfile.DIRTYPE
                out.addfile(directory)
            member = tarfile.TarInfo(name)
            member.size = len(body)
            out.addfile(member, io.BytesIO(body))
    return path


def make_zip(path, payload=PAYLOAD):
    with zipfile.ZipFile(path, 'w') as out:
        for name, body in payload.items():
            out.writestr(name, body)
    return path


def oracle(payload=PAYLOAD, directories=2, sha256=None):
    return dict(files=len(payload), directories=directories,
                expanded_bytes=sum(len(v) for v in payload.values()), sha256=sha256)


def run(tmp_path, archive_name, expected, **kwargs):
    source, dest = tmp_path / 'src', tmp_path / 'dest'
    source.mkdir(exist_ok=True)
    dest.mkdir(exist_ok=True)
    return ex.extract_archive(archive_name, source, dest, expected, tmp_path, 'uuid',
                              kwargs.pop('allow_existing', False), **kwargs)


# --- happy paths ------------------------------------------------------------------------------

@COMPONENT
def test_tar_round_trip_promotes_and_matches_content(tmp_path):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_tar(tmp_path / 'src' / 'a.tar.gz')
    result = run(tmp_path, 'a.tar.gz', oracle())
    final = tmp_path / 'dest' / 'a'
    assert final.is_dir() and not list((tmp_path / 'dest').glob('*.partial-*'))
    assert result['files'] == 2 and result['expanded_bytes'] == 20
    for name, body in PAYLOAD.items():
        assert (final / name).read_bytes() == body


@COMPONENT
def test_zip_round_trip_promotes(tmp_path):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_zip(tmp_path / 'src' / 'b.zip')
    run(tmp_path, 'b.zip', oracle(directories=0))
    final = tmp_path / 'dest' / 'b'
    assert final.is_dir()
    for name, body in PAYLOAD.items():
        assert (final / name).read_bytes() == body


@COMPONENT
def test_pinned_digest_is_verified(tmp_path):
    (tmp_path / 'src').mkdir(exist_ok=True)
    path = make_tar(tmp_path / 'src' / 'a.tar.gz')
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    result = run(tmp_path, 'a.tar.gz', oracle(sha256=digest))
    assert result['sha256'] == digest


# --- refusals ---------------------------------------------------------------------------------

@COMPONENT
def test_invalid_existing_destination_is_refused_not_overwritten(tmp_path, capsys):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_tar(tmp_path / 'src' / 'a.tar.gz')
    (tmp_path / 'dest').mkdir(exist_ok=True)
    marker = tmp_path / 'dest' / 'a'
    marker.mkdir()
    (marker / 'prior').write_bytes(b'keep me')
    with pytest.raises(ValueError, match='does not match pinned'):
        run(tmp_path, 'a.tar.gz', oracle())
    assert (marker / 'prior').read_bytes() == b'keep me'
    assert 'archive_already_extracted' not in capsys.readouterr().out


@COMPONENT
@pytest.mark.parametrize('kind', ['tar', 'zip'])
def test_cumulative_size_limit_precedes_second_file_write(tmp_path, guard, monkeypatch, kind):
    monkeypatch.setattr(ex, 'MAX_EXPANDED', 15)
    payload = {'first': b'a' * 10, 'second': b'b' * 10}
    out = tmp_path / 'out'
    out.mkdir()
    if kind == 'tar':
        archive = make_tar(tmp_path / 'a.tar.gz', payload, dirs=False)
        extract = ex.extract_tar
    else:
        archive = make_zip(tmp_path / 'a.zip', payload)
        extract = ex.extract_zip
    with pytest.raises(ValueError, match='resource ceiling'):
        extract(archive, out, guard, noop)
    assert (out / 'first').stat().st_size == 10
    assert not (out / 'second').exists()


@UNIT
def test_metadata_verification_does_not_claim_content_integrity(tmp_path):
    target = tmp_path / 'file'
    target.write_bytes(b'original')
    before = ex.measure_tree(tmp_path)
    target.write_bytes(b'changed!')
    assert ex.measure_tree(tmp_path) == before


@UNIT
def test_verify_refuses_symlink_root(tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    link = tmp_path / 'link'
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match='Ordinary extracted directory'):
        ex.measure_tree(link)


@UNIT
def test_floor_check_happens_before_payload_write(tmp_path, guard, monkeypatch):
    monkeypatch.setattr(ex, 'free_bytes', lambda _: 3)
    with pytest.raises(RuntimeError, match='would fall below'):
        ex.write_member(io.BytesIO(b'1234'), tmp_path / 'file', 4, guard, noop)
    assert (tmp_path / 'file').stat().st_size == 0


@COMPONENT
def test_previous_partial_blocks_until_acknowledged(tmp_path):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_tar(tmp_path / 'src' / 'a.tar.gz')
    (tmp_path / 'dest').mkdir(exist_ok=True)
    stale = tmp_path / 'dest' / 'a.partial-20260101T000000Z'
    stale.mkdir()
    with pytest.raises(ValueError, match='previous partial attempt'):
        run(tmp_path, 'a.tar.gz', oracle())
    assert stale.is_dir(), 'the stale attempt must be preserved, never reused or deleted'
    run(tmp_path, 'a.tar.gz', oracle(), allow_existing=True)
    assert (tmp_path / 'dest' / 'a').is_dir() and stale.is_dir()


@COMPONENT
def test_unsafe_member_refused(tmp_path, guard):
    path = make_tar(tmp_path / 'evil.tar.gz', {'../escape': b'x'}, dirs=False)
    with pytest.raises(ValueError, match='Unsafe member'):
        ex.extract_tar(path, tmp_path / 'out', guard, noop)


@COMPONENT
def test_truncated_archive_refused(tmp_path, guard):
    path = make_tar(tmp_path / 'a.tar.gz')
    path.write_bytes(path.read_bytes()[:-5])
    (tmp_path / 'out').mkdir()
    with pytest.raises((EOFError, tarfile.ReadError, gzip.BadGzipFile)):
        ex.extract_tar(path, tmp_path / 'out', guard, noop)


@COMPONENT
def test_trailing_data_after_tar_end_refused(tmp_path, guard):
    path = make_tar(tmp_path / 'a.tar.gz')
    path.write_bytes(path.read_bytes() + gzip.compress(b'appended'))
    (tmp_path / 'out').mkdir()
    with pytest.raises(ValueError, match='after tar end'):
        ex.extract_tar(path, tmp_path / 'out', guard, noop)


@COMPONENT
def test_oracle_mismatch_refuses_promotion_and_keeps_partial(tmp_path):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_tar(tmp_path / 'src' / 'a.tar.gz')
    wrong = dict(oracle(), files=99)
    with pytest.raises(ValueError, match='does not match pinned'):
        run(tmp_path, 'a.tar.gz', wrong)
    assert not (tmp_path / 'dest' / 'a').exists()
    assert list((tmp_path / 'dest').glob('a.partial-*')), 'evidence must survive for inspection'


@COMPONENT
def test_wrong_pinned_digest_refuses_promotion(tmp_path):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_tar(tmp_path / 'src' / 'a.tar.gz')
    with pytest.raises(ValueError, match='digest does not match'):
        run(tmp_path, 'a.tar.gz', oracle(sha256='0' * 64))
    assert not (tmp_path / 'dest' / 'a').exists()


@UNIT
def test_member_longer_than_declared_is_refused(tmp_path, guard):
    with pytest.raises(ValueError, match='more bytes than it declared'):
        ex.write_member(io.BytesIO(b'toolong'), tmp_path / 'f', 3, guard, noop)


@UNIT
def test_member_shorter_than_declared_is_refused(tmp_path, guard):
    with pytest.raises(ValueError, match='fewer bytes than it declared'):
        ex.write_member(io.BytesIO(b'ab'), tmp_path / 'f', 3, guard, noop)


@UNIT
def test_existing_file_is_never_overwritten(tmp_path, guard):
    target = tmp_path / 'f'
    target.write_bytes(b'original')
    with pytest.raises(FileExistsError):
        ex.write_member(io.BytesIO(b'new'), target, 3, guard, noop)
    assert target.read_bytes() == b'original'


@UNIT
def test_path_length_ceiling(tmp_path):
    with pytest.raises(ValueError, match='supported length'):
        ex.target_for(tmp_path, '/'.join(['x' * 200] * 10))


@UNIT
def test_path_length_is_checked_before_the_symlink_walk(tmp_path, monkeypatch):
    """Regression, and an ordering assertion rather than a platform accident.

    macOS lstat() raises a bare ENAMETOOLONG past PATH_MAX (1024), so walking the parent chain
    first masked the real message; Linux's 4096 limit hid the bug entirely. Asserting that
    under() is never reached proves the order on any platform.
    """
    def unreachable(*args, **kwargs):
        raise AssertionError('under() must not run for a path already known to be too long')

    monkeypatch.setattr(ex, 'under', unreachable)
    with pytest.raises(ValueError, match='supported length'):
        ex.target_for(tmp_path, '/'.join(['x' * 200] * 10))


@UNIT
def test_target_cannot_escape_the_partial_root(tmp_path):
    with pytest.raises(ValueError, match='escapes'):
        ex.under(tmp_path.parent / 'elsewhere', tmp_path)


# --- interruption and capacity ------------------------------------------------------------------

@INJECT
def test_interruption_leaves_only_a_partial(tmp_path, monkeypatch):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_tar(tmp_path / 'src' / 'a.tar.gz')
    calls = {'n': 0}
    real = ex.write_member

    def flaky(*args, **kwargs):
        calls['n'] += 1
        if calls['n'] == 2:
            raise RuntimeError('simulated kill')
        return real(*args, **kwargs)

    monkeypatch.setattr(ex, 'write_member', flaky)
    with pytest.raises(RuntimeError, match='simulated kill'):
        run(tmp_path, 'a.tar.gz', oracle())
    assert not (tmp_path / 'dest' / 'a').exists(), 'the final name must never appear'
    partials = list((tmp_path / 'dest').glob('a.partial-*'))
    assert len(partials) == 1 and list(partials[0].rglob('*')), 'partial retained and visible'


@INJECT
def test_free_space_floor_stops_extraction(tmp_path):
    path = make_tar(tmp_path / 'a.tar.gz')
    (tmp_path / 'out').mkdir()
    tight = ex.Guard(tmp_path, device=1, floor=2**62, interval=0)
    with pytest.raises(RuntimeError, match='below the operational floor'):
        ex.extract_tar(path, tmp_path / 'out', tight, noop)


# --- verify mode ---------------------------------------------------------------------------------

@COMPONENT
def test_verify_detects_a_tree_that_no_longer_matches(tmp_path):
    (tmp_path / 'src').mkdir(exist_ok=True)
    make_tar(tmp_path / 'src' / 'a.tar.gz')
    run(tmp_path, 'a.tar.gz', oracle())
    final = tmp_path / 'dest' / 'a'
    assert ex.measure_tree(final)['files'] == 2
    (final / 'PanTS_00000001' / 'ct.nii.gz').unlink()
    with pytest.raises(ValueError, match='files 1 does not match pinned 2'):
        ex.check_expected(ex.measure_tree(final), oracle(), 'a.tar.gz', ('files', 'expanded_bytes'))


# --- expectations loading -------------------------------------------------------------------------

@UNIT
def test_load_expected_reads_scan_log_and_zip_preflight(tmp_path):
    log = tmp_path / 'scan.jsonl'
    log.write_text('\n'.join([
        json.dumps(dict(event='scan_started', archives=1)),
        json.dumps(dict(event='archive_scanned', archive='a.tar.gz', files=2, directories=2,
                        expanded_bytes=20, sha256='abc')),
        '']))
    pre = tmp_path / 'pre.json'
    pre.write_text(json.dumps(dict(archives=[dict(archive='b.zip', files=3, directories=0,
                                                  declared_expanded_bytes=30)])))
    expected = ex.load_expected([log, pre])
    assert expected['a.tar.gz'] == dict(files=2, directories=2, expanded_bytes=20, sha256='abc')
    assert expected['b.zip']['expanded_bytes'] == 30 and expected['b.zip']['sha256'] is None


@UNIT
def test_refuses_to_extract_without_pinned_expectations(tmp_path):
    empty = tmp_path / 'empty.jsonl'
    empty.write_text('')
    with pytest.raises(ValueError, match='refusing to extract unverified'):
        ex.load_expected([empty])


@UNIT
def test_stem_rejects_unknown_suffixes():
    assert ex.stem('PanTSMini_Label.tar.gz') == 'PanTSMini_Label'
    assert ex.stem('batch_1.zip') == 'batch_1'
    with pytest.raises(ValueError, match='Unsupported archive suffix'):
        ex.stem('mystery.7z')


# --- regression: controls that were silently inert -------------------------------------------

@COMPONENT
def test_appended_data_is_detected_by_scan_and_extractor(tmp_path, guard):
    """Regression for a control that was dead code.

    Reading the stream after tarfile finishes cannot work: gzip.GzipFile concatenates members
    transparently and tarfile's stream mode consumes to EOF, so nothing remains. The equivalent
    guard in scripts/diagnostics/scan_pants_archives.py never fires for this reason. The
    extractor compares decompressed bytes against where the last member actually ends instead.
    """
    from scripts.diagnostics.scan_pants_archives import scan
    path = make_tar(tmp_path / 'a.tar.gz')
    path.write_bytes(path.read_bytes() + gzip.compress(b'appended'))

    with pytest.raises(ValueError, match='after tar end'):
        scan(path)

    (tmp_path / 'out').mkdir()
    with pytest.raises(ValueError, match='after tar end'):
        ex.extract_tar(path, tmp_path / 'out', guard, noop)


# --- rehearsal against the real archive shape --------------------------------------------------

@COMPONENT
def test_end_to_end_against_pinned_scan_log_format(tmp_path):
    """Mirrors PanTSMini_ImageTr_*: one directory per case, one volume inside each."""
    import hashlib
    (tmp_path / 'src').mkdir(exist_ok=True)
    payload = {f'PanTS_{i:08d}/ct.nii.gz': bytes([i % 251]) * (100 + i) for i in range(1, 26)}
    archive = tmp_path / 'src' / 'PanTSMini_ImageTr_00000001_00000025.tar.gz'
    make_tar(archive, payload)

    log = tmp_path / 'scan.jsonl'
    log.write_text(json.dumps(dict(
        at='2026-09-21T20:39:08Z', event='archive_scanned', archive=archive.name,
        files=len(payload), directories=len(payload),
        expanded_bytes=sum(len(v) for v in payload.values()),
        sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        issues={}, publisher_sha256_match=True)) + '\n')

    expected = ex.load_expected([log])
    result = ex.extract_archive(archive.name, tmp_path / 'src', tmp_path / 'dest',
                                expected[archive.name], tmp_path, 'uuid', False)
    final = tmp_path / 'dest' / 'PanTSMini_ImageTr_00000001_00000025'
    assert result['files'] == 25 and result['directories'] == 25
    assert final.is_dir() and not list((tmp_path / 'dest').glob('*.partial-*'))
    for name, body in payload.items():
        assert (final / name).read_bytes() == body
    # a second run is a no-op rather than a re-extraction
    assert ex.extract_archive(archive.name, tmp_path / 'src', tmp_path / 'dest',
                              expected[archive.name], tmp_path, 'uuid', False) is None
    ex.check_expected(ex.measure_tree(final), expected[archive.name], archive.name,
                      ('files', 'expanded_bytes'))
