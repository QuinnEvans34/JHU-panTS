"""Tests for the serving/inference path (M4A1 §4). Run on the Mac (needs torch/MONAI):
    python tests/test_predict.py

Covers the checks Codex asked for that don't require a trained model or the external drive:
  * recipe verification raises on mismatch, passes on match, and handles missing metadata;
  * a predict_case-style summary is JSON-serializable (numpy scalars + NaN->None);
  * anatomy5 collapse helpers behave (delegated to test_collapse.py).
The model-dependent behaviors (unknown id -> KeyError, tumor-free -> lesion_dice None, real
anatomy5 collapse on a prediction) are exercised live via scripts/serve.py against a checkpoint —
documented in week4/ rather than unit-tested here, since they need a GPU + data.
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.inference.predict import verify_checkpoint_recipe


def _cfg(**over):
    cfg = {
        "label_mode": "pancreas_lesion",
        "model": {"out_channels": 3},
        "preprocessing": {"target_spacing": [1.5, 1.5, 1.5], "whole_box": True,
                          "roi_source": "pancreas", "crop_native_margin_vox": 16,
                          "crop_to_pancreas_margin_mm": None},
        "inference": {"sw_roi_size": [128, 128, 128]},
    }
    for k, v in over.items():
        cfg[k] = v
    return cfg


def _meta():
    return {"label_mode": "pancreas_lesion", "out_channels": 3, "target_spacing": [1.5, 1.5, 1.5],
            "sw_roi_size": [128, 128, 128], "whole_box": True, "roi_source": "pancreas",
            "crop_native_margin_vox": 16, "crop_to_pancreas_margin_mm": None}


def test_recipe_match_passes():
    verify_checkpoint_recipe(_meta(), _cfg())   # no raise


def test_recipe_mismatch_raises():
    bad = _meta(); bad["sw_roi_size"] = [96, 96, 96]
    try:
        verify_checkpoint_recipe(bad, _cfg())
        raise AssertionError("expected ValueError on recipe mismatch")
    except ValueError as e:
        assert "sw_roi_size" in str(e)


def test_missing_meta_optional_vs_required():
    verify_checkpoint_recipe({}, _cfg(), require_meta=False)   # allowed
    try:
        verify_checkpoint_recipe({}, _cfg(), require_meta=True)
        raise AssertionError("expected ValueError when meta required but absent")
    except ValueError:
        pass


def test_sparse_meta_tolerated_but_present_mismatch_raises():
    # sparse metadata (only some keys recorded) is tolerated — absent keys are NOT treated as None-mismatch
    sparse = {"label_mode": "pancreas_lesion", "sw_roi_size": [128, 128, 128]}
    verify_checkpoint_recipe(sparse, _cfg())   # no raise
    # but a PRESENT key that disagrees still raises
    raised = False
    try:
        verify_checkpoint_recipe({"label_mode": "anatomy5"}, _cfg())
    except ValueError:
        raised = True
    assert raised, "a present-but-mismatched key must still raise"


def test_summary_json_safe():
    def _f(x):
        return None if (x != x) else float(x)
    summary = {"case_id": "PanTS_x", "lesion_flagged": False, "lesion_volume_mm3": 0.0,
               "global_peak_lesion_confidence": 0.12, "retained_peak_lesion_confidence": 0.0,
               "pancreas_dice_cleaned": _f(0.81), "lesion_dice_cleaned": _f(float("nan"))}
    s = json.loads(json.dumps(summary))
    assert s["lesion_dice_cleaned"] is None       # tumor-free -> None, not NaN
    assert s["pancreas_dice_cleaned"] == 0.81


def test_predict_case_unknown_id_raises_keyerror():
    """A case_id not in the split must raise KeyError (before any model work)."""
    import unittest.mock as m
    from src.inference import predict as pmod
    with m.patch.object(pmod, "P") as P, m.patch.object(pmod, "load_split_ids", return_value=["A", "B"]):
        P.data_paths.return_value = {"splits_dir": "x"}
        try:
            pmod.load_single_case(_cfg(), "test", "NOT_IN_SPLIT")
            raise AssertionError("expected KeyError for unknown case_id")
        except KeyError:
            pass


def test_predict_case_numpy_nan_conversion():
    """Run predict_case with mocked I/O + inference: tumor-free GT -> lesion_dice None, all JSON-safe."""
    import unittest.mock as m
    import numpy as np
    import torch
    from src.inference import predict as pmod

    S = 8
    # GT: a pancreas blob (==1), NO lesion
    label = torch.zeros(1, 1, S, S, S)
    label[0, 0, 2:6, 2:6, 2:6] = 1
    # logits: background dominant everywhere, pancreas dominant ONLY in the blob (so pred ≈ GT).
    logits = torch.zeros(1, 3, S, S, S)
    logits[0, 0] = 3.0                          # background high by default
    logits[0, 1, 2:6, 2:6, 2:6] = 6.0           # pancreas wins inside the blob
    batch = {"image": torch.zeros(1, 1, S, S, S), "label": label, "case_id": ["PanTS_test"]}

    with m.patch.object(pmod, "load_single_case", return_value=batch), \
         m.patch.object(pmod, "predict_volume", return_value=logits):
        # model only needs .eval(); predict_volume is mocked, so the network is never actually called
        out = pmod.predict_case(_cfg(), model=m.MagicMock(), device="cpu", case_id="PanTS_test", split="test")

    json.dumps(out)                                   # must be JSON-safe (no numpy scalars / NaN)
    assert out["lesion_dice_cleaned"] is None         # tumor-free -> None
    assert out["lesion_flagged"] is False
    assert out["pancreas_dice_cleaned"] is not None and out["pancreas_dice_cleaned"] > 0.5
    assert isinstance(out["lesion_volume_mm3"], float)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    fails = []
    for fn in fns:
        try:
            fn(); print(f"  PASS  {fn.__name__}")
        except Exception as e:
            fails.append(fn.__name__); print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - len(fails)}/{len(fns)} passed.")
    if fails:
        sys.exit(1)   # fail closed so CI cannot report a false pass


if __name__ == "__main__":
    _run_all()
