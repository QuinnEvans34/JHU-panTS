#!/usr/bin/env python3
"""Peek at one PanTS case — see what a 3D CT scan actually looks like.

Prints the volume's shape / spacing / intensity range, then saves:
  - triplanar.png     axial + coronal + sagittal slices, pancreas (green) + lesion (red) overlaid
  - axial_montage.png 12 axial slices stepping through the pancreas (shows the 3D stack)
  - mesh3d.png        a 3D surface render of the pancreas + lesion (needs scikit-image)

Usage:
  python scripts/peek_case.py                                 # default case PanTS_00000001
  python scripts/peek_case.py --case PanTS_00000042
  python scripts/peek_case.py --root /Volumes/JHU-PanTS/PanTS/data --case PanTS_00000001
"""
import argparse
import os
import sys

import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

GREEN = "#22c55e"
RED = "#ef4444"
RED_CMAP = mcolors.ListedColormap([RED])


def load_canonical(path):
    """Load a NIfTI and reorient to closest-canonical (RAS) so slices display sensibly."""
    return nib.as_closest_canonical(nib.load(str(path)))


def load_mask(path):
    if os.path.exists(path):
        return (load_canonical(path).get_fdata() > 0.5).astype(np.uint8)
    return None


def centroid(mask):
    idx = np.argwhere(mask > 0)
    return idx.mean(0).round().astype(int) if len(idx) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/Volumes/JHU-PanTS/PanTS/data")
    ap.add_argument("--case", default="PanTS_00000001")
    ap.add_argument("--out", default=None)
    ap.add_argument("--hu", nargs=2, type=float, default=[-100, 300],
                    help="CT Hounsfield window for display (default abdominal soft tissue)")
    args = ap.parse_args()

    # locate the CT (train or test folder)
    ct_path = os.path.join(args.root, "ImageTr", args.case, "ct.nii.gz")
    if not os.path.exists(ct_path):
        alt = os.path.join(args.root, "ImageTe", args.case, "ct.nii.gz")
        ct_path = alt if os.path.exists(alt) else ct_path
    if not os.path.exists(ct_path):
        sys.exit(f"CT not found for {args.case} under {args.root} (ImageTr/ImageTe)")

    seg_dir = os.path.join(args.root, "LabelAll", args.case, "segmentations")
    panc = load_mask(os.path.join(seg_dir, "pancreas.nii.gz"))
    les = load_mask(os.path.join(seg_dir, "pancreatic_lesion.nii.gz"))

    out = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "peek", args.case)
    os.makedirs(out, exist_ok=True)

    ct_img = load_canonical(ct_path)
    ct = ct_img.get_fdata().astype(np.float32)
    zooms = [float(z) for z in ct_img.header.get_zooms()[:3]]

    print(f"\n=== {args.case} ===")
    print(f"CT: {ct_path}")
    print(f"Shape (X,Y,Z voxels): {ct.shape}")
    print(f"Voxel spacing (mm):   {tuple(round(z, 3) for z in zooms)}")
    print(f"Physical size (cm):   {tuple(round(s * z / 10.0, 1) for s, z in zip(ct.shape, zooms))}")
    print(f"Intensity (HU):       min={ct.min():.0f}  max={ct.max():.0f}  mean={ct.mean():.0f}")
    print(f"pancreas mask: {'present' if panc is not None else 'MISSING'}   "
          f"lesion mask: {'present' if les is not None else 'MISSING'}"
          + (f"  (lesion voxels = {int(les.sum())})" if les is not None else ""))

    # display window -> [0,1]
    lo, hi = args.hu
    disp = (np.clip(ct, lo, hi) - lo) / (hi - lo)

    # center the view on the lesion, else the pancreas, else the volume middle
    c = None
    if les is not None and les.sum() > 0:
        c = centroid(les)
    elif panc is not None and panc.sum() > 0:
        c = centroid(panc)
    if c is None:
        c = np.array(ct.shape) // 2
    cx, cy, cz = int(c[0]), int(c[1]), int(c[2])
    print(f"View centered on voxel (x,y,z) = {(cx, cy, cz)}")

    def plane(vol, which):
        if vol is None:
            return None
        if which == "ax":
            return np.rot90(vol[:, :, cz])
        if which == "co":
            return np.rot90(vol[:, cy, :])
        return np.rot90(vol[cx, :, :])  # sagittal

    def draw(ax, base, p, l, title):
        ax.imshow(base, cmap="gray", origin="lower", vmin=0, vmax=1)
        if p is not None and p.max() > 0:
            ax.contour(p, levels=[0.5], colors=GREEN, linewidths=0.9)
        if l is not None and l.max() > 0:
            ax.imshow(np.ma.masked_where(l == 0, l), cmap=RED_CMAP, alpha=0.55, origin="lower")
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    # 1) tri-planar
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.3))
    draw(axs[0], plane(disp, "ax"), plane(panc, "ax"), plane(les, "ax"), f"Axial  z={cz}")
    draw(axs[1], plane(disp, "co"), plane(panc, "co"), plane(les, "co"), f"Coronal  y={cy}")
    draw(axs[2], plane(disp, "sa"), plane(panc, "sa"), plane(les, "sa"), f"Sagittal  x={cx}")
    fig.suptitle(f"{args.case} — CT with pancreas (green) + lesion (red)", fontsize=11)
    fig.tight_layout()
    p1 = os.path.join(out, "triplanar.png")
    fig.savefig(p1, dpi=130)
    plt.close(fig)
    print(f"saved {p1}")

    # 2) axial montage through the pancreas z-range
    zsrc = panc if (panc is not None and panc.sum() > 0) else les
    if zsrc is not None and zsrc.sum() > 0:
        zs = np.argwhere(zsrc > 0)[:, 2]
        z0, z1 = int(zs.min()), int(zs.max())
    else:
        z0, z1 = int(ct.shape[2] * 0.35), int(ct.shape[2] * 0.65)
    zsel = np.unique(np.linspace(z0, z1, 12).astype(int))
    fig, axs = plt.subplots(3, 4, figsize=(11, 8))
    for a, z in zip(axs.ravel(), zsel):
        a.imshow(np.rot90(disp[:, :, z]), cmap="gray", origin="lower", vmin=0, vmax=1)
        if les is not None:
            ls = np.rot90(les[:, :, z])
            if ls.max() > 0:
                a.imshow(np.ma.masked_where(ls == 0, ls), cmap=RED_CMAP, alpha=0.6, origin="lower")
        if panc is not None:
            ps = np.rot90(panc[:, :, z])
            if ps.max() > 0:
                a.contour(ps, levels=[0.5], colors=GREEN, linewidths=0.6)
        a.set_title(f"z={z}", fontsize=8)
        a.axis("off")
    for a in axs.ravel()[len(zsel):]:
        a.axis("off")
    fig.suptitle(f"{args.case} — axial slices stepping through the pancreas", fontsize=11)
    fig.tight_layout()
    p2 = os.path.join(out, "axial_montage.png")
    fig.savefig(p2, dpi=120)
    plt.close(fig)
    print(f"saved {p2}")

    # 3) optional 3D surface render
    try:
        from skimage import measure
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        fig = plt.figure(figsize=(7, 7))
        ax = fig.add_subplot(111, projection="3d")

        def add_mesh(mask, color, alpha):
            if mask is None or mask.sum() == 0:
                return
            m = mask[::2, ::2, ::2]  # downsample for speed
            verts, faces, _, _ = measure.marching_cubes(m.astype(float), level=0.5)
            coll = Poly3DCollection(verts[faces], alpha=alpha)
            coll.set_facecolor(color)
            ax.add_collection3d(coll)

        add_mesh(panc, GREEN, 0.15)
        add_mesh(les, RED, 0.9)
        ref = panc if (panc is not None and panc.sum() > 0) else les
        if ref is not None and ref.sum() > 0:
            idx = np.argwhere(ref[::2, ::2, ::2] > 0)
            mn, mx = idx.min(0), idx.max(0)
            ax.set_xlim(mn[0], mx[0]); ax.set_ylim(mn[1], mx[1]); ax.set_zlim(mn[2], mx[2])
        ax.set_title(f"{args.case} — 3D pancreas (green) + lesion (red)", fontsize=10)
        ax.set_axis_off()
        p3 = os.path.join(out, "mesh3d.png")
        fig.savefig(p3, dpi=120)
        plt.close(fig)
        print(f"saved {p3}")
    except Exception as e:
        print(f"(3D mesh skipped: {e})")

    print(f"\nDone — open the PNGs in:\n  {out}\n")


if __name__ == "__main__":
    main()
