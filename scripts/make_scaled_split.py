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

    # CRITICAL (Codex audit 2026-07-19): sample from the CARVED train fold (train.txt), NOT the
    # manifest "split" column — that column marks the ImageTr/ImageTe SOURCE FOLDER, which still
    # contains the cases later carved into val.txt. Using it leaked 266 val cases into scaledmax.
    def read_ids(name):
        f = Path(dp["splits_dir"]) / f"{name}.txt"
        return {x.strip() for x in f.read_text().split() if x.strip()} if f.exists() else set()
    train_ids, val_ids, test_ids = read_ids("train"), read_ids("val"), read_ids("test")
    if not train_ids:
        sys.exit("outputs/splits/train.txt not found — run scripts/create_splits.py first")

    pool = m[m["case_id"].isin(train_ids)]                 # <- disjoint from val/test by construction
    pos = pool[pool["has_lesion"].astype(bool)]["case_id"]
    neg = pool[~pool["has_lesion"].astype(bool)]["case_id"]

    n_pos = min(args.n_tumor, len(pos))
    n_neg = min(args.n_healthy, len(neg))
    pos = pos.sample(n_pos, random_state=args.seed).tolist()
    neg = neg.sample(n_neg, random_state=args.seed).tolist()
    ids = pos + neg

    # hard guarantee: NOTHING here may appear in val or test
    leak = set(ids) & (val_ids | test_ids)
    assert not leak, f"LEAKAGE: {len(leak)} of {len(ids)} sampled cases are in val/test — aborting: {sorted(leak)[:5]}"

    out = Path(dp["splits_dir"]) / f"{args.name}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(ids) + "\n")
    print(f"wrote {out}")
    print(f"  {len(ids)} cases: {n_pos} tumor / {n_neg} healthy  (pool = train.txt fold, {len(train_ids)} cases)")
    print(f"  DISJOINTNESS CHECK: overlap with val = {len(set(ids) & val_ids)}, with test = {len(set(ids) & test_ids)}  (both must be 0)")


if __name__ == "__main__":
    main()
