"""FastAPI endpoint behavior tests (M4A1 §4). Run on the Mac (needs fastapi + torch):
    python tests/test_serve.py

Tests the route functions directly (populating serve.STATE) to avoid the lifespan model load:
404 unknown case, 422 invalid split, 503 not-loaded / data-missing, and /health fields.
"""
import sys
import threading
import unittest.mock as m
from pathlib import Path

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
                roi=[128, 128, 128], spacing=[1.5, 1.5, 1.5], roi_source="pancreas", data_root_ok=True)


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
    with m.patch.object(serve, "predict_case", side_effect=KeyError("nope")):
        assert _status(serve.predict, serve.PredictRequest(case_id="X", split="test")) == 404
    serve.STATE.clear()


def test_predict_ok_adds_latency():
    serve.STATE.clear(); serve.STATE.update(_ok_state())
    with m.patch.object(serve, "predict_case", return_value={"case_id": "X", "lesion_flagged": False, "_mask": 1}):
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
