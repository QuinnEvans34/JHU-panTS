"""Offline acquisition guards; no network, external volumes, or raw data."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("download_pants", Path(__file__).parents[1] / "scripts/acquisition/download_pants.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_initial_response():
    module.validate_response(200, {"Content-Length": "10", "ETag": '"a"'}, 0, 10, '"a"')


def test_resumed_response():
    module.validate_response(206, {"Content-Length": "6", "Content-Range": "bytes 4-9/10"}, 4, 10)


@pytest.mark.parametrize("status,headers,offset,etag", [
    (200, {}, 4, None),
    (206, {"Content-Range": "bytes 0-9/10"}, 4, None),
    (200, {"Content-Length": "11"}, 0, None),
    (200, {"ETag": '"b"'}, 0, '"a"'),
    (200, {}, 0, '"a"'),
])
def test_bad_response_rejected(status, headers, offset, etag):
    with pytest.raises(ValueError):
        module.validate_response(status, headers, offset, 10, etag)


def test_verified_payload_and_corruption(tmp_path):
    target = tmp_path / "payload"
    target.write_bytes(b"known payload")
    item = {"bytes": 13, "sha256": hashlib.sha256(b"known payload").hexdigest()}
    assert module.verify_file(target, item) == item["sha256"]
    target.write_bytes(b"wrong payload")
    with pytest.raises(ValueError, match="SHA-256"):
        module.verify_file(target, item)


def test_short_payload(tmp_path):
    target = tmp_path / "payload"
    target.write_bytes(b"short")
    with pytest.raises(ValueError, match="size"):
        module.verify_file(target, {"bytes": 10})


def test_symlink_payload_refused(tmp_path):
    target = tmp_path / "payload"
    target.write_bytes(b"abc")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(ValueError):
        module.verify_file(link, {"bytes": 3})


def test_directory_escape_refused(tmp_path):
    with pytest.raises(ValueError):
        module.safe_directory(tmp_path.parent / "escape", tmp_path)


def test_symlink_directory_refused(tmp_path):
    (tmp_path / "link").symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):
        module.safe_directory(tmp_path / "link" / "new", tmp_path)


def test_missing_mount_refused(tmp_path):
    with pytest.raises(RuntimeError, match="mount absent"):
        module.mounted(tmp_path / "not-mounted", "not-a-uuid")
