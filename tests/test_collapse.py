"""Tests for the 5->3 collapse helpers (Codex fix #2: mode is declared, never inferred).

Run:  python tests/test_collapse.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.inference.collapse import collapse_label_np, collapse_probs_np


def test_anatomy5_only_bg_body():
    """A lesion-free, tail-free case: labels {0,1,2}. Body(2) MUST become pancreas(1), NOT lesion."""
    lab = np.array([0, 1, 2, 2, 1, 0])
    out = collapse_label_np(lab, "anatomy5")
    assert out.tolist() == [0, 1, 1, 1, 1, 0], out.tolist()
    assert (out == 2).sum() == 0   # no lesion invented from body voxels


def test_anatomy5_only_bg_head():
    """labels {0,1} -> {0,1}."""
    lab = np.array([0, 1, 1, 0])
    assert collapse_label_np(lab, "anatomy5").tolist() == [0, 1, 1, 0]


def test_anatomy5_full():
    lab = np.array([0, 1, 2, 3, 4])
    assert collapse_label_np(lab, "anatomy5").tolist() == [0, 1, 1, 1, 2]


def test_pancreas_lesion_passthrough():
    lab = np.array([0, 1, 2, 1])
    assert collapse_label_np(lab, "pancreas_lesion").tolist() == [0, 1, 2, 1]


def test_probs_collapse_5ch():
    p = np.zeros((5, 2, 2, 2))
    p[1] = 0.2; p[2] = 0.3; p[3] = 0.1; p[4] = 0.15; p[0] = 0.25
    c = collapse_probs_np(p)
    assert c.shape[0] == 3
    assert np.allclose(c[1], 0.6)   # pancreas = head+body+tail = 0.2+0.3+0.1
    assert np.allclose(c[2], 0.15)  # lesion
    assert np.allclose(c[0], 0.25)


def test_probs_collapse_3ch_passthrough():
    p = np.random.rand(3, 2, 2, 2)
    assert np.allclose(collapse_probs_np(p), p)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"  PASS  {fn.__name__}")
    print(f"\nAll {len(fns)} collapse tests passed.")


if __name__ == "__main__":
    _run_all()
