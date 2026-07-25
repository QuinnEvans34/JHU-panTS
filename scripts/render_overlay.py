"""Render a report-ready PNG overlay from an exported ui_cases case.

Reads outputs/ui_cases/<case>/{ct,gt,pred}.nii.gz (written by export_case.py) plus the
per-case confidence from outputs/ui_cases/results.json, picks the axial slice with the most
lesion, and draws the CT slice with ground-truth vs predicted lesion contours + the pancreas
outline, titled with the CADe confidence and the cleaned Dice scores.

Usage:
  python scripts/render_overlay.py --case PanTS_00009005 --out week4/img/sample-good-case.png
"""
import argparse, json, os
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def load(case, root="outputs/ui_cases"):
    d = os.path.join(root, case)
    ct = nib.load(os.path.join(d, "ct.nii.gz")).get_fdata()
    gt = nib.load(os.path.join(d, "gt.nii.gz")).get_fdata().astype(int)
    pred = nib.load(os.path.join(d, "pred.nii.gz")).get_fdata().astype(int)
    meta = {}
    rj = os.path.join(root, "results.json")
    if os.path.exists(rj):
        meta = json.load(open(rj)).get(case, {})
    return ct, gt, pred, meta


def pick_slice(gt, pred):
    lesion = (gt == 2)
    if lesion.sum() == 0:
        lesion = (pred == 2)          # miss case: center on where the model fired
    if lesion.sum() == 0:
        lesion = (gt == 1) | (pred == 1)   # fall back to pancreas
    return int(np.argmax(lesion.sum(axis=(0, 1))))


def window(sl):
    lo, hi = np.percentile(sl, 1), np.percentile(sl, 99)
    if hi <= lo:
        hi = lo + 1.0
    return np.clip((sl - lo) / (hi - lo), 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--root", default="outputs/ui_cases")
    a = ap.parse_args()

    ct, gt, pred, meta = load(a.case, a.root)
    z = pick_slice(gt, pred)
    ct_s = np.rot90(window(ct[:, :, z]))
    gt_s, pr_s = np.rot90(gt[:, :, z]), np.rot90(pred[:, :, z])

    conf = meta.get("confidence")
    dl = meta.get("dice_lesion")
    dp = meta.get("dice_pancreas")
    vol = meta.get("lesion_volume_mm3")
    bits = [a.case]
    if dl is not None: bits.append(f"lesion Dice {dl:.2f}")
    if dp is not None: bits.append(f"pancreas Dice {dp:.2f}")
    if conf is not None: bits.append(f"CADe confidence {conf:.2f}")
    if vol is not None: bits.append(f"pred lesion {vol:.0f} mm³")
    title = "  ·  ".join(bits)

    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    ax.imshow(ct_s, cmap="gray", interpolation="nearest")
    # pancreas context (thin), then lesion GT (green) vs pred (red)
    if (gt_s == 1).any() or (pr_s == 1).any():
        ax.contour((gt_s == 1).astype(float), levels=[0.5], colors="#4f9cff", linewidths=0.8, alpha=0.7)
    if (gt_s == 2).any():
        ax.contour((gt_s == 2).astype(float), levels=[0.5], colors="#33dd77", linewidths=1.8)
    if (pr_s == 2).any():
        ax.contour((pr_s == 2).astype(float), levels=[0.5], colors="#ff4d4d", linewidths=1.8)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=9, pad=8)
    legend = [
        Line2D([0], [0], color="#33dd77", lw=2, label="ground-truth lesion"),
        Line2D([0], [0], color="#ff4d4d", lw=2, label="predicted lesion"),
        Line2D([0], [0], color="#4f9cff", lw=1.2, label="pancreas (GT)", alpha=0.8),
    ]
    ax.legend(handles=legend, loc="lower right", fontsize=7, framealpha=0.6,
              facecolor="black", edgecolor="none", labelcolor="white")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fig.tight_layout()
    fig.savefig(a.out, bbox_inches="tight")
    print(f"wrote {a.out}  (slice z={z}, {title})")


if __name__ == "__main__":
    main()
