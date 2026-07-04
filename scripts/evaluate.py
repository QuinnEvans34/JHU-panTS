#!/usr/bin/env python3
"""Evaluate a trained checkpoint the RIGHT way, separating the two questions:

  - Lesion (and pancreas) Dice measured ONLY on tumor-positive cases
    ("when there is a tumor, how well do we outline it?")
  - Specificity on tumor-free cases
    ("how often do we correctly NOT flag a tumor?")

Full-volume sliding-window inference. No retraining — loads an existing checkpoint.

Usage:
  python scripts/evaluate.py --ckpt outputs/checkpoints/pants-level45/last.pt
  python scripts/evaluate.py --ckpt .../last.pt --n-pos 15 --n-neg 15
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
from src.training.metrics import DiceEvaluator
from src.training import trainer as T
from src.inference.sliding_window import predict_volume

from monai.data import DataLoader


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--n-pos", type=int, default=12, help="# tumor-positive cases to score")
    ap.add_argument("--n-neg", type=int, default=12, help="# tumor-free cases to score")
    ap.add_argument("--min-lesion-mm3", type=float, default=50.0,
                    help="predicted lesion below this volume counts as 'not flagged'")
    args = ap.parse_args()

    cfg = load_config(args.config)
    set_seed(get(cfg, "seed", 42))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)

    model = build_model(cfg).to(device)
    step, _ = T.load_checkpoint(args.ckpt, model, map_location=device)
    model.eval()
    print(f"loaded {args.ckpt} (step {step}) on {device}\n")

    man = pd.read_csv(dp["manifest"])
    val_ids = {x.strip() for x in (dp["splits_dir"] / f"{args.split}.txt").read_text().split() if x.strip()}
    vdf = man[man["case_id"].isin(val_ids)]
    pos_ids = vdf[vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_pos]
    neg_ids = vdf[~vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_neg]
    print(f"scoring on {len(pos_ids)} tumor-positive and {len(neg_ids)} tumor-free {args.split} cases "
          f"(sliding-window, this takes a bit)...")

    # --- Dice on tumor-positive cases ---
    ev = DiceEvaluator(num_classes=int(get(cfg, "model.out_channels", 3)))
    pos_ds = get_dataset(cfg, args.split, train=False, cache=False, ids=pos_ids)
    for b in DataLoader(pos_ds, batch_size=1, num_workers=0):
        with torch.no_grad():
            logits = predict_volume(model, b["image"].to(device), cfg, device)
        ev.update(logits, b["label"])
    d = ev.aggregate()
    print(f"\n[TUMOR-POSITIVE cases, n={len(pos_ids)}]")
    print(f"  pancreas Dice : {d.get('pancreas', 0):.3f}")
    print(f"  lesion   Dice : {d.get('lesion', 0):.3f}    <-- the REAL lesion score")

    # --- specificity on tumor-free cases ---
    if neg_ids:
        spacing_prod = float(np.prod(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5])))
        neg_ds = get_dataset(cfg, args.split, train=False, cache=False, ids=neg_ids)
        clean = 0
        for b in DataLoader(neg_ds, batch_size=1, num_workers=0):
            with torch.no_grad():
                logits = predict_volume(model, b["image"].to(device), cfg, device)
            les_vox = int((logits.argmax(1) == 2).sum())
            if les_vox * spacing_prod < args.min_lesion_mm3:
                clean += 1
        print(f"\n[TUMOR-FREE cases, n={len(neg_ids)}]")
        print(f"  correctly NOT flagged (specificity): {clean}/{len(neg_ids)} = {100*clean/len(neg_ids):.0f}%")

    print("\nDone. This is the honest picture: lesion Dice on real tumors, and false-alarm rate on healthy scans.")


if __name__ == "__main__":
    main()
