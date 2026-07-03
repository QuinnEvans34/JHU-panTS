#!/usr/bin/env python3
"""Create patient-level, tumor-stratified train/validation splits from the manifest.

- Test set = the official ImageTe cases (held out, never trained on).
- Train/val carved from the ImageTr pool, GROUPED by patient (no leakage) and
  STRATIFIED by has_lesion (balanced tumor fraction).
- Optional dev subset for fast iteration.
Writes case-id lists to outputs/splits/ (train.txt, val.txt, test.txt, dev_subset.txt).

Usage:
  python scripts/create_splits.py
  python scripts/create_splits.py --manifest /tmp/m.csv     # testing
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils import paths as P
from src.utils.seed import set_seed


def write_list(path: Path, ids) -> None:
    path.write_text("\n".join(map(str, ids)) + ("\n" if len(ids) else ""))


def frac_pos(df: pd.DataFrame, ids) -> float:
    s = df[df.case_id.isin(ids)]
    return 100.0 * s.has_lesion.mean() if len(s) else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    dp = P.data_paths(cfg)
    P.ensure_output_dirs(dp)
    seed = int(get(cfg, "seed", 42))
    set_seed(seed)

    man = Path(args.manifest) if args.manifest else dp["manifest"]
    if not man.exists():
        sys.exit(f"manifest not found: {man}  (run build_manifest.py first)")
    df = pd.read_csv(man)
    df["has_lesion"] = df["has_lesion"].astype(bool)
    splits_dir = dp["splits_dir"]

    # 1) official held-out test set
    test_ids = df[df.split == "test"]["case_id"].tolist()
    write_list(splits_dir / "test.txt", test_ids)

    # 2) patient-level, tumor-stratified train/val from the training pool
    pool = df[df.split == "train"].reset_index(drop=True)
    if pool.empty:
        sys.exit("no train-split cases in manifest")

    val_frac = float(get(cfg, "split.val_fraction", 0.2))
    stratify_on = get(cfg, "split.stratify_on", "has_lesion")
    groups = pool["patient_id"].astype(str).values
    y = pool[stratify_on].astype(int).values

    from sklearn.model_selection import StratifiedGroupKFold
    n_splits = max(2, round(1.0 / val_frac))
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    train_idx, val_idx = next(iter(sgkf.split(pool, y, groups)))

    train_ids = pool.loc[train_idx, "case_id"].tolist()
    val_ids = pool.loc[val_idx, "case_id"].tolist()

    # leakage guard: no patient in both train and val
    tp = set(pool.loc[train_idx, "patient_id"])
    vp = set(pool.loc[val_idx, "patient_id"])
    assert tp.isdisjoint(vp), "PATIENT LEAKAGE between train and val!"

    write_list(splits_dir / "train.txt", train_ids)
    write_list(splits_dir / "val.txt", val_ids)

    # 3) optional dev subset (fast iteration): n cases at a target positive fraction
    ds = get(cfg, "split.dev_subset", {}) or {}
    dev_ids = []
    if ds.get("enabled"):
        n = int(ds.get("n_cases", 100))
        pf = float(ds.get("positive_fraction", 0.5))
        tr = pool[pool.case_id.isin(train_ids)]
        pos = tr[tr.has_lesion]["case_id"].tolist()
        neg = tr[~tr.has_lesion]["case_id"].tolist()
        rng = np.random.default_rng(seed)
        n_pos = min(len(pos), int(round(n * pf)))
        n_neg = min(len(neg), n - n_pos)
        dev_ids = list(rng.choice(pos, n_pos, replace=False)) + list(rng.choice(neg, n_neg, replace=False))
        rng.shuffle(dev_ids)
        write_list(splits_dir / "dev_subset.txt", dev_ids)

    # 4) summary
    print("=== SPLITS ===")
    print(f"train: {len(train_ids)} cases ({frac_pos(df, train_ids):.1f}% tumor)  |  "
          f"val: {len(val_ids)} ({frac_pos(df, val_ids):.1f}%)  |  "
          f"test (official): {len(test_ids)} ({frac_pos(df, test_ids):.1f}%)")
    print(f"patients — train {len(tp)}, val {len(vp)}  (disjoint: OK, no leakage)")
    if dev_ids:
        print(f"dev_subset: {len(dev_ids)} cases ({frac_pos(df, dev_ids):.1f}% tumor)")
    print(f"wrote lists to {splits_dir}")


if __name__ == "__main__":
    main()
