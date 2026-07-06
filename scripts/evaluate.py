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
from src.inference.sliding_window import predict_volume
from src.inference.postprocess import postprocess

from monai.data import DataLoader


def dice(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a.astype(bool), b.astype(bool)
    s = int(a.sum() + b.sum())
    return 1.0 if s == 0 else 2.0 * int((a & b).sum()) / s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--n-pos", type=int, default=12)
    ap.add_argument("--n-neg", type=int, default=12)
    ap.add_argument("--min-lesion-mm3", type=float, default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
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
    print(f"loaded {args.ckpt} (step {step}) on {device}   min-lesion={min_mm3:.0f} mm3\n")

    man = pd.read_csv(dp["manifest"])
    vset = {x.strip() for x in (dp["splits_dir"] / f"{args.split}.txt").read_text().split() if x.strip()}
    vdf = man[man["case_id"].isin(vset)]
    pos = vdf[vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_pos]
    neg = vdf[~vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_neg]
    print(f"scoring {len(pos)} tumor-positive + {len(neg)} tumor-free {args.split} cases "
          f"(sliding-window, takes a bit)...")

    # --- tumor-positive: pancreas + lesion Dice, raw vs cleaned ---
    p_d, l_raw, l_pp = [], [], []
    for b in DataLoader(get_dataset(cfg, args.split, train=False, cache=False, ids=pos),
                        batch_size=1, num_workers=0):
        with torch.no_grad():
            logits = predict_volume(model, b["image"].to(device), cfg, device)
        pred = logits.argmax(1)[0].cpu().numpy()
        gt = b["label"][0, 0].cpu().numpy()
        p_d.append(dice(pred == 1, gt == 1))
        l_raw.append(dice(pred == 2, gt == 2))
        l_pp.append(dice(postprocess(pred, spacing, lesion_min_mm3=min_mm3) == 2, gt == 2))
    print(f"\n[TUMOR-POSITIVE cases, n={len(pos)}]")
    print(f"  pancreas Dice         : {np.mean(p_d):.3f}")
    print(f"  lesion Dice (raw)     : {np.mean(l_raw):.3f}")
    print(f"  lesion Dice (cleaned) : {np.mean(l_pp):.3f}")

    # --- tumor-free: specificity, raw vs cleaned ---
    if neg:
        clean_raw = clean_pp = 0
        for b in DataLoader(get_dataset(cfg, args.split, train=False, cache=False, ids=neg),
                            batch_size=1, num_workers=0):
            with torch.no_grad():
                logits = predict_volume(model, b["image"].to(device), cfg, device)
            pred = logits.argmax(1)[0].cpu().numpy()
            if int((pred == 2).sum()) * vox_mm3 < min_mm3:
                clean_raw += 1
            if int((postprocess(pred, spacing, lesion_min_mm3=min_mm3) == 2).sum()) * vox_mm3 < min_mm3:
                clean_pp += 1
        n = len(neg)
        print(f"\n[TUMOR-FREE cases, n={n}]  (specificity = correctly NOT flagged)")
        print(f"  specificity (raw)     : {clean_raw}/{n} = {100*clean_raw/n:.0f}%")
        print(f"  specificity (cleaned) : {clean_pp}/{n} = {100*clean_pp/n:.0f}%")

    print("\nDone. 'cleaned' = after CADe post-processing (largest component + volume threshold).")


if __name__ == "__main__":
    main()
