#!/usr/bin/env python3
"""Evaluate a trained checkpoint honestly, separating the two questions and showing
the effect of CADe post-processing:

  - Lesion (and pancreas) Dice on TUMOR-POSITIVE cases  ("when there is a tumor, how well
    do we outline it?"), reported RAW and CLEANED (largest-component + volume threshold).
  - Specificity on TUMOR-FREE cases ("how often do we correctly NOT flag a tumor?"),
    RAW and CLEANED.

Full-volume sliding-window inference. No retraining.

Usage:
  python scripts/evaluate.py --ckpt outputs/checkpoints/pants-level45/last.pt
  python scripts/evaluate.py --ckpt .../last.pt --n-pos 15 --n-neg 15 --min-lesion-mm3 100
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.dataset import get_dataset
from src.models.segresnet import build_model
from src.training import trainer as T
from src.inference.sliding_window import predict_volume, predict_probs_tta
from src.inference.postprocess import postprocess

from monai.data import DataLoader


def dice(pred: np.ndarray, gt: np.ndarray) -> float:
    """Dice of prediction vs ground truth. Returns NaN when the GROUND TRUTH is empty
    (the class is undefined for this case) so it is excluded via nanmean — never silently
    awarded 1.0, which would inflate a positive-cohort mean if a tiny lesion vanished in
    preprocessing (metrics audit, 2026-07-17)."""
    pred, gt = np.asarray(pred).astype(bool), np.asarray(gt).astype(bool)
    g = int(gt.sum())
    if g == 0:
        return float("nan")
    return 2.0 * int((pred & gt).sum()) / (int(pred.sum()) + g)


def softmax_np(logits) -> np.ndarray:
    """logits: torch tensor (1, C, H, W, D) -> numpy softmax probs (C, H, W, D)."""
    p = torch.softmax(logits, dim=1)[0].cpu().numpy()
    return p


def label_from_probs(probs: np.ndarray, lesion_thresh: float) -> np.ndarray:
    """Build a 3-class map: a voxel is lesion (2) when its lesion probability clears
    the threshold; otherwise it is pancreas (1) or background (0) by which is larger.
    Raising the threshold trades sensitivity for specificity."""
    lesion = probs[2] >= lesion_thresh
    out = np.where(probs[1] >= probs[0], 1, 0).astype(np.int16)
    out[lesion] = 2
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--n-pos", type=int, default=12)
    ap.add_argument("--n-neg", type=int, default=12)
    ap.add_argument("--min-lesion-mm3", type=float, default=None)
    ap.add_argument("--sweep", action="store_true",
                    help="sweep the lesion probability threshold and print a sens/spec table")
    ap.add_argument("--thresholds", default="0.3,0.4,0.5,0.6,0.7,0.8,0.9",
                    help="comma-separated lesion probability thresholds for --sweep")
    ap.add_argument("--lesion-within-pancreas-mm", type=float, default=None,
                    help="if set, cleaned metrics also demote lesion components >this many mm from the pancreas")
    ap.add_argument("--roi", type=int, default=None,
                    help="sliding-window size; MUST match the patch the model was trained at (e.g. 128)")
    ap.add_argument("--spacing", type=float, default=None,
                    help="override target spacing in mm; MUST match what the model was trained at")
    ap.add_argument("--crop-pancreas", type=float, default=None,
                    help="oracle ROI: crop to ground-truth pancreas + margin mm; MUST match training")
    ap.add_argument("--crop-native", type=int, default=None,
                    help="crop pancreas in native space + native-voxel margin; MUST match training")
    ap.add_argument("--whole-box", action="store_true",
                    help="EXP-12: feed the whole pancreas box as one --roi cube; MUST match training")
    ap.add_argument("--tta", action="store_true",
                    help="test-time augmentation: average predictions over flips (no retrain); 8 views")
    ap.add_argument("--roi-source", choices=["union", "pancreas"], default=None,
                    help="ROI crop source; MUST match training (union=legacy, pancreas=organ only)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.roi:
        cfg["sampling"]["patch_size"] = [args.roi, args.roi, args.roi]
        cfg["inference"]["sw_roi_size"] = [args.roi, args.roi, args.roi]
        print(f"[override] patch/roi -> {args.roi}^3")
    if args.spacing:
        cfg["preprocessing"]["target_spacing"] = [args.spacing, args.spacing, args.spacing]
        print(f"[override] target_spacing -> {args.spacing}mm")
    if args.crop_pancreas is not None:
        cfg["preprocessing"]["crop_to_pancreas_margin_mm"] = args.crop_pancreas
        print(f"[override] crop to pancreas ROI + {args.crop_pancreas}mm margin")
    if args.crop_native is not None:
        cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
        print(f"[override] crop to pancreas in NATIVE space + {args.crop_native}-voxel margin")
    if args.whole_box:
        cfg["preprocessing"]["whole_box"] = True
        print(f"[override] WHOLE-BOX: feeding the entire pancreas box as one cube")
    if args.roi_source:
        cfg["preprocessing"]["roi_source"] = args.roi_source
        print(f"[override] ROI source = {args.roi_source}")
    set_seed(get(cfg, "seed", 42))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)
    spacing = tuple(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5]))
    vox_mm3 = float(np.prod(spacing))
    min_mm3 = (args.min_lesion_mm3 if args.min_lesion_mm3 is not None
               else float(get(cfg, "inference.postprocess.lesion_min_volume_mm3", 50)))

    model = build_model(cfg).to(device)
    step, _ = T.load_checkpoint(args.ckpt, model, map_location=device)
    model.eval()
    use_tta = args.tta or bool(get(cfg, "inference.tta", False))
    print(f"loaded {args.ckpt} (step {step}) on {device}   min-lesion={min_mm3:.0f} mm3"
          f"{'   [TTA: 8-view flips]' if use_tta else ''}\n")

    def infer_probs(image):
        """Softmax probabilities (C,H,W,D) for one volume, with or without flip TTA."""
        if use_tta:
            return predict_probs_tta(model, image, cfg, device)
        with torch.no_grad():
            return softmax_np(predict_volume(model, image, cfg, device))

    man = pd.read_csv(dp["manifest"])
    vset = {x.strip() for x in (dp["splits_dir"] / f"{args.split}.txt").read_text().split() if x.strip()}
    vdf = man[man["case_id"].isin(vset)]
    pos = vdf[vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_pos]
    neg = vdf[~vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_neg]
    print(f"scoring {len(pos)} tumor-positive + {len(neg)} tumor-free {args.split} cases "
          f"(sliding-window, takes a bit)...")

    thresholds = [float(x) for x in args.thresholds.split(",") if x.strip()] if args.sweep else []
    within = args.lesion_within_pancreas_mm
    # per-threshold accumulators: lesion Dice on positives, correct-not-flagged count on negatives
    sweep_pos = {t: [] for t in thresholds}
    sweep_neg = {t: 0 for t in thresholds}

    # --- tumor-positive: pancreas + lesion Dice, raw vs cleaned ---
    p_d, l_raw, l_pp = [], [], []
    for b in DataLoader(get_dataset(cfg, args.split, train=False, cache=False, ids=pos),
                        batch_size=1, num_workers=0):
        probs = infer_probs(b["image"].to(device))       # (C,H,W,D), computed once (TTA-aware)
        pred = probs.argmax(0)
        gt = b["label"][0, 0].cpu().numpy()
        p_d.append(dice(pred == 1, gt == 1))
        l_raw.append(dice(pred == 2, gt == 2))
        l_pp.append(dice(postprocess(pred, spacing, lesion_min_mm3=min_mm3,
                                     lesion_within_pancreas_mm=within) == 2, gt == 2))
        for t in thresholds:
            sweep_pos[t].append(dice(label_from_probs(probs, t) == 2, gt == 2))
    n_excl = int(np.isnan(l_raw).sum())
    print(f"\n[TUMOR-POSITIVE cases, n={len(pos)}]"
          + (f"  ({n_excl} excluded: lesion empty after preprocessing)" if n_excl else ""))
    print(f"  pancreas Dice         : {np.nanmean(p_d):.3f}")
    print(f"  lesion Dice (raw)     : {np.nanmean(l_raw):.3f}")
    print(f"  lesion Dice (cleaned) : {np.nanmean(l_pp):.3f}")

    # --- tumor-free: specificity, raw vs cleaned ---
    n = len(neg)
    if neg:
        clean_raw = clean_pp = 0
        for b in DataLoader(get_dataset(cfg, args.split, train=False, cache=False, ids=neg),
                            batch_size=1, num_workers=0):
            probs = infer_probs(b["image"].to(device))
            pred = probs.argmax(0)
            if int((pred == 2).sum()) * vox_mm3 < min_mm3:
                clean_raw += 1
            if int((postprocess(pred, spacing, lesion_min_mm3=min_mm3,
                                lesion_within_pancreas_mm=within) == 2).sum()) * vox_mm3 < min_mm3:
                clean_pp += 1
            for t in thresholds:
                if int((label_from_probs(probs, t) == 2).sum()) * vox_mm3 < min_mm3:
                    sweep_neg[t] += 1
        print(f"\n[MASK-NEGATIVE cases, n={n}]  (specificity@{min_mm3:.0f}mm3 = predicted lesion below threshold)")
        print(f"  specificity (raw)     : {clean_raw}/{n} = {100*clean_raw/n:.0f}%")
        print(f"  specificity (cleaned) : {clean_pp}/{n} = {100*clean_pp/n:.0f}%")

    # --- lesion probability-threshold sweep (the sens/spec tradeoff curve) ---
    if thresholds:
        print(f"\n[LESION THRESHOLD SWEEP]  higher threshold = fewer lesion calls = higher specificity")
        print(f"  {'thresh':>7} | {'lesion Dice (pos)':>18} | {'specificity (neg)':>18}")
        print("  " + "-" * 52)
        for t in thresholds:
            ld = np.nanmean(sweep_pos[t]) if sweep_pos[t] else float("nan")
            sp = f"{sweep_neg[t]}/{n} = {100*sweep_neg[t]/n:.0f}%" if n else "n/a"
            print(f"  {t:>7.2f} | {ld:>18.3f} | {sp:>18}")

    cleaned_note = "largest component + volume threshold"
    if within is not None:
        cleaned_note += f" + lesion-within-{within:.0f}mm-of-pancreas"
    print(f"\nDone. 'cleaned' = after CADe post-processing ({cleaned_note}).")


if __name__ == "__main__":
    main()
