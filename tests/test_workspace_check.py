from pathlib import Path
import subprocess

import pytest

from scripts.diagnostics.check_workspace import check_workspace


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "renamed-checkout"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for marker in ("docs/capstone/README.md", "requirements/locks/macos-arm64-py312.txt"):
        path = root / marker
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    return root


def test_arbitrary_checkout_name_is_supported(checkout):
    assert check_workspace(checkout, checkout) == checkout.resolve()


def test_other_working_directory_is_rejected(checkout, tmp_path):
    with pytest.raises(ValueError, match="Run from"):
        check_workspace(tmp_path, checkout)


def test_missing_project_marker_is_rejected(checkout):
    (checkout / "docs/capstone/README.md").unlink()
    with pytest.raises(ValueError, match="Missing PROWL marker"):
        check_workspace(checkout, checkout)


def test_nested_folder_cannot_impersonate_git_root(checkout):
    nested = checkout / "nested"
    nested.mkdir()
    with pytest.raises(ValueError, match="Git root"):
        check_workspace(nested, nested)
