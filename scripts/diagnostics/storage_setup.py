"""Bounded Plan 10 filesystem diagnostic; NOT a production artifact/workflow writer.

Creates only the explicitly approved workspace/backup paths and unique small test folders.
Preserves all test evidence, including failures. No deletion, repair, disconnect, or migration.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import sys
import tempfile

import numpy as np
from jsonschema import Draft202012Validator, FormatChecker


GIB = 1024 ** 3
REPO = Path(__file__).resolve().parents[2]


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def disk_info(path):
    return plistlib.loads(subprocess.check_output(
        ["diskutil", "info", "-plist", str(path)], timeout=20))


def free_bytes(path):
    info = os.statvfs(path)
    return info.f_bavail * info.f_frsize


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def safe_directory(path):
    check(path.is_absolute() and path.resolve() == path, f"Unsafe/symlink path: {path}")
    path.mkdir(exist_ok=True)
    check(path.is_dir() and not path.is_symlink(), f"Not a plain directory: {path}")


def used_bytes(root):
    total = 0
    for path in root.rglob("*"):
        check(not path.is_symlink(), f"Unexpected link in backup tree: {path}")
        if path.is_file():
            total += path.stat().st_size
    return total


def run(args):
    mount, backup = args.primary_mount, args.backup_root
    check(mount.is_mount() and mount.resolve() == mount, "Primary is not the expected real mount")
    info = disk_info(mount)
    check(info.get("VolumeUUID") == args.expected_uuid, "Wrong primary UUID")
    check(info.get("MountPoint") == str(mount), "Wrong primary mount path")
    check(info.get("FilesystemType") == "apfs", "Primary is not APFS")
    check(not info.get("ReadOnly", False), "Primary is read-only")
    check(backup.parent.is_dir() and backup.resolve() == backup, "Unsafe backup path")
    internal = disk_info(Path("/System/Volumes/Data"))
    check(internal.get("VolumeUUID") == args.expected_backup_uuid, "Wrong internal volume")
    check(backup.parent.stat().st_dev == Path("/System/Volumes/Data").stat().st_dev,
          "Backup is not on the expected internal volume")
    check(backup.parent.stat().st_dev != mount.stat().st_dev, "Backup shares the primary device")
    check(free_bytes(backup.parent) - 16 * 1024 ** 2 >= 100 * GIB, "Internal free-space floor")
    check(free_bytes(mount) >= 16 * 1024 ** 2, "Insufficient primary diagnostic space")
    if backup.exists():
        check(used_bytes(backup) + 16 * 1024 ** 2 <= 20 * GIB, "Backup budget exceeded")
    recovery_before = {p.name: [p.stat().st_size, p.stat().st_mtime_ns]
                       for p in mount.glob("JHU-PanTS-recovery.*")}
    workspace = mount / "PROWL"
    safe_directory(workspace)
    safe_directory(backup)
    probe = Path(tempfile.mkdtemp(prefix=".storage-check-", dir=workspace))
    report = {"schema_version": "1.0.0", "kind": "one_off_storage_diagnostic",
              "approval": "D-258", "status": "running", "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "probe": str(probe), "backup_root": str(backup), "checks": {},
              "primary_volume_uuid": info["VolumeUUID"], "internal_volume_uuid": internal["VolumeUUID"],
              "backup_cap_bytes": 20 * GIB, "internal_free_floor_bytes": 100 * GIB,
              "script_sha256": digest(Path(__file__)),
              "limitations": ["Not a production writer/resolver/backup service", "No power-loss or disconnect test",
                              "No trained-model restore", "No hardware-health certification",
                              "No enforceable source-role permissions implemented; volume ownership is disabled"]}
    try:
        payload = bytes(range(256)) * 4096
        payload_hash = hashlib.sha256(payload).hexdigest()
        source = probe / "payload.before"
        write_new(source, payload)
        check(digest(source) == payload_hash, "Write/flush/reopen mismatch")
        renamed = probe / "payload.renamed"
        source.rename(renamed)
        check(not source.exists() and digest(renamed) == payload_hash, "Rename check failed")
        report["checks"]["write_fsync_reopen_same_volume_rename"] = "pass"

        review = json.loads((REPO / "tests/fixtures/contracts/review-event.synthetic.json").read_text())
        schema = json.loads((REPO / "docs/capstone/contracts/review-event.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        reviews = probe / "reviews.jsonl"
        lock = probe / "probe.lock"
        contender = (
            "import fcntl,sys; f=open(sys.argv[1],'rb'); "
            "\ntry: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)"
            "\nexcept BlockingIOError: sys.exit(23)"
            "\nsys.exit(0)"
        )
        with lock.open("xb") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            rival = subprocess.run([sys.executable, "-c", contender, str(lock)], timeout=10)
            check(rival.returncode == 23, "Competing process was not refused")
            for index in (1, 2):
                event = dict(review)
                event["review_event_id"] = f"review:00000000-0000-4000-8000-{index:012d}"
                validator.validate(event)
                with reviews.open("ab") as stream:
                    stream.write((json.dumps(event) + "\n").encode())
                    stream.flush()
                    os.fsync(stream.fileno())
        check(subprocess.run([sys.executable, "-c", contender, str(lock)], timeout=10).returncode == 0,
              "Lock was not released")
        events = [json.loads(line) for line in reviews.read_text().splitlines()]
        check(len(events) == 2, "Append count mismatch")
        for event in events:
            validator.validate(event)
        report["checks"]["cross_process_lock_refusal_release_jsonl_append"] = "pass"

        incomplete, complete = probe / "incomplete", probe / "complete"
        incomplete.mkdir(); complete.mkdir()
        write_new(incomplete / "payload", b"partial")
        write_new(complete / "COMPLETE", b"diagnostic marker only")
        discovered = [p.name for p in (incomplete, complete) if (p / "COMPLETE").is_file()]
        check(discovered == ["complete"], "Diagnostic marker filter exposed incomplete content")
        report["checks"]["diagnostic_only_completion_marker_filter"] = "pass"
        long_name = probe / ("safe-" + "a" * 180)
        write_new(long_name, b"long-safe-name")
        unicode_name = probe / "fixture-pancreas-\u0394"
        write_new(unicode_name, b"unicode")
        check(unicode_name.read_bytes() == b"unicode" and long_name.read_bytes() == b"long-safe-name",
              "Name roundtrip failed")
        case_name = probe / "CaseProbe"
        write_new(case_name, b"case")
        report["case_sensitive"] = not (probe / "caseprobe").exists()
        os.chmod(case_name, 0o600)
        report["recorded_mode_bits"] = oct(stat.S_IMODE(case_name.stat().st_mode))
        link = probe / "outside-probe"
        link.symlink_to(workspace, target_is_directory=True)
        check(not link.resolve().is_relative_to(probe), "Outside symlink not distinguishable")
        report["checks"]["name_roundtrip_case_observation_symlink_boundary"] = "pass"

        control = probe / "control.json"
        write_new(control, encoded({"kind": "synthetic-storage-control", "value": 42}))
        array_file = probe / "array.npy"
        with array_file.open("xb") as stream:
            np.save(stream, np.arange(24, dtype=np.int16).reshape(2, 3, 4), allow_pickle=False)
            stream.flush(); os.fsync(stream.fileno())
        members = [control, reviews, array_file]
        inventory = {p.name: {"sha256": digest(p), "bytes": p.stat().st_size} for p in members}
        destination = backup / probe.name.removeprefix(".")
        destination.mkdir(exist_ok=False)
        for member in members:
            write_new(destination / member.name, member.read_bytes())
            check(digest(destination / member.name) == inventory[member.name]["sha256"], "Backup mismatch")
        restore = probe / "restore-from-backup"
        restore.mkdir()
        # After this point restore reads backup bytes, not the original payloads.
        for name, expected in inventory.items():
            write_new(restore / name, (destination / name).read_bytes())
            check(digest(restore / name) == expected["sha256"], "Restore mismatch")
        check(json.loads((restore / "control.json").read_text())["value"] == 42, "Control consumer failed")
        for line in (restore / "reviews.jsonl").read_text().splitlines():
            validator.validate(json.loads(line))
        check(np.array_equal(np.load(restore / "array.npy", allow_pickle=False),
                             np.arange(24, dtype=np.int16).reshape(2, 3, 4)), "Array consumer failed")
        damaged = probe / "corrupt-copy.json"
        write_new(damaged, (destination / "control.json").read_bytes() + b"corruption")
        check(digest(damaged) != inventory["control.json"]["sha256"], "Corruption went undetected")
        report["checks"]["independent_copy_restore_consumers_corruption_detection"] = "pass"
        report["backup_catalog"] = {"status": "restore_tested_synthetic_only", "members": inventory,
                                     "location": str(destination)}

        for relative in ["sources", "sources/pants", "sources/panorama", "artifacts",
                         "artifacts/quarantine", "scratch"]:
            safe_directory(workspace / relative)
        recovery_after = {p.name: [p.stat().st_size, p.stat().st_mtime_ns]
                          for p in mount.glob("JHU-PanTS-recovery.*")}
        check(recovery_before == recovery_after, "Existing recovery-file metadata changed")
        report["checks"]["existing_recovery_file_size_mtime_unchanged"] = "pass"
        check(used_bytes(backup) <= 20 * GIB and free_bytes(backup) >= 100 * GIB, "Final backup capacity failed")
        report["primary_free_bytes"] = free_bytes(mount)
        report["internal_free_bytes"] = free_bytes(backup)
        report["status"] = "passed_scoped_diagnostic"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        write_new(probe / "report.json", encoded(report))
        print(json.dumps(report, indent=2))
    write_new(destination / "catalog.json", encoded(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-mount", type=Path, required=True)
    parser.add_argument("--expected-uuid", required=True)
    parser.add_argument("--backup-root", type=Path, required=True)
    parser.add_argument("--expected-backup-uuid", required=True)
    run(parser.parse_args())
