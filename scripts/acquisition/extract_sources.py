"""Standalone safe extraction of pinned PanTS/PANORAMA archives. Not a Plan 04 runner.

Each archive expands into a uniquely named partial directory and is renamed to its final name
ONLY after extraction checks pass. Existing names alone are not proof of integrity.
Never overwrites, never deletes, never activates a source alias, and never claims
source readiness. Design and rationale: docs/capstone/operations/EXTRACTION-DESIGN-2026-09-22.md

Only aggregates are emitted; member paths stay in memory.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import fcntl
import gzip
import json
import os
import stat
from pathlib import Path, PurePosixPath
import sys
import tarfile
import time
import zipfile

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.acquisition.download_pants import CHUNK, FLOOR, mounted
from scripts.acquisition.member_safety import Inspector, from_tar, from_zip
from scripts.diagnostics.scan_pants_archives import Meter, TarStreamAudit

INTERVAL = 30
MAX_PATH_BYTES = 1000
MAX_EXPANDED = 4 * 1024**4
CACHE_RESERVE = 1024**4
RETRY_RESERVE = 64 * 1024**3
SUFFIXES = ('.tar.gz', '.zip')


def emit(event, **values):
    print(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(), event=event, **values)), flush=True)


def stem(name):
    for suffix in SUFFIXES:
        if name.endswith(suffix):
            return name[:-len(suffix)]
    raise ValueError('Unsupported archive suffix')


def free_bytes(path):
    info = os.statvfs(path)
    return info.f_bavail * info.f_frsize


def promote_exclusive(partial, final):
    """macOS no-clobber rename, refusing symlink ancestors; no unsafe fallback."""
    if sys.platform != 'darwin':
        raise RuntimeError('Exclusive promotion currently qualified only on macOS')
    rename = ctypes.CDLL(None, use_errno=True).renamex_np
    rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    # macOS SDK sys/stdio.h: RENAME_EXCL | RENAME_NOFOLLOW_ANY.
    if rename(os.fsencode(partial), os.fsencode(final), 0x04 | 0x10):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def archive_identity(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Ordinary archive file required')
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def require_budget(mount, payload):
    if type(payload) is not int or payload < 0 or payload > MAX_EXPANDED:
        raise ValueError('Invalid expanded-size expectation')
    required = payload + (payload + 9) // 10 + CACHE_RESERVE + RETRY_RESERVE + FLOOR
    if free_bytes(mount) < required:
        raise RuntimeError('Insufficient extraction budget; preserve data and re-budget')
    return required


def under(path, root):
    """Reject a path outside root or reached through a symlink."""
    if path != root and not path.is_relative_to(root):
        raise ValueError('Path escapes its approved root')
    current = root
    for part in path.relative_to(root).parts if path != root else ():
        current = current / part
        try:
            if current.is_symlink():
                raise ValueError('Symlink in approved path')
        except OSError as exc:
            raise ValueError(f'Path could not be verified: {exc.strerror}') from exc
    return path


class Guard:
    """Re-verifies the volume and free space during long writes, and paces progress events."""

    def __init__(self, mount, device, floor=FLOOR, interval=INTERVAL):
        self.mount, self.device, self.floor, self.interval = mount, device, floor, interval
        self.last = self.start = time.monotonic()

    def tick(self, report, force=False):
        now = time.monotonic()
        if not force and now - self.last < self.interval:
            return
        self.last = now
        mounted(self.mount, None, self.device)
        available = free_bytes(self.mount)
        if available < self.floor:
            raise RuntimeError('Free space fell below the operational floor; extraction stopped')
        report(round(now - self.start, 1), available)


def target_for(root, name):
    target = root.joinpath(*PurePosixPath(name).parts)
    # Checked before any syscall: lstat() on a path past the platform limit raises a bare
    # ENAMETOOLONG, which would mask this message and touch the filesystem to learn nothing.
    if len(str(target).encode('utf-8')) > MAX_PATH_BYTES:
        raise ValueError('Constructed path exceeds the supported length')
    under(target.parent, root)
    return target


def write_member(source, target, declared, guard, report):
    """Exclusive-create one member; the kernel enforces no-overwrite via O_EXCL."""
    if declared < 0 or declared > MAX_EXPANDED:
        raise ValueError('Expanded-size resource ceiling exceeded')
    guard.tick(report)
    if free_bytes(guard.mount) < guard.floor:
        raise RuntimeError('Free space fell below the operational floor; extraction stopped')
    target.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with target.open('xb') as out:
        while chunk := source.read(CHUNK):
            written += len(chunk)
            if written > declared:
                raise ValueError('Member wrote more bytes than it declared')
            if free_bytes(guard.mount) - len(chunk) < guard.floor:
                raise RuntimeError('Free space would fall below the operational floor')
            out.write(chunk)
            guard.tick(report)
    if written != declared:
        raise ValueError('Member wrote fewer bytes than it declared')
    return written


class Totals:
    def __init__(self, on_file=None):
        self.files = self.directories = self.expanded_bytes = 0
        self.on_file = on_file

    def add_dir(self):
        self.directories += 1

    def add_file(self, size):
        self.files += 1
        self.expanded_bytes += size
        if self.expanded_bytes > MAX_EXPANDED:
            raise ValueError('Expanded-size resource ceiling exceeded')
        if self.on_file:
            self.on_file(self.files, self.expanded_bytes)

    def asdict(self):
        return dict(files=self.files, directories=self.directories,
                    expanded_bytes=self.expanded_bytes)


def extract_tar(path, partial, guard, report, on_file=None):
    """Stream a .tar.gz, hashing compressed bytes so identity is proven without a second read."""
    before = path.stat()
    inspector, totals = Inspector(), Totals(on_file)
    end = 0
    with path.open('rb') as raw:
        meter = Meter(raw, before.st_size, lambda *a: guard.tick(report))
        with gzip.GzipFile(fileobj=meter, mode='rb') as stream:
            counted = TarStreamAudit(stream)
            with tarfile.open(fileobj=counted, mode='r|', bufsize=CHUNK) as archive:
                for member in archive:
                    issues = inspector.inspect(**from_tar(member))
                    if issues:
                        raise ValueError(f'Unsafe member rejected: {sorted(issues)}')
                    target = target_for(partial, member.name)
                    if member.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                        totals.add_dir()
                    else:
                        if totals.expanded_bytes + member.size > MAX_EXPANDED:
                            raise ValueError('Expanded-size resource ceiling exceeded')
                        source = archive.extractfile(member)
                        if source is None:
                            raise ValueError('Member offered no readable payload')
                        write_member(source, target, member.size, guard, report)
                        totals.add_file(member.size)
                    guard.tick(report)
                    end = max(end, member.offset_data + (member.size + 511) // 512 * 512)
                    # Streaming iteration otherwise retains every TarInfo in Python 3.12.
                    archive.members.clear()
            counted.finish(end)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Archive changed during extraction')
    if meter.count != before.st_size:
        raise ValueError('Compressed stream not fully consumed')
    issues = inspector.structural_issues()
    if issues:
        raise ValueError(f'Structural member conflict: {dict(issues)}')
    return dict(totals.asdict(), sha256=meter.hash.hexdigest())


def extract_zip(path, partial, guard, report, on_file=None):
    """Extract a .zip. zipfile validates each member's CRC-32 when the entry is read to EOF."""
    before = archive_identity(path)
    inspector, totals = Inspector(), Totals(on_file)
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            issues = inspector.inspect(**from_zip(info))
            if issues:
                raise ValueError(f'Unsafe member rejected: {sorted(issues)}')
            target = target_for(partial, info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                totals.add_dir()
            else:
                if totals.expanded_bytes + info.file_size > MAX_EXPANDED:
                    raise ValueError('Expanded-size resource ceiling exceeded')
                with archive.open(info) as source:
                    write_member(source, target, info.file_size, guard, report)
                totals.add_file(info.file_size)
            guard.tick(report)
    if archive_identity(path) != before:
        raise ValueError('Archive changed during extraction')
    issues = inspector.structural_issues()
    if issues:
        raise ValueError(f'Structural member conflict: {dict(issues)}')
    return dict(totals.asdict(), sha256=None)


def check_expected(result, expected, name, fields=('files', 'directories', 'expanded_bytes')):
    for field in fields:
        if expected.get(field) is not None and result[field] != expected[field]:
            raise ValueError(f'{name}: {field} {result[field]} does not match pinned {expected[field]}')
    pinned = expected.get('sha256')
    if pinned and result.get('sha256') and result['sha256'] != pinned:
        raise ValueError(f'{name}: archive digest does not match pinned evidence')


def measure_tree(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Ordinary extracted directory required')
    totals = Totals()
    def fail(error):
        raise error
    for current, directories, files in os.walk(root, onerror=fail):
        base = Path(current)
        for entry in directories:
            if (base / entry).is_symlink():
                raise ValueError('Symlink found in an extracted tree')
            totals.add_dir()
        for entry in files:
            item = base / entry
            if not stat.S_ISREG(item.lstat().st_mode):
                raise ValueError('Non-regular file found in an extracted tree')
            totals.add_file(item.stat().st_size)
    return totals.asdict()


def extract_archive(name, source_dir, dest_root, expected, mount, uuid, allow_existing):
    """Extract one archive into a partial directory and promote it only once verified."""
    archive_path = under(source_dir / name, source_dir)
    if archive_path.is_symlink() or not archive_path.is_file():
        raise ValueError('Ordinary archive file required')
    final = under(dest_root / stem(name), dest_root)
    if final.exists():
        check_expected(measure_tree(final), expected, name, ('files', 'expanded_bytes'))
        emit('archive_already_extracted', archive=name, destination=final.name,
             verification='metadata_only', content_integrity_verified=False)
        return None
    stale = sorted(p.name for p in dest_root.glob(f'{stem(name)}.partial-*'))
    if stale and not allow_existing:
        emit('existing_partial_preserved', archive=name, partials=stale)
        raise ValueError('A previous partial attempt exists; inspect it, then pass '
                         '--allow-existing-partial to extract into a new attempt directory')

    device = mounted(mount, uuid)
    require_budget(mount, expected.get('expanded_bytes'))
    guard = Guard(mount, device)
    guard.tick(lambda *args: None, force=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    partial = under(dest_root / f'{stem(name)}.partial-{stamp}', dest_root)
    partial.mkdir(parents=True, exist_ok=False)
    emit('archive_started', archive=name, partial=partial.name,
         expected_files=expected.get('files'), expected_bytes=expected.get('expanded_bytes'))

    started = time.monotonic()
    state = dict(files=0, bytes=0)

    def report(elapsed, available):
        emit('progress', archive=name, files_written=state['files'], bytes_written=state['bytes'],
             expected_bytes=expected.get('expanded_bytes'), elapsed_seconds=elapsed,
             free_bytes=available)

    def on_file(files, written):
        state['files'], state['bytes'] = files, written

    extractor = extract_zip if name.endswith('.zip') else extract_tar
    result = extractor(archive_path, partial, guard, report, on_file)

    check_expected(result, expected, name)
    mounted(mount, uuid, device)
    # Best-effort filesystem flush, not a power-loss durability certification.
    os.sync()
    mounted(mount, uuid, device)
    promote_exclusive(partial, final)
    os.sync()
    elapsed = round(time.monotonic() - started, 1)
    emit('archive_extracted', archive=name, destination=final.name, elapsed_seconds=elapsed,
         throughput_bytes_per_second=round(result['expanded_bytes'] / max(elapsed, 0.001)),
         source_ready=False, **result)
    return result


def load_expected(paths):
    """Merge pinned expectations from the tar scan log and the ZIP preflight report."""
    expected = {}
    for path in paths:
        text = path.read_text()
        if path.suffix == '.jsonl':
            for line in text.splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get('event') == 'archive_scanned':
                    expected[record['archive']] = {k: record[k] for k in
                                                   ('files', 'directories', 'expanded_bytes', 'sha256')}
        else:
            for record in json.loads(text)['archives']:
                expected[record['archive']] = dict(
                    files=record['files'], directories=record['directories'],
                    expanded_bytes=record['declared_expanded_bytes'], sha256=None)
    if not expected:
        raise ValueError('No pinned expectations were loaded; refusing to extract unverified')
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--expectations', type=Path, action='append', required=True)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--dest-root', type=Path, required=True)
    parser.add_argument('--lock', type=Path, required=True)
    parser.add_argument('--archive', action='append', default=[],
                        help='Archive filename; repeatable. Default: every pinned archive present.')
    parser.add_argument('--allow-existing-partial', action='store_true')
    parser.add_argument('--verify', action='store_true',
                        help='Re-check already promoted trees against pinned expectations.')
    args = parser.parse_args()

    registry = yaml.safe_load(args.registry.read_text())
    primary = registry['failure_domains']['external_primary']
    mount, uuid = Path(primary['mount_path']), primary['volume_uuid']
    device = mounted(mount, uuid)
    source_dir = under(args.source_dir.resolve(), mount)
    dest_root = under(args.dest_root.resolve(), mount)
    expected = load_expected(args.expectations)
    names = args.archive or [n for n in expected if (source_dir / n).exists()]
    missing = [n for n in names if n not in expected]
    if missing:
        raise ValueError(f'No pinned expectation for: {missing}')

    with args.lock.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.verify:
            emit('verify_started', archives=len(names), pid=os.getpid())
            for name in names:
                final = dest_root / stem(name)
                if not final.exists():
                    emit('verify_absent', archive=name)
                    raise ValueError('Requested extracted directory is absent')
                observed = measure_tree(final)
                check_expected(observed, expected[name], name, ('files', 'expanded_bytes'))
                emit('verify_passed', archive=name, observed_directories=observed['directories'],
                     verification='metadata_only', content_integrity_verified=False,
                     declared_directories=expected[name].get('directories'),
                     files=observed['files'], expanded_bytes=observed['expanded_bytes'])
            emit('verify_complete', archives=len(names), source_ready=False)
            return

        require_budget(mount, sum(expected[n]['expanded_bytes'] for n in names
                                  if not (dest_root / stem(n)).exists()))
        dest_root.mkdir(parents=True, exist_ok=True)
        emit('extraction_started', archives=len(names), pid=os.getpid(),
             free_bytes=free_bytes(mount), floor_bytes=FLOOR)
        done = 0
        for name in names:
            mounted(mount, uuid, device)
            if extract_archive(name, source_dir, dest_root, expected[name], mount, uuid,
                               args.allow_existing_partial) is not None:
                done += 1
        emit('extraction_complete', archives=len(names), extracted=done, source_ready=False,
             cohorts_reconciled=False, free_bytes=free_bytes(mount))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        emit('extraction_cancelled', source_ready=False,
             note='Partial directory retained; the final name was never created')
        raise SystemExit(130)
    except Exception as exc:
        emit('extraction_failed', error_type=type(exc).__name__, message=str(exc),
             source_ready=False)
        raise
