"""Minimal FastAPI inference endpoint for the pancreas-lesion CADe model (M4A1 §4).

Dataset-backed, PROVIDED-ROI serving: POST a known `case_id` (from the manifest) and get back a CADe
summary (possible-lesion flag, volume, confidence, cleaned Dice). This is NOT raw-CT autonomous
deployment — the whole-box model builds its ROI from the case's ground-truth pancreas mask; serving an
uploaded raw CT would require the localize-then-segment cascade (future work).

Design (per Codex review): model loaded exactly ONCE via a lifespan hook; a process-level lock
serializes MPS inference; recipe is verified against the checkpoint metadata at startup; the endpoint
never leaks filesystem paths or tracebacks; config comes from ENV so `uvicorn scripts.serve:app` works.

Run (use --workers 1 — multiple workers create independent models + locks, defeating the single-model
serialization and multiplying GPU memory):
  MODEL_CKPT=outputs/checkpoints/pants-level45/<...>/best.pt uvicorn scripts.serve:app --port 8000 --workers 1
Optional ENV: MODEL_CONFIG, MODEL_LABEL_MODE, MODEL_WHOLE_BOX, MODEL_ROI, MODEL_SPACING,
              MODEL_CROP_NATIVE, MODEL_ROI_SOURCE
"""
import os
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.utils.config import load_config, get
from src.utils import paths as P
from src.training import trainer as T
from src.models.segresnet import build_model, sha256_file
from src.inference.predict import predict_case, verify_checkpoint_recipe

STATE: dict = {}   # populated once at startup


def _apply_recipe(cfg: dict) -> dict:
    """Set the final-model whole-box recipe on cfg (ENV-overridable). Must match the checkpoint —
    verified against the embedded metadata at startup."""
    roi = int(os.environ.get("MODEL_ROI", "128"))
    cfg["preprocessing"]["whole_box"] = os.environ.get("MODEL_WHOLE_BOX", "1") == "1"
    cfg["preprocessing"]["crop_native_margin_vox"] = int(os.environ.get("MODEL_CROP_NATIVE", "16"))
    cfg["preprocessing"]["target_spacing"] = [float(os.environ.get("MODEL_SPACING", "1.5"))] * 3
    cfg["preprocessing"]["roi_source"] = os.environ.get("MODEL_ROI_SOURCE", "pancreas")
    cfg["sampling"]["patch_size"] = [roi] * 3
    cfg["inference"]["sw_roi_size"] = [roi] * 3
    lm = os.environ.get("MODEL_LABEL_MODE", "pancreas_lesion")
    cfg["label_mode"] = lm
    cfg["model"]["out_channels"] = 5 if lm == "anatomy5" else 3
    return cfg


@asynccontextmanager
async def lifespan(app: FastAPI):
    ckpt = os.environ.get("MODEL_CKPT")
    if not ckpt or not Path(ckpt).exists():
        raise RuntimeError("set MODEL_CKPT to an existing checkpoint before starting the server")
    cfg = _apply_recipe(load_config(os.environ.get("MODEL_CONFIG", "configs/level45.yaml")))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)
    data_root_ok = Path(str(get(cfg, "paths.pants_root", ""))).exists() and Path(dp["manifest"]).exists()

    blob = torch.load(ckpt, map_location="cpu", weights_only=False)
    meta = blob.get("extra", {}) if isinstance(blob, dict) else {}
    verify_checkpoint_recipe(meta, cfg, require_meta=False)   # abort on mismatch when meta is present

    model = build_model(cfg)
    T.load_checkpoint(ckpt, model, map_location=device)
    model.to(device).eval()

    STATE.update(model=model, cfg=cfg, device=device, lock=threading.Lock(),
                 ckpt_step=blob.get("step"), ckpt_sha=sha256_file(ckpt),
                 label_mode=cfg["label_mode"], roi=cfg["inference"]["sw_roi_size"],
                 spacing=cfg["preprocessing"]["target_spacing"], roi_source=cfg["preprocessing"]["roi_source"],
                 data_root_ok=bool(data_root_ok))
    print(f"[serve] loaded step={blob.get('step')} sha={STATE['ckpt_sha'][:12]} "
          f"label_mode={cfg['label_mode']} device={device} data_root_ok={data_root_ok}")
    yield
    STATE.clear()


app = FastAPI(title="Pancreas-lesion CADe (provided-ROI)", version="1.0", lifespan=lifespan)


class PredictRequest(BaseModel):
    case_id: str
    split: str = "test"


@app.get("/health")
def health():
    return {
        "status": "ok" if STATE else "starting",
        "model": "pancreas-lesion-segmenter",
        "checkpoint_step": STATE.get("ckpt_step"),
        "checkpoint_sha256": (STATE.get("ckpt_sha") or "")[:16],
        "label_mode": STATE.get("label_mode"),
        "roi": STATE.get("roi"),
        "spacing": STATE.get("spacing"),
        "roi_source": STATE.get("roi_source"),
        "device": str(STATE.get("device")),
        "data_root_available": STATE.get("data_root_ok"),
        "note": "CADe assist — flags a possible lesion for radiologist review; not a diagnosis.",
    }


@app.post("/predict")
def predict(req: PredictRequest):
    if not STATE:
        raise HTTPException(status_code=503, detail="model not loaded")
    if not STATE["data_root_ok"]:
        raise HTTPException(status_code=503, detail="data root unavailable (drive/manifest missing)")
    if req.split not in ("test", "val"):
        raise HTTPException(status_code=422, detail="split must be 'test' or 'val'")
    t0 = time.time()
    try:
        with STATE["lock"]:      # serialize inference — one global model, MPS not concurrency-safe
            res = predict_case(STATE["cfg"], STATE["model"], STATE["device"], req.case_id, split=req.split)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown case_id in split '{req.split}'")
    except ValueError:
        raise HTTPException(status_code=500, detail="inference recipe error")   # no internal detail leaked
    res.pop("_mask", None)
    res["inference_seconds"] = round(time.time() - t0, 2)
    res["checkpoint_step"] = STATE.get("ckpt_step")
    return res
