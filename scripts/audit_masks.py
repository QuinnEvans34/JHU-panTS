#!/usr/bin/env python3
"""Data-integrity audit of the pancreas + lesion masks.

Flags cases whose pancreas mask is empty or suspiciously tiny (these are the cases that
made the pancreas crop degenerate and, at scale, would feed the model garbage). Writes a
report and an optional clean id-list that excludes the bad cases.

Usage:
  python scripts/audit_masks.py                      # audit all manifest cases
  python scripts/audit_masks.py --split dev_subset   # audit one split
  python scripts/audit_masks.py --min-panc-ml 1.0 --write-clean
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils import paths as P


def voxels_and_ml(path: str):
    """Return (nonzero voxel count, volume in mL) for a mask, or (0, 0) if missing."""
    if not isinstance(path, str) or not path or not Path(path).exists():
        return 0, 0.0
    img = nib.load(path)
    n = int(np.count_nonzero(np.asanyarray(img.dataobj)))
    vox_mm3 = float(np.prod(img.header.get_zooms()[:3]))
    return n, n * vox_mm3 / 1000.0  # mm^3 -> mL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--split", default=None, help="limit to a split id-list (e.g. dev_subset)")
    ap.add_argument("--min-panc-ml", type=float, default=1.0,
                    help="flag pancreas masks smaller than this (mL)")
    ap.add_argument("--max-panc-ml", type=float, default=300.0,
                    help="flag pancreas masks LARGER than this (mL) as over-inclusive/corrupt (normal max ~150)")
    ap.add_argument("--write-clean", action="store_true",
                    help="write a <split>_clean.txt excluding flagged cases")
    args = ap.parse_args()

    cfg = load_config(args.config)
    dp = P.data_paths(cfg)
    man = pd.read_csv(dp["manifest"])
    if args.split:
        ids = {x.strip() for x in (dp["splits_dir"] / f"{args.split}.txt").read_text().split() if x.strip()}
        man = man[man["case_id"].isin(ids)]
    print(f"auditing {len(man)} cases (min pancreas {args.min_panc_ml} mL)...\n")

    rows, flagged, recoverable = [], [], []
    for i, r in enumerate(man.itertuples(), 1):
        pv, pml = voxels_and_ml(getattr(r, "pancreas_path", ""))
        lv, lml = voxels_and_ml(getattr(r, "lesion_path", ""))
        # PanTS stores the pancreas both as a combined pancreas.nii.gz AND as head/body/tail.
        # If the combined file is empty, the organ may still live in the subregions -> RECOVERABLE.
        sub_ml = sum(voxels_and_ml(getattr(r, k, ""))[1] for k in ("head_path", "body_path", "tail_path"))
        tiny = pv == 0 or pml < args.min_panc_ml
        giant = pml > args.max_panc_ml
        bad = tiny or giant
        is_recoverable = tiny and sub_ml >= args.min_panc_ml
        flag = ("RECOVERABLE_FROM_SUBREGIONS" if is_recoverable else
                "TINY_OR_EMPTY_PANCREAS" if tiny else
                "OVERSIZED_PANCREAS" if giant else "")
        rows.append({"case_id": r.case_id, "pancreas_mL": round(pml, 2),
                     "subregion_mL": round(sub_ml, 2), "lesion_mL": round(lml, 2),
                     "has_lesion": bool(getattr(r, "has_lesion", False)), "flag": flag})
        if bad:
            flagged.append(r.case_id)
        if is_recoverable:
            recoverable.append(r.case_id)
        if i % 200 == 0:
            print(f"  ...{i}")

    rep = pd.DataFrame(rows)
    out = dp["output_dir"] / "mask_audit.csv"
    rep.to_csv(out, index=False)
    print(f"\nwrote {out}")
    print(f"pancreas mL: min {rep.pancreas_mL.min():.2f} / median {rep.pancreas_mL.median():.2f} / max {rep.pancreas_mL.max():.2f}")
    n_tiny = int((rep.flag == "TINY_OR_EMPTY_PANCREAS").sum())
    n_giant = int((rep.flag == "OVERSIZED_PANCREAS").sum())
    print(f"FLAGGED total: {len(flagged)} of {len(rep)}  "
          f"(tiny/empty {n_tiny}, oversized {n_giant}, RECOVERABLE from head+body+tail {len(recoverable)})")
    if recoverable:
        print(f"\n>>> {len(recoverable)} 'empty' cases have a populated head+body+tail — the combined pancreas.nii.gz")
        print(f">>> is empty but the organ IS labelled. FIX = union the subregions, do NOT discard these cases.")
        for c in recoverable[:10]:
            print("    recover:", c)
    print(f"\nother flagged:")
    for c in [x for x in flagged if x not in set(recoverable)][:15]:
        print("   ", c)

    if args.write_clean and args.split:
        keep = [c for c in man["case_id"] if c not in set(flagged)]
        cf = dp["splits_dir"] / f"{args.split}_clean.txt"
        cf.write_text("\n".join(keep) + "\n")
        print(f"\nwrote clean split ({len(keep)} cases) -> {cf}")


if __name__ == "__main__":
    main()
