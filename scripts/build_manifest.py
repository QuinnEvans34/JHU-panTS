#!/usr/bin/env python3
"""Build the case manifest: pair each CT with its masks, flag lesions, join metadata.

Scans <pants_root>/LabelAll for cases that also have a CT in ImageTr/ImageTe, records
mask paths + lesion stats + CT header, and left-joins metadata.xlsx. Also inspects the
metadata for a patient identifier to answer "is one case == one patient?" (drives splits).

Usage:
  python scripts/build_manifest.py                 # full dataset (configs/level45.yaml)
  python scripts/build_manifest.py --limit 20      # first 20 cases — fast smoke test
  python scripts/build_manifest.py --root /path --out /tmp/m.csv   # overrides (testing)
Output:
  outputs/manifest.csv
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils import paths as P

# structure -> filename in each case's segmentations/ folder
KNOWN = {
    "pancreas": "pancreas.nii.gz",
    "lesion": "pancreatic_lesion.nii.gz",
    "head": "pancreas_head.nii.gz",
    "body": "pancreas_body.nii.gz",
    "tail": "pancreas_tail.nii.gz",
    "pancreatic_duct": "pancreatic_duct.nii.gz",
}


def nonzero_count(path: Path) -> int:
    # dataobj avoids a float cast — fast nonzero count on the raw mask
    return int(np.count_nonzero(np.asanyarray(nib.load(str(path)).dataobj)))


def build(dp: dict, limit=None) -> pd.DataFrame:
    label_root = dp["labels"]
    if not label_root.exists():
        sys.exit(f"labels dir not found: {label_root}")
    cases = sorted(d.name for d in label_root.iterdir() if d.is_dir())
    if limit:
        cases = cases[:limit]

    rows = []
    for i, cid in enumerate(cases, 1):
        ct_tr = dp["images_train"] / cid / "ct.nii.gz"
        ct_te = dp["images_test"] / cid / "ct.nii.gz"
        if ct_tr.exists():
            ct, split = ct_tr, "train"
        elif ct_te.exists():
            ct, split = ct_te, "test"
        else:
            continue  # label case with no downloaded image — skip

        seg = label_root / cid / "segmentations"
        present = sorted(p.name[:-7] for p in seg.glob("*.nii.gz"))  # strip ".nii.gz"

        row = {"case_id": cid, "split": split, "ct_path": str(ct)}
        for key, fname in KNOWN.items():
            fp = seg / fname
            row[f"{key}_path"] = str(fp) if fp.exists() else ""

        lesion_fp = seg / KNOWN["lesion"]
        if lesion_fp.exists():
            zooms = nib.load(str(lesion_fp)).header.get_zooms()[:3]
            cnt = nonzero_count(lesion_fp)
            row["has_lesion"] = bool(cnt > 0)
            row["lesion_voxel_count"] = cnt
            row["lesion_volume_mm3"] = round(cnt * float(np.prod(zooms)), 2)
        else:
            row["has_lesion"], row["lesion_voxel_count"], row["lesion_volume_mm3"] = False, 0, 0.0

        h = nib.load(str(ct))  # lazy — header only, no array load
        row["shape"] = "x".join(map(str, h.shape[:3]))
        row["spacing"] = ",".join(str(round(float(z), 3)) for z in h.header.get_zooms()[:3])
        row["available_structures"] = ";".join(present)
        row["n_structures"] = len(present)
        rows.append(row)
        if i % 200 == 0:
            print(f"  ...scanned {i} cases")
    return pd.DataFrame(rows)


def join_metadata(df: pd.DataFrame, meta_path: Path):
    if not Path(meta_path).exists():
        print(f"metadata not found at {meta_path} — skipping join")
        return df, None
    try:
        md = pd.read_excel(meta_path)
    except ImportError:
        print("metadata join needs 'openpyxl' (run: pip install openpyxl) — "
              "building manifest WITHOUT metadata for now.")
        return df, None
    print(f"\nmetadata.xlsx: {md.shape[0]} rows, columns = {list(md.columns)}")

    case_ids = set(df["case_id"].astype(str))
    id_col = None
    for c in md.columns:
        col_vals = set(md[c].astype(str))
        # detect the join column as the one containing most of OUR case ids
        # (robust to --limit runs where the manifest is a small subset of the metadata)
        if len(case_ids & col_vals) / max(1, len(case_ids)) > 0.5:
            id_col = c
            break
    pid_col = next((c for c in md.columns
                    if any(k in str(c).lower() for k in ["patient", "subject", "pid"])), None)

    if id_col is None:
        print("could not auto-detect a case-id column in metadata — manifest left without metadata join.")
        print("  (inspect the columns above; we'll map the join key.)")
        return df, pid_col

    print(f"join key detected: '{id_col}'   |   patient-id column: {pid_col!r}")
    md = md.copy()
    md[id_col] = md[id_col].astype(str)
    md = md.rename(columns={id_col: "case_id"})
    # avoid clobbering manifest columns
    dupe = [c for c in md.columns if c in df.columns and c != "case_id"]
    md = md.drop(columns=dupe)
    return df.merge(md, on="case_id", how="left"), pid_col


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--root", default=None, help="override dataset root (testing)")
    ap.add_argument("--out", default=None, help="override manifest output path (testing)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if args.root:
        os.environ["PANTS_ROOT"] = args.root
    cfg = load_config(args.config)
    dp = P.data_paths(cfg)
    out = Path(args.out) if args.out else dp["manifest"]
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Scanning labels under: {dp['labels']}")
    df = build(dp, args.limit)
    if df.empty:
        sys.exit("No cases with both image and labels found — check the dataset root.")
    df, pid_col = join_metadata(df, dp["metadata"])

    n = len(df)
    pos = int(df["has_lesion"].sum())
    print("\n=== SUMMARY ===")
    print(f"cases (image+labels): {n}   train {int((df.split=='train').sum())}, test {int((df.split=='test').sum())}")
    print(f"tumor-positive: {pos} ({100*pos/n:.1f}%)   tumor-free: {n-pos}")
    if pos:
        v = df.loc[df.has_lesion, "lesion_volume_mm3"]
        print(f"lesion volume mm3 — min {v.min():.0f} / median {v.median():.0f} / max {v.max():.0f}")
    if pid_col and pid_col in df.columns:
        up = df[pid_col].nunique()
        verdict = ("MULTIPLE scans per patient -> MUST group splits by patient"
                   if up < n else "one case == one patient")
        print(f"patient column '{pid_col}': {up} unique patients / {n} cases  ->  {verdict}")
    else:
        print("no patient-id column detected -> treat each case as its own patient (confirm from columns above)")

    # canonical patient_id for split grouping (fallback: one case == one patient)
    if pid_col and pid_col in df.columns:
        df["patient_id"] = df[pid_col].astype(str)
    else:
        df["patient_id"] = df["case_id"].astype(str)

    df.to_csv(out, index=False)
    print(f"\nwrote {out}   ({len(df)} rows, {df.shape[1]} columns)")


if __name__ == "__main__":
    main()
