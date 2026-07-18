#!/usr/bin/env python3
"""Build a larger, tumor-enriched training split from the train pool (EXP-17 data scale-up).

Reads the manifest only (no drive needed) and writes outputs/splits/<name>.txt. The point
is to feed the whole-box recipe MORE TUMOR CASES, the one lever every recipe null pointed to.

  python scripts/make_scaled_split.py --n-tumor 150 --n-healthy 150 --name scaled300
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils import paths as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--n-tumor", type=int, default=150)
    ap.add_argument("--n-healthy", type=int, default=150)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--name", default="scaled300")
    args = ap.parse_args()

    cfg = load_config(args.config)
    dp = P.data_paths(cfg)
    m = pd.read_csv(dp["manifest"])
    pool = m[m["split"] == "train"]
    pos = pool[pool["has_lesion"].astype(bool)]["case_id"]
    neg = pool[~pool["has_lesion"].astype(bool)]["case_id"]

    n_pos = min(args.n_tumor, len(pos))
    n_neg = min(args.n_healthy, len(neg))
    pos = pos.sample(n_pos, random_state=args.seed).tolist()
    neg = neg.sample(n_neg, random_state=args.seed).tolist()
    ids = pos + neg

    out = Path(dp["splits_dir"]) / f"{args.name}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(ids) + "\n")
    print(f"wrote {out}")
    print(f"  {len(ids)} cases: {n_pos} tumor / {n_neg} healthy  (vs dev_subset_clean: 95 / 50 tumor)")
    print(f"  tumor examples: {n_pos} (a {n_pos/50:.1f}x increase over the dev subset)")


if __name__ == "__main__":
    main()
