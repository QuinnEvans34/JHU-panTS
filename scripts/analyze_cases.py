#!/usr/bin/env python3
"""Per-case failure analysis: where is the average lesion Dice actually lost?

Runs the model over the tumor-positive val cases and, for each, records lesion Dice,
tumor size, contrast phase, and whether the tumor was DETECTED (flagged at all) vs MISSED.
Then stratifies by size and phase, and reports detection sensitivity separately from
outline quality — so we can see whether the low mean is misses, the tiny-tumor tail, or
genuinely loose outlines. Eval-only; no training.

  PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/analyze_cases.py \
    --ckpt outputs/checkpoints/pants-level45/wholebox_scaled300_GOOD.pt \
    --n-pos 20 --crop-native 16 --whole-box --roi 128 --spacing 1.5
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

from monai.data import DataLoader


def dice(pred, gt):
    """NaN when the ground truth is empty (undefined), so empty-lesion cases are excluded
    rather than silently scored 1.0 (metrics audit, 2026-07-17)."""
    pred, gt = np.asarray(pred).astype(bool), np.asarray(gt).astype(bool)
    g = int(gt.sum())
    if g == 0:
        return float("nan")
    return 2.0 * int((pred & gt).sum()) / (int(pred.sum()) + g)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--n-pos", type=int, default=20)
    ap.add_argument("--min-lesion-mm3", type=float, default=50.0, help="a tumor counts as DETECTED above this predicted volume")
    ap.add_argument("--roi", type=int, default=None)
    ap.add_argument("--spacing", type=float, default=None)
    ap.add_argument("--crop-native", type=int, default=None)
    ap.add_argument("--crop-pancreas", type=float, default=None)
    ap.add_argument("--whole-box", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.roi:
        cfg["sampling"]["patch_size"] = [args.roi] * 3
        cfg["inference"]["sw_roi_size"] = [args.roi] * 3
    if args.spacing:
        cfg["preprocessing"]["target_spacing"] = [args.spacing] * 3
    if args.crop_native is not None:
        cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
    if args.crop_pancreas is not None:
        cfg["preprocessing"]["crop_to_pancreas_margin_mm"] = args.crop_pancreas
    if args.whole_box:
        cfg["preprocessing"]["whole_box"] = True
    set_seed(get(cfg, "seed", 42))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)
    spacing = np.array(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5]), float)
    vox_mm3 = float(spacing.prod())

    model = build_model(cfg).to(device)
    T.load_checkpoint(args.ckpt, model, map_location=device)
    model.eval()

    man = pd.read_csv(dp["manifest"]).set_index("case_id")
    vset = {x.strip() for x in (dp["splits_dir"] / f"{args.split}.txt").read_text().split() if x.strip()}
    vdf = man[man.index.isin(vset)]
    pos = vdf[vdf["has_lesion"].astype(bool)].index.tolist()[: args.n_pos]

    rows = []
    for cid in pos:
        for b in DataLoader(get_dataset(cfg, args.split, train=False, cache=False, ids=[cid]), batch_size=1, num_workers=0):
            with torch.no_grad():
                logits = predict_volume(model, b["image"].to(device), cfg, device)
            pred = torch.softmax(logits, 1)[0].cpu().numpy().argmax(0)
            gt = b["label"][0, 0].cpu().numpy()
        gt_mm3 = float((gt == 2).sum()) * vox_mm3
        pred_mm3 = float((pred == 2).sum()) * vox_mm3
        rows.append({
            "case": cid,
            "gt_mm3": round(gt_mm3, 0),
            "pred_mm3": round(pred_mm3, 0),
            "dice": dice(pred == 2, gt == 2),   # full precision; round only when printing
            "detected": pred_mm3 >= args.min_lesion_mm3,
            "phase": str(man.loc[cid, "ct phase"]) if "ct phase" in man.columns else "?",
        })
    df = pd.DataFrame(rows)

    def bin_size(v):
        return "small (<1 cm3)" if v < 1000 else ("medium (1-8 cm3)" if v < 8000 else "large (>8 cm3)")
    df["size_bin"] = df["gt_mm3"].apply(bin_size)

    print(f"\n=== per-case (n={len(df)}), sorted by tumor size ===")
    disp = df.sort_values("gt_mm3")[["case", "gt_mm3", "pred_mm3", "dice", "detected", "phase"]].copy()
    disp["dice"] = disp["dice"].round(3)
    print(disp.to_string(index=False))

    det = df["detected"].sum()
    print(f"\n=== headline ===")
    print(f"mean lesion Dice (all)          : {df['dice'].mean():.3f}")
    print(f"detection sensitivity           : {det}/{len(df)} = {100*det/len(df):.0f}%  (tumor flagged at all)")
    print(f"mean lesion Dice (detected only): {df[df['detected']]['dice'].mean():.3f}  (outline quality when we DO catch it)")

    print(f"\n=== by tumor size ===")
    g = df.groupby("size_bin").agg(n=("dice", "size"), mean_dice=("dice", "mean"),
                                   detect_rate=("detected", "mean")).reindex(
        ["small (<1 cm3)", "medium (1-8 cm3)", "large (>8 cm3)"]).dropna(how="all")
    for name, r in g.iterrows():
        print(f"  {name:<18} n={int(r['n']):>2}  mean Dice {r['mean_dice']:.3f}  detected {100*r['detect_rate']:.0f}%")

    print(f"\n=== by contrast phase ===")
    for name, r in df.groupby("phase").agg(n=("dice", "size"), mean_dice=("dice", "mean"),
                                           detect_rate=("detected", "mean")).iterrows():
        print(f"  {str(name):<16} n={int(r['n']):>2}  mean Dice {r['mean_dice']:.3f}  detected {100*r['detect_rate']:.0f}%")


if __name__ == "__main__":
    main()
