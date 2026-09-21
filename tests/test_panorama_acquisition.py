"""Offline checksum, commit ZIP, retry and publication guards for the overnight queue."""
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
import zipfile

import pytest

from scripts.acquisition import download_panorama as downloader


def sample_zip(tmp_path, *, content=b"label", name="mask.nii.gz", mode="100644"):
    path = tmp_path / "labels.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("panorama_labels-abc/" + name, content)
    digest = hashlib.sha1(b"blob 5\0label", usedforsecurity=False).hexdigest()
    tree = {"truncated": False, "tree": [{"path": "mask.nii.gz", "type": "blob", "size": 5, "sha": digest, "mode": mode}]}
    return path, tree


def test_git_members_verified(tmp_path):
    path, tree = sample_zip(tmp_path)
    assert downloader.check_label_zip(path, tree, "abc") == 1


@pytest.mark.parametrize("content,name,mode", [(b"wrong", "mask.nii.gz", "100644"), (b"label", "../escape", "100644"), (b"label", "mask.nii.gz", "120000")])
def test_bad_label_member(tmp_path, content, name, mode):
    path, tree = sample_zip(tmp_path, content=content, name=name, mode=mode)
    with pytest.raises(ValueError):
        downloader.check_label_zip(path, tree, "abc")


def test_missing_label_member(tmp_path):
    path, tree = sample_zip(tmp_path)
    tree["tree"].append(dict(tree["tree"][0], path="missing"))
    with pytest.raises(ValueError, match="Missing"):
        downloader.check_label_zip(path, tree, "abc")


def test_truncated_git_tree(tmp_path):
    path, tree = sample_zip(tmp_path)
    tree["truncated"] = True
    with pytest.raises(ValueError, match="truncated"):
        downloader.check_label_zip(path, tree, "abc")


def test_publisher_md5_and_local_sha256(tmp_path):
    p = tmp_path / "ct.zip"
    p.write_bytes(b"known")
    item = {"bytes": 5, "publisher_md5": hashlib.md5(b"known").hexdigest()}
    assert downloader.digests(p, item)["sha256"] == hashlib.sha256(b"known").hexdigest()
    p.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="MD5"):
        downloader.digests(p, item)


def test_unknown_length_bound(tmp_path):
    p = tmp_path / "payload"
    p.write_bytes(b"too long")
    with pytest.raises(ValueError, match="bound"):
        downloader.digests(p, {"max_bytes": 2})


@pytest.mark.parametrize("code,expected", [(403, False), (404, False), (429, True), (503, True)])
def test_http_retry_classification(code, expected):
    assert downloader.transient(HTTPError("https://example.invalid", code, "test", {}, None)) is expected


def test_network_retry_but_not_integrity_error():
    assert downloader.transient(URLError("offline"))
    assert not downloader.transient(ValueError("checksum failure"))


def test_inventory_totals():
    inventory = json.loads((Path(__file__).parents[1] / "docs/capstone/data/acquisition-2026-09-19.json").read_text())
    assert sum(x["bytes"] for x in inventory["panorama"]["ct_archives"]) == 194181682590
