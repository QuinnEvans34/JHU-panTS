"""Minimal FastAPI inference endpoint for the pancreas-lesion CADe model (M4A1 §4).

Local-demo, PROVIDED-ROI serving: POST a known `case_id` from `ui/public/cases/` and get back a CADe
summary (possible-lesion flag, volume, confidence, cleaned Dice). The whole-box model builds its ROI
from that case's local `gt.nii.gz` mask and scores its local `ct.nii.gz`; the external PanTS drive is
not needed at demo time. This is not raw-CT autonomous deployment — uploaded CT serving would require
the localize-then-segment cascade (future work).

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

import json
import re
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from monai.data import list_data_collate
from monai.transforms import (
    Compose,
    CropForegroundd,
    EnsureChannelFirstd,
    EnsureTyped,
    LoadImaged,
    MapTransform,
    Orientationd,
    ResizeWithPadOrCropd,
    Spacingd,
    SpatialPadd,
)
from pydantic import BaseModel

from src.utils.config import load_config, get
from src.data.transforms import PadEmptyCropd
from src.training import trainer as T
from src.models.segresnet import build_model, sha256_file
from src.inference.collapse import collapse_probs_np, is_anatomy5
from src.inference.postprocess import postprocess
from src.inference.predict import dice_np, softmax_np, verify_checkpoint_recipe
from src.inference.sliding_window import predict_volume

STATE: dict = {}   # populated once at startup
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEMO_CASES_DIR = _REPO_ROOT / "ui" / "public" / "cases"
_CASE_ID_PATTERN = re.compile(r"^PanTS_\d{8}$")


def _label_foreground(label):
    return label > 0


class _ValidateDemoVolumesd(MapTransform):
    """Reject malformed local inputs before cropping; error text never reaches the response."""

    def __init__(self):
        super().__init__(keys=["image", "label"])

    def __call__(self, data):
        d = dict(data)
        image, label = d["image"], d["label"]
        if tuple(image.shape[-3:]) != tuple(label.shape[-3:]):
            raise ValueError("local CT and mask shapes differ")
        if not bool(torch.isfinite(image).all()) or not bool(torch.isfinite(label).all()):
            raise ValueError("local CT or mask contains non-finite values")
        rounded = label.round()
        if not bool(torch.allclose(label.float(), rounded.float())):
            raise ValueError("local mask must contain integer labels")
        values = {int(value) for value in torch.unique(rounded).tolist()}
        if not values.issubset({0, 1, 2}) or not bool((rounded > 0).any()):
            raise ValueError("local mask must contain a 3-class pancreas foreground")
        d["label"] = rounded
        return d


class _NormalizeDemoCTd(MapTransform):
    """Preserve exported [0,1] CTs; HU-window raw CTs if a future local case is unscaled."""

    def __init__(self, hu_lo: float, hu_hi: float):
        super().__init__(keys=["image"])
        self.hu_lo = float(hu_lo)
        self.hu_hi = float(hu_hi)

    def __call__(self, data):
        d = dict(data)
        image = d["image"].float()
        lo, hi = float(image.min()), float(image.max())
        if lo >= -1e-4 and hi <= 1.0001:
            d["image"] = image.clamp(0.0, 1.0)
        else:
            d["image"] = ((image.clamp(self.hu_lo, self.hu_hi) - self.hu_lo)
                          / (self.hu_hi - self.hu_lo))
        return d


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


def _safe_friendly_label(case_id: str, metadata) -> str:
    if isinstance(metadata, dict):
        for key in ("label", "display_name", "name", "title"):
            value = metadata.get(key)
            if isinstance(value, str):
                value = " ".join(value.split()).strip()
                if value and len(value) <= 80 and "/" not in value and "\\" not in value:
                    return value
    return case_id.replace("_", " ")


def _discover_demo_cases() -> list[dict]:
    """List complete local cases and optional display labels without returning paths."""
    if not _DEMO_CASES_DIR.is_dir():
        raise OSError("demo case directory unavailable")

    results = {}
    results_path = _DEMO_CASES_DIR / "results.json"
    if results_path.exists():
        results = json.loads(results_path.read_text(encoding="utf-8"))
        if not isinstance(results, dict):
            raise ValueError("results metadata must be an object")

    cases = []
    for case_dir in _DEMO_CASES_DIR.iterdir():
        case_id = case_dir.name
        if (not case_dir.is_dir() or case_dir.is_symlink()
                or not _CASE_ID_PATTERN.fullmatch(case_id)):
            continue
        ct_path, gt_path = case_dir / "ct.nii.gz", case_dir / "gt.nii.gz"
        if (not ct_path.is_file() or not gt_path.is_file()
                or ct_path.is_symlink() or gt_path.is_symlink()):
            continue
        cases.append({
            "case_id": case_id,
            "split": "test",
            "label": _safe_friendly_label(case_id, results.get(case_id)),
        })
    return sorted(cases, key=lambda item: item["case_id"])


def _demo_case_files(case_id: str) -> tuple[Path, Path]:
    if not _CASE_ID_PATTERN.fullmatch(case_id):
        raise KeyError("unknown local demo case")
    case_dir = _DEMO_CASES_DIR / case_id
    ct_path, gt_path = case_dir / "ct.nii.gz", case_dir / "gt.nii.gz"
    if (not case_dir.is_dir() or case_dir.is_symlink()
            or not ct_path.is_file() or not gt_path.is_file()
            or ct_path.is_symlink() or gt_path.is_symlink()):
        raise KeyError("unknown local demo case")
    return ct_path, gt_path


def _build_demo_transform(cfg: dict) -> Compose:
    """Match the final whole-box preprocessing using a local combined 3-class mask."""
    pre = cfg["preprocessing"]
    patch = tuple(cfg["sampling"]["patch_size"])
    spacing = tuple(pre["target_spacing"])
    margin = int(pre.get("crop_native_margin_vox", 16))
    hu_lo, hu_hi = pre["hu_window"]
    if not bool(pre.get("whole_box", False)):
        raise ValueError("local demo serving requires the whole-box recipe")

    keys = ["image", "label"]
    # IMPORTANT: the local demo cases are ALREADY the final whole-box model input. Each
    # ct.nii.gz / gt.nii.gz was written by scripts/export_case.py with the exact training
    # recipe (crop to the pancreas box in native space + 16-vox margin -> resample to 1.5mm ->
    # ResizeWithPadOrCrop to 128^3 -> HU->[0,1]). They are already 128^3 @1.5mm in [0,1].
    # We must therefore NOT re-crop or re-resample here: doing so would crop a second time out
    # of the already-cropped cube and rescale the organ, so the model would see a different
    # field-of-view than it was trained on (a train/serve mismatch). Feed the cube straight
    # through, with an idempotent intensity normalize and a size guard that is a no-op at 128^3.
    return Compose([
        LoadImaged(keys=keys),
        EnsureChannelFirstd(keys=keys),
        Orientationd(keys=keys, axcodes=pre.get("orientation", "RAS")),
        _ValidateDemoVolumesd(),
        _NormalizeDemoCTd(hu_lo, hu_hi),
        ResizeWithPadOrCropd(keys=keys, spatial_size=patch),
        EnsureTyped(keys=keys),
    ])


def predict_demo_case(cfg: dict, model, device, case_id: str, transform: Compose,
                      min_lesion_mm3=None, return_mask: bool = False) -> dict:
    """Score one local prepared CT using a pancreas box derived from its local GT mask."""
    ct_path, gt_path = _demo_case_files(case_id)
    sample = transform({"image": str(ct_path), "label": str(gt_path)})
    batch = list_data_collate([sample])

    spacing = tuple(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5]))
    vox_mm3 = float(np.prod(spacing))
    min_mm3 = float(min_lesion_mm3 if min_lesion_mm3 is not None
                    else get(cfg, "inference.postprocess.lesion_min_volume_mm3", 50))

    model.eval()
    with torch.no_grad():
        logits = predict_volume(model, batch["image"].to(device), cfg, device)
    probs = softmax_np(logits)
    if is_anatomy5(cfg):
        probs = collapse_probs_np(probs)
    pred = postprocess(probs.argmax(0), spacing, lesion_min_mm3=min_mm3)
    gt = batch["label"][0, 0].cpu().numpy()

    les_vox = int((pred == 2).sum())
    les_mm3 = les_vox * vox_mm3
    pancreas_dice = dice_np(pred == 1, gt == 1)
    lesion_dice = dice_np(pred == 2, gt == 2)

    def json_float(value):
        return None if value != value else float(value)

    result = {
        "case_id": str(case_id),
        "lesion_flagged": bool(les_mm3 >= min_mm3),
        "lesion_volume_mm3": float(les_mm3),
        "global_peak_lesion_confidence": float(probs[2].max()),
        "retained_peak_lesion_confidence": float(probs[2][pred == 2].max()) if les_vox > 0 else 0.0,
        "pancreas_dice_cleaned": json_float(pancreas_dice),
        "lesion_dice_cleaned": json_float(lesion_dice),
        "min_lesion_mm3": min_mm3,
        "note": "CADe assist — flags a POSSIBLE lesion for radiologist review; not a diagnosis. "
                "Provided-ROI (local demo) inference.",
    }
    if return_mask:
        result["_mask"] = pred
    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    ckpt = os.environ.get("MODEL_CKPT")
    if not ckpt or not Path(ckpt).exists():
        raise RuntimeError("set MODEL_CKPT to an existing checkpoint before starting the server")
    cfg = _apply_recipe(load_config(os.environ.get("MODEL_CONFIG", "configs/level45.yaml")))
    device = T.get_device(cfg)
    demo_transform = _build_demo_transform(cfg)
    try:
        data_root_ok = bool(_discover_demo_cases())
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        data_root_ok = False

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
                 data_root_ok=bool(data_root_ok), demo_transform=demo_transform)
    print(f"[serve] loaded step={blob.get('step')} sha={STATE['ckpt_sha'][:12]} "
          f"label_mode={cfg['label_mode']} device={device} data_root_ok={data_root_ok}")
    yield
    STATE.clear()


app = FastAPI(title="Pancreas-lesion CADe (provided-ROI)", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class PredictRequest(BaseModel):
    case_id: str
    split: str = "test"


@app.get("/cases")
def list_cases():
    """Return complete local demo cases without exposing their filesystem locations."""
    try:
        cases = _discover_demo_cases()
    except (OSError, UnicodeError):
        raise HTTPException(status_code=503, detail="case catalog unavailable")
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=500, detail="case catalog invalid")

    if not cases:
        raise HTTPException(status_code=503, detail="case catalog unavailable")
    return cases


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
        raise HTTPException(status_code=503, detail="local demo cases unavailable")
    if req.split not in ("test", "val"):
        raise HTTPException(status_code=422, detail="split must be 'test' or 'val'")
    t0 = time.time()
    try:
        with STATE["lock"]:      # serialize inference — one global model, MPS not concurrency-safe
            res = predict_demo_case(
                STATE["cfg"],
                STATE["model"],
                STATE["device"],
                req.case_id,
                STATE["demo_transform"],
            )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown case_id in split '{req.split}'")
    except Exception:
        raise HTTPException(status_code=500, detail="inference recipe error")   # no internal detail leaked
    res.pop("_mask", None)
    res["inference_seconds"] = round(time.time() - t0, 2)
    res["checkpoint_step"] = STATE.get("ckpt_step")
    return res
