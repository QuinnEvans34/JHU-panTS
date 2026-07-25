"""Single-entry inference + CADe summary for ONE case — shared by serving and analysis.

Centralizes the load → preprocess → sliding-window → post-process → summary logic (previously
duplicated across evaluate.py / export_case.py), plus recipe verification against the checkpoint
metadata, so serving and evaluation can't silently diverge.

IMPORTANT (provided-ROI, not autonomous): the whole-box model's input ROI is built from the case's
GROUND-TRUTH pancreas/subregion mask. So `predict_case` requires the case to have BOTH a CT and its
ROI label available — this is dataset-backed, provided-ROI inference, NOT raw-CT deployment (that
would need the localize-then-segment cascade). Whether we also compute Dice is a separate matter.

Clinical framing: this is a CADe (computer-aided *detection*) assist — it flags a POSSIBLE lesion for
a radiologist to review; it makes no diagnostic claim.
"""
from __future__ import annotations

import os
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np
import torch
from monai.data import list_data_collate

from src.utils.config import get
from src.utils import paths as P
from src.data.dataset import get_dataset, load_split_ids
from src.inference.sliding_window import predict_volume
from src.inference.postprocess import postprocess
from src.inference.collapse import is_anatomy5, collapse_probs_np, collapse_label_np


def softmax_np(logits) -> np.ndarray:
    """logits (1,C,*) torch -> (C,*) numpy softmax probabilities."""
    return torch.softmax(logits, dim=1)[0].cpu().numpy()


def dice_np(pred_bool, gt_bool) -> float:
    """Dice; NaN when the ground truth is empty (class undefined for this case)."""
    pred = np.asarray(pred_bool, dtype=bool)
    gt = np.asarray(gt_bool, dtype=bool)
    g = int(gt.sum())
    if g == 0:
        return float("nan")
    return 2.0 * int((pred & gt).sum()) / (int(pred.sum()) + g)


def verify_checkpoint_recipe(meta: dict, cfg: dict, require_meta: bool = True) -> None:
    """Raise ValueError if the serve/eval recipe disagrees with the checkpoint's embedded metadata —
    the same guarantee evaluate.py enforces. Serving must never silently run a mismatched recipe."""
    if not meta:
        if require_meta:
            raise ValueError("checkpoint has no embedded recipe metadata; cannot verify recipe")
        return
    want = {
        "label_mode": cfg.get("label_mode", "pancreas_lesion"),
        "out_channels": int(get(cfg, "model.out_channels", 3)),
        "target_spacing": list(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5])),
        "sw_roi_size": list(get(cfg, "inference.sw_roi_size", [96, 96, 96])),
        "whole_box": bool(get(cfg, "preprocessing.whole_box", False)),
        "roi_source": get(cfg, "preprocessing.roi_source", "union"),
        "crop_native_margin_vox": get(cfg, "preprocessing.crop_native_margin_vox"),
        "crop_to_pancreas_margin_mm": get(cfg, "preprocessing.crop_to_pancreas_margin_mm"),
    }
    # Only verify keys that are ACTUALLY PRESENT in the metadata. An absent key means the checkpoint
    # simply didn't record that field (older/sparse metadata) — treat it as unverified, NOT as a
    # None-vs-value mismatch. This lets a sparse-but-consistent checkpoint pass while still catching a
    # PRESENT key that disagrees.
    mism = {k: (meta.get(k), v) for k, v in want.items() if k in meta and str(meta.get(k)) != str(v)}
    if mism:
        raise ValueError("recipe mismatch vs checkpoint: "
                         + "; ".join(f"{k}: ckpt={a!r} cfg={b!r}" for k, (a, b) in mism.items()))


def load_single_case(cfg: dict, split: str, case_id: str):
    """Return a batched dict for ONE case, after asserting the id belongs to the split.
    Raises KeyError if the id is not in the split (build_records silently drops unknown ids, so we
    validate against the split file first) or if the loaded sample identity doesn't match."""
    dp = P.data_paths(cfg)
    split_ids = set(load_split_ids(dp["splits_dir"], split))
    if case_id not in split_ids:
        raise KeyError(f"case_id not in split '{split}'")
    ds = get_dataset(cfg, split, train=False, cache="none", ids=[case_id])
    sample = ds[0]
    got = sample.get("case_id")
    got = got[0] if isinstance(got, (list, tuple)) else got
    if str(got) != str(case_id):
        raise KeyError(f"loaded case identity '{got}' != requested '{case_id}'")
    return list_data_collate([sample])


def predict_case(cfg: dict, model, device, case_id: str, split: str = "test",
                 min_lesion_mm3=None, return_mask: bool = False) -> dict:
    """Run the final model on one case and return a JSON-safe CADe summary (Dice is post-processed,
    i.e. 'cleaned'). Requires the case to have CT + ROI labels (provided-ROI whole-box model)."""
    anat = is_anatomy5(cfg)
    spacing = tuple(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5]))
    vox_mm3 = float(np.prod(spacing))
    min_mm3 = float(min_lesion_mm3 if min_lesion_mm3 is not None
                    else get(cfg, "inference.postprocess.lesion_min_volume_mm3", 50))

    batch = load_single_case(cfg, split, case_id)
    model.eval()
    with torch.no_grad():
        logits = predict_volume(model, batch["image"].to(device), cfg, device)
    probs = softmax_np(logits)
    if anat:
        probs = collapse_probs_np(probs)
    pred = postprocess(probs.argmax(0), spacing, lesion_min_mm3=min_mm3)   # cleaned label map
    gt = batch["label"][0, 0].cpu().numpy()
    if anat:
        gt = collapse_label_np(gt, "anatomy5")

    les_vox = int((pred == 2).sum())
    les_mm3 = les_vox * vox_mm3
    pd_c, ld_c = dice_np(pred == 1, gt == 1), dice_np(pred == 2, gt == 2)

    def _f(x):   # NaN -> None (JSON-safe)
        return None if (x != x) else float(x)

    out = {
        "case_id": str(case_id),
        "lesion_flagged": bool(les_mm3 >= min_mm3),   # "possible lesion" CADe flag — NOT a diagnosis
        "lesion_volume_mm3": float(les_mm3),
        "global_peak_lesion_confidence": float(probs[2].max()),                        # over the whole ROI
        "retained_peak_lesion_confidence": float(probs[2][pred == 2].max()) if les_vox > 0 else 0.0,
        "pancreas_dice_cleaned": _f(pd_c),
        "lesion_dice_cleaned": _f(ld_c),
        "min_lesion_mm3": min_mm3,
        "note": "CADe assist — flags a POSSIBLE lesion for radiologist review; not a diagnosis. "
                "Provided-ROI (dataset-backed) inference.",
    }
    if return_mask:
        out["_mask"] = pred   # internal only — never serialize into an API response
    return out
