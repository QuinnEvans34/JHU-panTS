"""Standalone, archive-only PanTS acquisition. Not a Plan 04 runner or source activator.

Keeps partials, validates publisher hashes, never extracts/deletes, and refuses a missing
or different mounted volume. Run with the pinned inventory and ignored local registry.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

import yaml

CHUNK = 1024 * 1024
FLOOR = 512 * 1024**3


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path, item):
    if path.is_symlink() or path.stat().st_size != item["bytes"]:
        raise ValueError("File type/size differs from acquisition inventory")
    actual = sha256(path)
    if item.get("sha256") and actual != item["sha256"]:
        raise ValueError("SHA-256 mismatch; retain file for investigation")
    return actual


def validate_response(status, headers, offset, expected, etag=None):
    if status != (206 if offset else 200):
        raise ValueError("Server did not honor the requested transfer/resume mode")
    if offset and headers.get("Content-Range") != f"bytes {offset}-{expected - 1}/{expected}":
        raise ValueError("Unexpected Content-Range")
    if headers.get("Content-Length") is not None:
        if int(headers["Content-Length"]) != expected - offset:
            raise ValueError("Unexpected response length")
    if etag and headers.get("ETag") != etag:
        raise ValueError("Mutable label URL changed its pinned entity validator")


def mounted(mount, uuid, device=None):
    if mount.is_symlink() or not mount.is_mount() or mount.resolve() != mount:
        raise RuntimeError("Expected external mount absent; no fallback path will be created")
    if device is not None and mount.stat().st_dev != device:
        raise RuntimeError("Mounted filesystem changed during transfer")
    if uuid is not None:
        info = plistlib.loads(subprocess.check_output(["diskutil", "info", "-plist", str(mount)]))
        if info.get("VolumeUUID") != uuid or info.get("FilesystemType") != "apfs":
            raise RuntimeError("External volume identity/filesystem mismatch")
    return mount.stat().st_dev


def safe_directory(path, mount):
    if not path.is_relative_to(mount):
        raise ValueError("Acquisition path escapes the external mount")
    current = mount
    for part in path.relative_to(mount).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink in acquisition directory")
        current.mkdir(exist_ok=True)
    return path


def download(item, directory, mount, uuid, record):
    name = item["name"]
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError("Unsafe inventory filename")
    device = mounted(mount, uuid)
    final = directory / name
    partial = directory / (name + ".part")
    if final.is_symlink() or partial.is_symlink():
        raise ValueError("Symlink payload refused")
    if final.exists():
        record("verified_existing", name=name, bytes=item["bytes"], sha256=verify_file(final, item))
        return
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > item["bytes"]:
        raise ValueError("Oversize partial retained; manual review required")
    if shutil.disk_usage(mount).free - (item["bytes"] - offset) < FLOOR:
        raise RuntimeError("Transfer would cross the 512 GiB external free-space floor")
    record("starting", name=name, resume_bytes=offset, expected_bytes=item["bytes"])
    if offset < item["bytes"]:
        headers = {"User-Agent": "PROWL-research-acquisition/1.0", "Accept-Encoding": "identity"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        if item.get("etag"):
            headers["If-Match"] = item["etag"]
        request = Request(item["url"], headers=headers)
        with urlopen(request, timeout=60) as response:
            validate_response(response.status, response.headers, offset, item["bytes"], item.get("etag"))
            mounted(mount, uuid, device)
            flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW
            flags |= os.O_CREAT | os.O_EXCL if not partial.exists() else 0
            with os.fdopen(os.open(partial, flags, 0o600), "ab") as stream:
                if os.fstat(stream.fileno()).st_dev != device:
                    raise RuntimeError("Payload is not on the verified external volume")
                count = offset
                last_report = time.monotonic()
                for chunk in iter(lambda: response.read(CHUNK), b""):
                    mounted(mount, None, device)
                    if count + len(chunk) > item["bytes"]:
                        raise ValueError("Server sent more bytes than the pinned inventory")
                    if count // (64 * CHUNK) != (count + len(chunk)) // (64 * CHUNK):
                        if shutil.disk_usage(mount).free < FLOOR + len(chunk):
                            raise RuntimeError("External free-space reserve exhausted")
                    stream.write(chunk)
                    count += len(chunk)
                    if time.monotonic() - last_report >= 30:
                        stream.flush()
                        record("progress", name=name, bytes=count, expected_bytes=item["bytes"])
                        last_report = time.monotonic()
                stream.flush()
                os.fsync(stream.fileno())
        if count != item["bytes"]:
            raise ConnectionError("Short transfer; partial retained for safe resume")
    mounted(mount, uuid, device)
    actual = verify_file(partial, item)
    if final.exists():
        raise FileExistsError("Destination appeared unexpectedly; refusing overwrite")
    partial.rename(final)
    record("verified_download", name=name, bytes=item["bytes"], sha256=actual,
           publisher_sha256_available=bool(item.get("sha256")), etag=item.get("etag"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--roots", type=Path, required=True)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    registry = yaml.safe_load(args.roots.read_text())
    primary = registry["failure_domains"]["external_primary"]
    mount = Path(primary["mount_path"])
    uuid = primary["volume_uuid"]
    mounted(mount, uuid)
    revision = inventory["pants"]["huggingface_revision"]
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Expected immutable publisher revision")
    root = Path(registry["roots"]["pants_source"]["acquisition_parent"])
    directory = safe_directory(root / ("acquisition-" + revision[:12]), mount)
    labels = dict(inventory["pants"]["labels"], name="PanTSMini_Label.tar.gz")
    files = inventory["pants"]["files"]
    # Metadata, labels, training images, then opaque protected publisher-test archive.
    queue = [files[0], labels, *files[1:]]
    if sum(x["bytes"] for x in queue) + FLOOR > shutil.disk_usage(mount).free:
        raise RuntimeError("Conservative entire-queue capacity check failed")
    lockpath = directory / ".download.lock"
    lockfd = os.open(lockpath, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lockfd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        attempt = directory / ("attempt-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".jsonl")
        with attempt.open("x") as log:
            def record(event, **fields):
                line = json.dumps(dict(at=utc(), event=event, **fields), sort_keys=True)
                log.write(line + "\n")
                log.flush()
                os.fsync(log.fileno())
                print(line, flush=True)
            record("attempt_started", inventory_sha256=sha256(args.inventory),
                   script_sha256=sha256(Path(__file__)), files=len(queue), extraction=False)
            try:
                for item in queue:
                    for retry in range(3):
                        try:
                            download(item, directory, mount, uuid, record)
                            break
                        except (URLError, ConnectionError, TimeoutError) as exc:
                            record("network_attempt_failed", name=item["name"], error_type=type(exc).__name__, retry=retry)
                            if retry == 2:
                                raise
                            time.sleep(2 ** retry)
                record("archive_queue_complete", source_ready=False,
                       next_step="Archive safety/expanded-size inventory, extraction, source/cohort reconciliation")
            except BaseException as exc:
                record("attempt_stopped", error_type=type(exc).__name__, partials_retained=True)
                raise


if __name__ == "__main__":
    main()
