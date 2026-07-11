#!/usr/bin/env python3
"""Build the EXP-13 clarity-stratified training splits (curriculum-inspired data selection).

Two 20-case training sets, both balanced 10 tumor / 10 healthy, drawn from the TRAIN pool:
  clarity20.txt  (treatment)  = 12 from the clearest scans (thinnest slices) + 8 from the rest
  repr20.txt     (baseline)   = 20 sampled representatively across the whole clarity range

"Clearest" = highest spatial resolution: native slice thickness first, then in-plane spacing.
Everything is seeded and the two sets are disjoint, so the ONLY thing that differs between the
arms is training-set clarity (tumor count, size, and eval set are all held constant). Writes
id-lists to outputs/splits/ so train.py --split clarity20 / --split repr20 can use them.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_spacing(s):
    """'x,y,z' -> (in-plane mm = mean(x,y), slice mm = z). NaN on malformed."""
    try:
        parts = [float(x) for x in str(s).split(",")]
        if len(parts) >= 3:
            return (parts[0] + parts[1]) / 2.0, parts[2]
    except Exception:
        pass
    return np.nan, np.nan


def take(df, n, rng):
    """Deterministically sample n rows without replacement."""
    if len(df) < n:
        raise SystemExit(f"not enough rows to sample: need {n}, have {len(df)}")
    idx = rng.choice(df.index.values, size=n, replace=False)
    return df.loc[idx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="outputs/manifest.csv")
    ap.add_argument("--splits-dir", default="outputs/splits")
    ap.add_argument("--n", type=int, default=20, help="cases per arm")
    ap.add_argument("--n-clear", type=int, default=12, help="clarity arm: how many from the clearest pool")
    ap.add_argument("--tumor", type=int, default=10, help="tumor-positive cases per arm (rest healthy)")
    ap.add_argument("--clear-slice-max", type=float, default=1.0,
                    help="native slice thickness (mm) at or below which a scan counts as 'clearest'")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    m = pd.read_csv(args.manifest)
    m = m[m["split"] == "train"].copy()
    ip, sl = zip(*m["spacing"].map(parse_spacing))
    m["inplane_mm"], m["slice_mm"] = ip, sl
    m = m.dropna(subset=["slice_mm"])
    m["tumor"] = m["has_lesion"].astype(bool)

    n_heal = args.n - args.tumor
    clear_tumor = args.n_clear * args.tumor // args.n     # 12*10/20 = 6
    clear_heal = args.n_clear - clear_tumor               # 6
    rest_tumor = args.tumor - clear_tumor                 # 4
    rest_heal = n_heal - clear_heal                       # 4

    clearest = m[m["slice_mm"] <= args.clear_slice_max]
    rest = m[m["slice_mm"] > args.clear_slice_max]
    print(f"clearest pool (slice <= {args.clear_slice_max}mm): {len(clearest)} scans, "
          f"{int(clearest['tumor'].sum())} tumor+   |   rest: {len(rest)} scans, "
          f"{int(rest['tumor'].sum())} tumor+")

    # ---- Arm B: clarity-weighted (treatment) ----
    armB = pd.concat([
        take(clearest[clearest.tumor], clear_tumor, rng),
        take(clearest[~clearest.tumor], clear_heal, rng),
        take(rest[rest.tumor], rest_tumor, rng),
        take(rest[~rest.tumor], rest_heal, rng),
    ])
    usedB = set(armB["case_id"])

    # ---- Arm A: representative (baseline), disjoint from B, same 10/10 ----
    pool = m[~m["case_id"].isin(usedB)]
    armA = pd.concat([
        take(pool[pool.tumor], args.tumor, rng),
        take(pool[~pool.tumor], n_heal, rng),
    ])

    out = Path(args.splits_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "clarity20.txt").write_text("\n".join(armB["case_id"]) + "\n")
    (out / "repr20.txt").write_text("\n".join(armA["case_id"]) + "\n")

    def summarize(name, df):
        print(f"\n[{name}]  n={len(df)}  tumor+={int(df['tumor'].sum())}  "
              f"median slice={df['slice_mm'].median():.2f}mm  "
              f"median in-plane={df['inplane_mm'].median():.2f}mm")
        print("   site mix:", dict(df["site"].value_counts().head(8)))

    summarize("clarity20 (treatment)", armB)
    summarize("repr20 (baseline)", armA)
    print("\nwrote outputs/splits/clarity20.txt and outputs/splits/repr20.txt")


if __name__ == "__main__":
    main()
