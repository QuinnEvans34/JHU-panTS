#!/usr/bin/env python3
"""Scan PanTS cases for non-empty pancreatic_lesion masks — i.e. patients with a tumor.

Usage:
  python scripts/find_lesions.py                 # scan first 300 cases, stop after 8 hits
  python scripts/find_lesions.py --limit 500 --need 15
  python scripts/find_lesions.py --root /Volumes/JHU-PanTS/PanTS/data
"""
import argparse
import os

import numpy as np
import nibabel as nib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/Volumes/JHU-PanTS/PanTS/data")
    ap.add_argument("--limit", type=int, default=300, help="how many cases to scan")
    ap.add_argument("--need", type=int, default=8, help="stop after finding this many positives")
    args = ap.parse_args()

    label_root = os.path.join(args.root, "LabelAll")
    cases = sorted(d for d in os.listdir(label_root)
                   if os.path.isdir(os.path.join(label_root, d)))[:args.limit]

    print(f"Scanning {len(cases)} cases for pancreatic lesions...\n")
    found = []
    for i, c in enumerate(cases, 1):
        p = os.path.join(label_root, c, "segmentations", "pancreatic_lesion.nii.gz")
        if not os.path.exists(p):
            continue
        # dataobj avoids a float cast — fast nonzero count on the raw mask
        n = int(np.count_nonzero(np.asanyarray(nib.load(p).dataobj)))
        if n > 0:
            found.append((c, n))
            print(f"  ✓ {c}   lesion_voxels = {n:>7}")
            if len(found) >= args.need:
                break
        if i % 50 == 0:
            print(f"    ...scanned {i}, found {len(found)} so far")

    print(f"\nFound {len(found)} lesion-positive case(s) in the first {len(cases)} scanned.")
    if found:
        best = max(found, key=lambda t: t[1])
        print(f"Biggest lesion: {best[0]} ({best[1]} voxels)")
        print(f"\nView one with:\n  python scripts/peek_case.py --case {found[0][0]}")


if __name__ == "__main__":
    main()
