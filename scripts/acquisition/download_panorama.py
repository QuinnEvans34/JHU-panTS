"""Bounded standalone PANORAMA archive queue; no extraction, indexing, or training.

Zenodo payloads require publisher MD5 plus a recorded local SHA-256. The pinned
GitHub label ZIP is checked against every blob in the commit's Git tree without
extracting it. Partial CTs resume; incomplete non-range ZIP attempts are retained.
This does not implement Plan 04's scientific workflow or activate a source alias.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid as uuid_module
import zipfile

import yaml

from scripts.acquisition.download_pants import CHUNK, FLOOR, mounted, safe_directory, sha256, utc, validate_response


def digests(path, item):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Payload must be an ordinary file")
    if item.get("bytes") is not None and path.stat().st_size != item["bytes"]:
        raise ValueError("Payload size mismatch")
    if path.stat().st_size > item.get("max_bytes", item.get("bytes", 0)):
        raise ValueError("Payload exceeds approved bound")
    hashes = {"sha256": hashlib.sha256(), "md5": hashlib.md5(usedforsecurity=False)}
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            for digest in hashes.values():
                digest.update(chunk)
    result = {k: v.hexdigest() for k, v in hashes.items()}
    if item.get("publisher_md5") and result["md5"] != item["publisher_md5"]:
        raise ValueError("Publisher MD5 mismatch; retain bytes and stop")
    return result


def check_label_zip(path, tree, revision):
    if tree.get("truncated"):
        raise ValueError("Cannot verify against truncated Git tree")
    expected = {x["path"]: x for x in tree["tree"] if x["type"] == "blob"}
    if not expected or len(expected) != sum(x["type"] == "blob" for x in tree["tree"]):
        raise ValueError("Empty or duplicate blob inventory")
    prefix = f"panorama_labels-{revision}/"
    seen = set()
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            if not member.filename.startswith(prefix):
                raise ValueError("Unexpected archive prefix")
            name = member.filename[len(prefix):]
            if ".." in PurePosixPath(name).parts or "\\" in name or PurePosixPath(name).is_absolute():
                raise ValueError("Unsafe archive path")
            if member.is_dir():
                continue
            if name in seen or name not in expected:
                raise ValueError("Duplicate or unexpected archive member")
            reference = expected[name]
            if reference["mode"] not in {"100644", "100755"}:
                raise ValueError("Unsupported Git blob mode")
            mode = member.external_attr >> 16
            if (mode & 0o170000) == 0o120000:
                raise ValueError("ZIP symlink refused")
            if member.file_size != reference["size"]:
                raise ValueError("Expanded member size differs from Git tree")
            digest = hashlib.sha1(f'blob {member.file_size}\0'.encode(), usedforsecurity=False)
            with archive.open(member) as stream:
                for chunk in iter(lambda: stream.read(CHUNK), b""):
                    digest.update(chunk)
            if digest.hexdigest() != reference["sha"]:
                raise ValueError("Git blob hash mismatch")
            seen.add(name)
    if seen != set(expected):
        raise ValueError("Missing Git blobs")
    return len(seen)


def transient(exc):
    if isinstance(exc, HTTPError):
        return exc.code in {408, 429, 500, 502, 503, 504}
    return isinstance(exc, (URLError, TimeoutError, ConnectionError, http.client.IncompleteRead))


def transfer(item, directory, mount, volume_uuid, record, validator=None):
    name = item["name"]
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError("Unsafe destination name")
    device = mounted(mount, volume_uuid)
    final = directory / name
    if final.is_symlink():
        raise ValueError("Symlink destination refused")
    def verify(path):
        result = digests(path, item)
        if validator:
            result["verified_git_blobs"] = validator(path)
        return result
    if final.exists():
        record("verified_existing", name=name, **verify(final))
        return
    expected = item.get("bytes")
    bound = item.get("max_bytes", expected)
    # GitHub generated archives do not promise Range. Keep each failed attempt separately.
    suffix = ".part" if expected is not None else f".part-{uuid_module.uuid4().hex}"
    partial = directory / (name + suffix)
    if partial.is_symlink():
        raise ValueError("Symlink partial refused")
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > bound:
        raise ValueError("Oversize partial retained for review")
    if shutil.disk_usage(mount).free - (bound - offset) < FLOOR:
        raise RuntimeError("External free-space floor would be crossed")
    record("starting", name=name, resume_bytes=offset, expected_bytes=expected, max_bytes=bound, url=item["url"])
    if expected is None or offset < expected:
        headers = {"User-Agent": "PROWL-research-acquisition/1.0", "Accept-Encoding": "identity"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
        with urlopen(Request(item["url"], headers=headers), timeout=60) as response:
            if expected is not None:
                validate_response(response.status, response.headers, offset, expected)
            elif response.status != 200 or int(response.headers.get("Content-Length", "0")) > bound:
                raise ValueError("Unexpected archive response/status/size")
            mounted(mount, volume_uuid, device)
            flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW
            if not partial.exists():
                flags |= os.O_CREAT | os.O_EXCL
            with os.fdopen(os.open(partial, flags, 0o600), "ab") as stream:
                if os.fstat(stream.fileno()).st_dev != device:
                    raise RuntimeError("Payload is not on the expected volume")
                count = offset
                last_report = time.monotonic()
                for chunk in iter(lambda: response.read1(CHUNK), b""):
                    mounted(mount, None, device)
                    if count + len(chunk) > bound:
                        raise ValueError("Transfer exceeds approved byte bound")
                    if count // (64 * CHUNK) != (count + len(chunk)) // (64 * CHUNK):
                        if shutil.disk_usage(mount).free < FLOOR + len(chunk):
                            raise RuntimeError("External reserve exhausted")
                    stream.write(chunk)
                    count += len(chunk)
                    if time.monotonic() - last_report >= 30:
                        stream.flush()
                        record("progress", name=name, bytes=count, expected_bytes=expected)
                        last_report = time.monotonic()
                stream.flush()
                os.fsync(stream.fileno())
        if expected is not None and count != expected:
            raise ConnectionError("Short transfer retained for resume")
    mounted(mount, volume_uuid, device)
    result = verify(partial)
    if final.exists():
        raise FileExistsError("Refusing destination replacement")
    partial.rename(final)
    record("verified_download", name=name, bytes=final.stat().st_size, **result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--roots", type=Path, required=True)
    parser.add_argument("--zenodo-public-links", action="store_true",
                        help="Use each record's public download link, retaining the same size/hash requirements")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    config = yaml.safe_load(args.roots.read_text())
    primary = config["failure_domains"]["external_primary"]
    mount, volume_uuid = Path(primary["mount_path"]), primary["volume_uuid"]
    mounted(mount, volume_uuid)
    source = inventory["panorama"]
    revision = source["labels_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected fixed label commit")
    # Conservatively reserve both entire imaging queues plus six capped label attempts.
    needed = inventory["capacity"]["known_image_and_pants_label_archive_bytes"] + 12 * 1024**3
    if shutil.disk_usage(mount).free < needed + FLOOR:
        raise RuntimeError("Combined overnight archive budget fails reserve")
    parent = Path(config["roots"]["panorama_source"]["acquisition_parent"])
    directory = safe_directory(parent / ("acquisition-2026-09-19-" + revision[:12]), mount)
    lockfd = os.open(directory / ".download.lock", os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lockfd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        with (directory / f"attempt-{timestamp}.jsonl").open("x") as log:
            def record(event, **fields):
                line = json.dumps(dict(at=utc(), event=event, **fields), sort_keys=True)
                log.write(line + "\n")
                log.flush()
                os.fsync(log.fileno())
                print(line, flush=True)
            record("attempt_started", inventory_sha256=sha256(args.inventory),
                   script_sha256=sha256(Path(__file__)), helper_sha256=sha256(Path(__file__).with_name("download_pants.py")), extraction=False)
            try:
                tree_url = f"https://api.github.com/repos/DIAGNijmegen/panorama_labels/git/trees/{revision}?recursive=1"
                with urlopen(Request(tree_url, headers={"User-Agent": "PROWL-research-acquisition/1.0"}), timeout=60) as response:
                    raw = response.read(10 * 1024**2 + 1)
                if len(raw) > 10 * 1024**2:
                    raise ValueError("Git metadata exceeds bound")
                tree = json.loads(raw)
                if tree.get("truncated") or len([x for x in tree["tree"] if x["type"] == "blob"]) != source["labels_tree"]["blob_count"]:
                    raise ValueError("Pinned label inventory changed or is truncated")
                with (directory / f"label-tree-{timestamp}.json").open("xb") as output:
                    output.write(raw)
                record("label_tree_pinned", revision=revision, sha256=hashlib.sha256(raw).hexdigest())
                labels = {"name": f"panorama_labels-{revision}.zip", "url": source["labels_tree"]["archive_url"], "max_bytes": 2 * 1024**3}
                queue = [(labels, lambda path: check_label_zip(path, tree, revision))]
                for item in source["ct_archives"]:
                    if args.zenodo_public_links:
                        item = dict(item, url=f'https://zenodo.org/records/{item["record_id"]}/files/{item["name"]}?download=1')
                    queue.append((item, None))
                failures = []
                for item, validator in queue:
                    for retry in range(6):
                        try:
                            transfer(item, directory, mount, volume_uuid, record, validator)
                            break
                        except Exception as exc:
                            if not transient(exc):
                                raise
                            record("network_attempt_failed", name=item["name"], error_type=type(exc).__name__, retry=retry)
                            if retry == 5:
                                failures.append(item["name"])
                                record("file_deferred_network", name=item["name"], partials_retained=True)
                                break
                            delay = min(60, 5 * 2 ** retry)
                            if isinstance(exc, HTTPError) and exc.headers.get("Retry-After", "").isdigit():
                                delay = int(exc.headers["Retry-After"])
                            # Honor server delays without unbounded busy retries.
                            while delay > 0:
                                time.sleep(min(60, delay))
                                delay -= 60
                record("archive_queue_incomplete" if failures else "archive_queue_complete",
                       source_ready=False, network_deferred=failures)
            except BaseException as exc:
                record("attempt_stopped", error_type=type(exc).__name__, partials_retained=True)
                raise


if __name__ == "__main__":
    main()
