#!/usr/bin/env python3
"""Interactive 3D viewer for one PanTS case (napari).

Opens a real window: scroll through slices, click the 2D/3D toggle (bottom-left)
and drag to rotate the whole volume, and show/hide the CT, pancreas, and lesion
layers from the left panel.

Install once:
    pip install "napari[pyqt5]"
Run:
    python scripts/view3d.py --case PanTS_00000042
    python scripts/view3d.py --case PanTS_00000042 --downsample 2   # smoother 3D
"""
import argparse
import os
import sys

import numpy as np
import nibabel as nib


def load_canonical(path):
    return nib.as_closest_canonical(nib.load(str(path)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/Volumes/JHU-PanTS/PanTS/data")
    ap.add_argument("--case", default="PanTS_00000001")
    ap.add_argument("--downsample", type=int, default=1,
                    help="shrink factor for smoother 3D rotation (e.g. 2 or 3)")
    args = ap.parse_args()

    ct_path = os.path.join(args.root, "ImageTr", args.case, "ct.nii.gz")
    if not os.path.exists(ct_path):
        alt = os.path.join(args.root, "ImageTe", args.case, "ct.nii.gz")
        ct_path = alt if os.path.exists(alt) else ct_path
    if not os.path.exists(ct_path):
        sys.exit(f"CT not found for {args.case} under {args.root}")

    seg = os.path.join(args.root, "LabelAll", args.case, "segmentations")
    ct_img = load_canonical(ct_path)
    ct = ct_img.get_fdata().astype(np.float32)
    spacing = tuple(float(z) for z in ct_img.header.get_zooms()[:3])

    def mask(name):
        p = os.path.join(seg, name)
        return (load_canonical(p).get_fdata() > 0.5).astype(np.uint8) if os.path.exists(p) else None

    panc = mask("pancreas.nii.gz")
    les = mask("pancreatic_lesion.nii.gz")

    d = args.downsample
    if d > 1:
        ct = ct[::d, ::d, ::d]
        panc = panc[::d, ::d, ::d] if panc is not None else None
        les = les[::d, ::d, ::d] if les is not None else None
        spacing = tuple(s * d for s in spacing)

    # combined label volume: 1 = pancreas, 2 = lesion (lesion wins on overlap)
    lab = np.zeros(ct.shape, np.uint8)
    if panc is not None:
        lab[panc > 0] = 1
    if les is not None:
        lab[les > 0] = 2

    import napari
    viewer = napari.Viewer(title=f"PanTS {args.case}")
    viewer.add_image(ct, name="CT", colormap="gray",
                     contrast_limits=[-160, 240], scale=spacing)
    if lab.max() > 0:
        viewer.add_labels(lab, name="pancreas / lesion", scale=spacing, opacity=0.6)

    print("napari is open. Click the square 2D/3D toggle (bottom-left) and drag to rotate; "
          "scroll to move through slices; toggle layers on the left.")
    napari.run()


if __name__ == "__main__":
    main()
