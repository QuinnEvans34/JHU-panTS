"""Read-only checkout sanity check. This is not a filesystem permission boundary."""
from pathlib import Path
import subprocess
import sys


def check_workspace(cwd: Path, script_root: Path) -> Path:
    """Reject another working directory, nested repository, or incomplete checkout."""
    cwd, script_root = cwd.resolve(), script_root.resolve()
    if cwd != script_root:
        raise ValueError(f"Run from this script's repository root: {script_root}; got {cwd}")
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=cwd,
        check=True, capture_output=True, text=True,
    )
    if Path(result.stdout.strip()).resolve() != script_root:
        raise ValueError("Git root does not match this script's repository root")
    for marker in ("docs/capstone/README.md", "requirements/locks/macos-arm64-py312.txt"):
        if not (script_root / marker).is_file():
            raise ValueError(f"Missing PROWL marker: {marker}")
    return script_root


if __name__ == "__main__":
    try:
        root = check_workspace(Path.cwd(), Path(__file__).resolve().parents[2])
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Workspace check FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Workspace check passed: {root}")
    print("Confirm this is the intended checkout before editing; this check grants no permissions.")
