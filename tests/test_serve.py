"""FastAPI endpoint behavior tests (M4A1 §4). Run on the Mac (needs fastapi + torch):
    python tests/test_serve.py

Tests the route functions directly (populating serve.STATE) to avoid the lifespan model load:
404 unknown case, 422 invalid split, 503 not-loaded / demo-missing, catalog, and /health fields.
"""
import json
import sys
import threading
import unittest.mock as m
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException

from scripts import serve


def _status(fn, *a, **k):
    try:
        fn(*a, **k)
        return None
    except HTTPException as e:
        return e.status_code


def _ok_state():
    return dict(model=object(), cfg={}, device="cpu", lock=threading.Lock(),
                ckpt_step=24000, ckpt_sha="abcd" * 16, label_mode="pancreas_lesion",
                roi=[128, 128, 128], spacing=[1.5, 1.5, 1.5], roi_source="pancreas",
                data_root_ok=True, demo_transform=object())


def test_predict_503_when_not_loaded():
    serve.STATE.clear()
    assert _status(serve.predict, serve.PredictRequest(case_id="X")) == 503


def test_predict_503_when_data_missing():
    serve.STATE.clear(); serve.STATE.update(_ok_state()); serve.STATE["data_root_ok"] = False
    assert _status(serve.predict, serve.PredictRequest(case_id="X")) == 503
    serve.STATE.clear()


def test_predict_422_bad_split():
    serve.STATE.clear(); serve.STATE.update(_ok_state())
    assert _status(serve.predict, serve.PredictRequest(case_id="X", split="train")) == 422
    serve.STATE.clear()


def test_predict_404_unknown_case():
    serve.STATE.clear(); serve.STATE.update(_ok_state())
    with m.patch.object(serve, "predict_demo_case", side_effect=KeyError("nope")):
        assert _status(serve.predict, serve.PredictRequest(case_id="X", split="test")) == 404
    serve.STATE.clear()


def test_predict_ok_adds_latency():
    serve.STATE.clear(); serve.STATE.update(_ok_state())
    with m.patch.object(serve, "predict_demo_case",
                        return_value={"case_id": "X", "lesion_flagged": False, "_mask": 1}):
        res = serve.predict(serve.PredictRequest(case_id="X", split="test"))
    assert "_mask" not in res and "inference_seconds" in res and res["checkpoint_step"] == 24000
    serve.STATE.clear()


def test_health_fields():
    serve.STATE.clear(); serve.STATE.update(_ok_state())
    h = serve.health()
    for k in ("status", "model", "checkpoint_step", "checkpoint_sha256", "label_mode",
              "roi", "spacing", "device", "data_root_available"):
        assert k in h
    serve.STATE.clear()


def test_cases_returns_sorted_sanitized_catalog():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        for case_id in ("PanTS_00000002", "PanTS_00000001"):
            case_dir = root / case_id
            case_dir.mkdir()
            (case_dir / "ct.nii.gz").touch()
            (case_dir / "gt.nii.gz").touch()
        incomplete = root / "PanTS_00000003"
        incomplete.mkdir()
        (incomplete / "ct.nii.gz").touch()
        (root / "results.json").write_text(json.dumps({
            "PanTS_00000002": {"label": "Small false positive"},
        }))
        with m.patch.object(serve, "_DEMO_CASES_DIR", root):
            assert serve.list_cases() == [
                {"case_id": "PanTS_00000001", "split": "test", "label": "PanTS 00000001"},
                {"case_id": "PanTS_00000002", "split": "test", "label": "Small false positive"},
            ]


def test_cases_missing_catalog_returns_generic_503():
    with TemporaryDirectory() as tmp:
        missing = Path(tmp) / "does-not-exist.txt"
        with m.patch.object(serve, "_DEMO_CASES_DIR", missing):
            try:
                serve.list_cases()
                raise AssertionError("expected HTTPException")
            except HTTPException as exc:
                assert exc.status_code == 503
                assert exc.detail == "case catalog unavailable"
                assert str(missing) not in exc.detail


def test_cases_never_returns_a_path_as_a_label():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        case_dir = root / "PanTS_00000001"
        case_dir.mkdir()
        (case_dir / "ct.nii.gz").touch()
        (case_dir / "gt.nii.gz").touch()
        (root / "results.json").write_text(json.dumps({
            "PanTS_00000001": {"label": "/private/data/secret.nii.gz"},
        }))
        with m.patch.object(serve, "_DEMO_CASES_DIR", root):
            assert serve.list_cases()[0]["label"] == "PanTS 00000001"


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
