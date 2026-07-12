#!/usr/bin/env python3
"""Build the EXP-14 contrast-phase splits, matched on resolution AND lesion size.

EXP-13 found that clarity-weighted training raised specificity, but the sharp cohort was also
mostly non-contrast, so clarity and contrast phase were confounded. This isolates contrast phase
by holding resolution (both slice thickness and in-plane spacing), tumor count, and lesion size
constant, varying only phase:

  nc20.txt  = 20 non-contrast scans    (10 tumor / 10 healthy)
  pv20.txt  = 20 portal-venous scans   (10 tumor / 10 healthy)

Held constant so only contrast phase differs:
  - native slice thickness band (default 1.0-2.0mm; both phases land at median ~1.25mm)
  - in-plane spacing band       (default 0.7-1.1mm; both phases land at median ~0.80mm)
  - lesion size band for tumors (default 1000-20000 mm3; both phases median ~5000)
  - 10 tumor / 10 healthy per arm

Seeded and deterministic. Writes id-lists to outputs/splits/ so train.py --split nc20 /
--split pv20 can use them.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_spacing(s):
    try:
        p = [float(x) for x in str(s).split(",")]
        if len(p) >= 3:
            return (p[0] + p[1]) / 2.0, p[2]
    except Exception:
        pass
    return np.nan, np.nan


def take(df, n, rng, what):
    if len(df) < n:
        raise SystemExit(f"not enough {what}: need {n}, have {len(df)}. Loosen the bands.")
    return df.loc[rng.choice(df.index.values, size=n, replace=False)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="outputs/manifest.csv")
    ap.add_argument("--splits-dir", default="outputs/splits")
    ap.add_argument("--n", type=int, default=20, help="cases per arm")
    ap.add_argument("--tumor", type=int, default=10, help="tumor-positive cases per arm (rest healthy)")
    ap.add_argument("--slice-lo", type=float, default=1.0)
    ap.add_argument("--slice-hi", type=float, default=2.0)
    ap.add_argument("--inplane-lo", type=float, default=0.7)
    ap.add_argument("--inplane-hi", type=float, default=1.1)
    ap.add_argument("--lesion-min", type=float, default=1000.0, help="tumor size band low (mm3)")
    ap.add_argument("--lesion-max", type=float, default=20000.0, help="tumor size band high (mm3)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    m = pd.read_csv(args.manifest)
    m = m[m["split"] == "train"].copy()
    ip, sl = zip(*m["spacing"].map(parse_spacing))
    m["inplane_mm"], m["slice_mm"] = ip, sl
    m = m.dropna(subset=["slice_mm"])
    m["tumor"] = m["has_lesion"].astype(bool)
    m["phase"] = m["ct phase"].fillna("NA")

    band = m[m["slice_mm"].between(args.slice_lo, args.slice_hi)
             & m["inplane_mm"].between(args.inplane_lo, args.inplane_hi)]
    n_heal = args.n - args.tumor
    arms = {"nc20": "Non-contrast", "pv20": "Venous"}

    out = Path(args.splits_dir)
    out.mkdir(parents=True, exist_ok=True)
    for fname, phase in arms.items():
        s = band[band["phase"] == phase]
        tumors = s[s.tumor & s["lesion_volume_mm3"].between(args.lesion_min, args.lesion_max)]
        healthy = s[~s.tumor]
        arm = pd.concat([take(tumors, args.tumor, rng, f"{phase} tumors"),
                         take(healthy, n_heal, rng, f"{phase} healthy")])
        (out / f"{fname}.txt").write_text("\n".join(arm["case_id"]) + "\n")
        print(f"[{fname}]  phase={phase:12s} n={len(arm)} tumor+={int(arm.tumor.sum())}  "
              f"median slice={arm.slice_mm.median():.2f}mm  in-plane={arm.inplane_mm.median():.2f}mm  "
              f"lesion mm3 median={arm[arm.tumor]['lesion_volume_mm3'].median():.0f}")

    print(f"\nHeld constant: slice {args.slice_lo}-{args.slice_hi}mm, in-plane {args.inplane_lo}-{args.inplane_hi}mm, "
          f"tumor size {args.lesion_min:.0f}-{args.lesion_max:.0f} mm3, 10 tumor / 10 healthy.")
    print("Only contrast phase differs. Wrote outputs/splits/nc20.txt and outputs/splits/pv20.txt")


if __name__ == "__main__":
    main()
