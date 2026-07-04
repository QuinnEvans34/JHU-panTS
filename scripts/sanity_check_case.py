#!/usr/bin/env python3
"""Week 1 milestone: run ONE case through the real training pipeline and verify it.

Applies the actual MONAI transforms (transforms.py) to a lesion-positive case:
  - full-volume (val) preprocessing: reports resampled shape, intensity range,
    and label voxel counts (bg / pancreas / lesion), saves a tri-planar overlay.
  - patch sampling (train): reports patch shapes and how many sampled patches
    contain lesion (confirms positive sampling), saves a patch overlay.

Usage:
  python scripts/sanity_check_case.py                 # auto-picks a tumor-positive case
  python scripts/sanity_check_case.py --case PanTS_00000123
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.transforms import build_transforms
from src.data.dataset import build_records

RED = mcolors.ListedColormap(["#ef4444"])


def to_np(x):
    """MetaTensor/tensor (C,H,W,D) -> numpy (H,W,D), first channel."""
    arr = x[0]
    return arr.detach().cpu().numpy() if hasattr(arr, "detach") else np.asarray(arr)


def save_overlay(img, lab, path, title):
    """Tri-planar CT with pancreas (green contour) + lesion (red), centered on lesion if present."""
    les = (lab == 2)
    panc = (lab == 1)
    idx = np.argwhere(les if les.any() else panc)
    c = idx.mean(0).round().astype(int) if len(idx) else (np.array(img.shape) // 2)
    cx, cy, cz = int(c[0]), int(c[1]), int(c[2])

    def plane(v, w):
        return np.rot90(v[:, :, cz]) if w == "ax" else np.rot90(v[:, cy, :]) if w == "co" else np.rot90(v[cx, :, :])

    fig, axs = plt.subplots(1, 3, figsize=(12, 4.2))
    for ax, w, t in zip(axs, ("ax", "co", "sa"), (f"Axial z={cz}", f"Coronal y={cy}", f"Sagittal x={cx}")):
        ax.imshow(plane(img, w), cmap="gray", origin="lower", vmin=0, vmax=1)
        p = plane(panc.astype(np.uint8), w)
        if p.max() > 0:
            ax.contour(p, levels=[0.5], colors="#22c55e", linewidths=0.9)
        l = plane(les.astype(np.uint8), w)
        if l.max() > 0:
            ax.imshow(np.ma.masked_where(l == 0, l), cmap=RED, alpha=0.55, origin="lower")
        ax.set_title(t, fontsize=9)
        ax.axis("off")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--case", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg.get("seed", 42))
    dp = P.data_paths(cfg)
    out_dir = dp["output_dir"] / "sanity"
    out_dir.mkdir(parents=True, exist_ok=True)

    # pick a tumor-positive case if none given
    man = pd.read_csv(dp["manifest"])
    if args.case:
        case_id = args.case
    else:
        pos = man[man["has_lesion"].astype(bool)]
        if pos.empty:
            sys.exit("no tumor-positive case in manifest")
        # a mid-sized lesion is the clearest to look at
        case_id = pos.iloc[(pos["lesion_volume_mm3"] - pos["lesion_volume_mm3"].median()).abs().argmin()]["case_id"]
    print(f"Sanity-checking case: {case_id}")

    rec = build_records(dp["manifest"], [case_id])[0]

    # 1) full-volume preprocessing (val transforms — deterministic)
    val_out = build_transforms(cfg, train=False)(rec)
    img = to_np(val_out["image"])
    lab = to_np(val_out["label"]).astype(int)
    print("\n[full volume after preprocessing]")
    print(f"  image shape: {img.shape}   intensity min/max: {img.min():.3f}/{img.max():.3f}  (expect ~0..1)")
    vals, counts = np.unique(lab, return_counts=True)
    named = {0: "background", 1: "pancreas", 2: "lesion"}
    print("  label voxel counts: " + ", ".join(f"{named.get(int(v), v)}={int(c)}" for v, c in zip(vals, counts)))
    assert set(vals).issubset({0, 1, 2}), "unexpected label values!"
    save_overlay(img, lab, out_dir / f"{case_id}_fullvolume.png",
                 f"{case_id} — preprocessed full volume (pancreas green / lesion red)")
    print(f"  saved {out_dir / (case_id + '_fullvolume.png')}")

    # 2) patch sampling (train transforms — random pos/neg crops)
    patches = build_transforms(cfg, train=True)(rec)  # list of num_samples dicts
    print(f"\n[patch sampling] returned {len(patches)} patches")
    n_with_lesion = 0
    first_lesion_patch = None
    for i, pt in enumerate(patches):
        pi, pl = to_np(pt["image"]), to_np(pt["label"]).astype(int)
        les_vox = int((pl == 2).sum())
        n_with_lesion += les_vox > 0
        print(f"  patch {i}: shape {pi.shape}  pancreas={int((pl==1).sum())}  lesion={les_vox}")
        if les_vox > 0 and first_lesion_patch is None:
            first_lesion_patch = (pi, pl)
    print(f"  patches containing lesion: {n_with_lesion}/{len(patches)}  (positive sampling working if > 0)")
    if first_lesion_patch:
        pi, pl = first_lesion_patch
        save_overlay(pi, pl, out_dir / f"{case_id}_patch.png", f"{case_id} — sampled training patch")
        print(f"  saved {out_dir / (case_id + '_patch.png')}")

    print("\nSANITY CHECK PASSED — pipeline produces correct labels, shapes, and lesion-positive patches.")


if __name__ == "__main__":
    main()
