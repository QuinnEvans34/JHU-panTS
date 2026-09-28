"""Read-only tar.gz structure/size scan. No extraction or source activation.

Only aggregate results enter logs; member paths stay in memory. Drains gzip to EOF
for CRC validation and hashes compressed bytes during the same sequential read.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile
import time
import unicodedata

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.acquisition.download_pants import mounted


def emit(event, **values):
    print(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(), event=event, **values)), flush=True)


def inspect_member(member, seen, issues):
    name = member.name
    parts = PurePosixPath(name).parts
    if (not name or name.startswith('/') or '\\' in name or '..' in parts
            or re.match(r'^[A-Za-z]:', name) or any(ord(c) < 32 for c in name)):
        issues['unsafe_path'] += 1
    key = unicodedata.normalize('NFD', str(PurePosixPath(name))).casefold()
    if key in seen:
        issues['duplicate_or_case_unicode_collision'] += 1
    seen[key] = member.isdir()
    if not (member.isfile() or member.isdir()):
        issues['link_or_special_entry'] += 1
    if member.sparse is not None:
        issues['sparse_entry'] += 1
    if member.size < 0:
        issues['negative_size'] += 1


class Meter:
    def __init__(self, raw, size, progress):
        self.raw, self.size, self.progress = raw, size, progress
        self.hash = hashlib.sha256()
        self.count = 0
        self.last = self.start = time.monotonic()

    def read(self, n=-1):
        b = self.raw.read(n)
        self.hash.update(b)
        self.count += len(b)
        now = time.monotonic()
        if now-self.last >= 30:
            self.progress(self.count, self.size, now-self.start)
            self.last = now
        return b


class TarStreamAudit:
    """Track read-ahead too: tarfile may buffer bytes beyond its end marker."""
    def __init__(self, stream):
        self.stream, self.count, self.last_nonzero = stream, 0, -1

    def read(self, size=-1):
        data = self.stream.read(size)
        nonzero = data.rstrip(b'\0')
        if nonzero:
            self.last_nonzero = self.count + len(nonzero) - 1
        self.count += len(data)
        return data

    def finish(self, end):
        while self.read(1024 * 1024):
            if self.count - end > 16 * 1024**2:
                raise ValueError('Unexpected data after tar end; excessive padding')
        if (self.last_nonzero >= end or self.count < end + 1024
                or self.count - end > 16 * 1024**2 or self.count % 512):
            raise ValueError('Unexpected data after tar end; invalid terminator or padding')


def scan(path, progress=lambda *a: None, max_expanded=4*1024**4):
    if path.is_symlink() or path.resolve() != path:
        raise ValueError('Symlink archive/path refused')
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('Ordinary archive file required')
    seen, issues = {}, Counter()
    files = directories = total = 0
    end = 0
    with path.open('rb') as raw:
        meter = Meter(raw, before.st_size, progress)
        with gzip.GzipFile(fileobj=meter, mode='rb') as stream:
            audited = TarStreamAudit(stream)
            with tarfile.open(fileobj=audited, mode='r|', bufsize=1024*1024) as archive:
                for member in archive:
                    inspect_member(member, seen, issues)
                    end = max(end, member.offset_data + (member.size + 511) // 512 * 512)
                    if member.isfile():
                        files += 1
                        total += member.size
                    elif member.isdir():
                        directories += 1
                    if len(seen) > 2_000_000 or total > max_expanded:
                        raise ValueError('Member/expanded-size resource ceiling exceeded')
                    # Streaming iteration otherwise retains every TarInfo in Python 3.12.
                    archive.members.clear()
            audited.finish(end)
    for key in seen:
        for parent in PurePosixPath(key).parents:
            if str(parent) in seen and not seen[str(parent)]:
                issues['file_as_parent'] += 1
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Archive changed during scan')
    if meter.count != before.st_size:
        raise ValueError('Compressed stream not fully consumed')
    return dict(files=files, directories=directories, expanded_bytes=total,
                compressed_bytes=meter.count, sha256=meter.hash.hexdigest(), issues=dict(issues))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--inventory', type=Path, required=True)
    p.add_argument('--lock', type=Path, required=True)
    args = p.parse_args()
    reg = yaml.safe_load(args.registry.read_text())
    primary = reg['failure_domains']['external_primary']
    mount = Path(primary['mount_path'])
    device = mounted(mount, primary['volume_uuid'])
    base = mount/'PROWL/sources/pants/acquisition-3b1cd6110811'
    inv = json.loads(args.inventory.read_text())['pants']
    items = [x for x in inv['files'] if x['name'].endswith('.tar.gz')]
    items.append(dict(inv['labels'], name='PanTSMini_Label.tar.gz'))
    # Local lock only; never modify acquisition locks or the external filesystem.
    with args.lock.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        emit('scan_started', archives=len(items), pid=os.getpid(), read_only=True)
        total = 0
        for item in items:
            mounted(mount, primary['volume_uuid'], device)
            path = base/item['name']
            if path.stat().st_size != item['bytes']:
                raise ValueError('Archive size differs from pinned inventory')
            emit('archive_started', archive=item['name'], compressed_bytes=item['bytes'])

            def progress(n, size, seconds):
                mounted(mount, None, device)
                emit('progress', archive=item['name'], compressed_bytes_read=n,
                     compressed_bytes=size, elapsed_seconds=round(seconds, 1))

            result = scan(path, progress)
            mounted(mount, primary['volume_uuid'], device)
            expected = item.get('sha256')
            result['publisher_sha256_match'] = result['sha256'] == expected if expected else None
            emit('archive_scanned', archive=item['name'], **result)
            if result['issues'] or (expected and result['sha256'] != expected):
                raise ValueError('Safety or publisher hash check failed; no extraction permitted')
            total += result['expanded_bytes']
        emit('scan_complete', archives=len(items), expanded_bytes=total, source_ready=False,
             cross_archive_merge_validated=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        emit('scan_cancelled', source_ready=False)
        raise SystemExit(130)
    except Exception as exc:
        emit('scan_failed', error_type=type(exc).__name__, message=str(exc), source_ready=False)
        raise
