#!/usr/bin/env python3
"""Build the FROZEN, COMMITTED EXP-26 cohorts (Codex §7): train / val20 / report40 / report40_neg.

Disjointness guarantees (asserted here and again at train startup):
  train ∩ val20 = ∅, train ∩ report40 = ∅, val20 ∩ report40 = ∅,
  report40_neg disjoint from all positive cohorts, everything outside official test.

  * train        = the clean training split (default scaledmax_clean), carved from train.txt.
  * report40     = 40 tumor-POSITIVE val cases (held-out reporting cohort, deterministic).
  * val20        = 20 tumor-POSITIVE val cases, DISJOINT from report40 (best.pt selection only).
  * report40_neg = 40 tumor-FREE val cases (specificity).

Deterministic (sorted by case_id). Pass --exclude <file> (e.g. the audit's FATAL list) to drop
those ids and backfill from the sorted pool, then re-run the audit until clean, then commit.

Writes configs/cohorts/exp26/{train,val20,report40,report40_neg}.txt + README.md with SHA-256,
counts, and the intersection assertions.

Usage:
  python scripts/build_exp26_cohorts.py
  python scripts/build_exp26_cohorts.py --exclude outputs/exp26_fatal_ids.txt
"""
import argparse
import datetime
import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils import paths as P

N_REPORT_POS = 40
N_VAL_POS = 20
N_REPORT_NEG = 40


def sha256_file(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def read_ids(path):
    p = Path(path)
    return [x.strip() for x in p.read_text().split() if x.strip()] if p.exists() else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--train-split", default="scaledmax_clean", help="clean training split (from train.txt)")
    ap.add_argument("--val-split", default="val")
    ap.add_argument("--exclude", default=None, help="id file to drop (e.g. audit FATAL cases) + backfill")
    ap.add_argument("--out", default="configs/cohorts/exp26")
    args = ap.parse_args()

    cfg = load_config(args.config)
    dp = P.data_paths(cfg)
    man = pd.read_csv(dp["manifest"])
    excl = set(read_ids(args.exclude)) if args.exclude else set()

    splits_dir = dp["splits_dir"]
    train_ids = [c for c in read_ids(splits_dir / f"{args.train_split}.txt") if c not in excl]
    val_ids = set(read_ids(splits_dir / f"{args.val_split}.txt"))
    test_ids = set(read_ids(splits_dir / "test.txt"))
    if not train_ids:
        raise SystemExit(f"no training ids from {args.train_split} (or all excluded)")

    vdf = man[man["case_id"].isin(val_ids)].copy()
    vdf = vdf[~vdf["case_id"].isin(excl)]
    pos = sorted(vdf[vdf["has_lesion"].astype(bool)]["case_id"].tolist())
    neg = sorted(vdf[~vdf["has_lesion"].astype(bool)]["case_id"].tolist())
    need_pos = N_REPORT_POS + N_VAL_POS
    if len(pos) < need_pos:
        raise SystemExit(f"need {need_pos} positive val cases, have {len(pos)}")
    if len(neg) < N_REPORT_NEG:
        raise SystemExit(f"need {N_REPORT_NEG} negative val cases, have {len(neg)}")

    report40 = pos[:N_REPORT_POS]
    val20 = pos[N_REPORT_POS:N_REPORT_POS + N_VAL_POS]     # disjoint slice
    report40_neg = neg[:N_REPORT_NEG]

    cohorts = {"train": train_ids, "val20": val20, "report40": report40, "report40_neg": report40_neg}

    # --- disjointness assertions (the whole point) ---
    S = {k: set(v) for k, v in cohorts.items()}
    checks = [
        ("train ∩ val20", S["train"] & S["val20"]),
        ("train ∩ report40", S["train"] & S["report40"]),
        ("train ∩ report40_neg", S["train"] & S["report40_neg"]),
        ("val20 ∩ report40", S["val20"] & S["report40"]),
        ("report40 ∩ report40_neg", S["report40"] & S["report40_neg"]),
        ("val20 ∩ report40_neg", S["val20"] & S["report40_neg"]),
    ]
    for name, inter in checks:
        assert not inter, f"DISJOINTNESS FAIL: {name} = {len(inter)} ({sorted(inter)[:5]})"
    for k, v in S.items():
        leak = v & test_ids
        assert not leak, f"{k} overlaps official test: {len(leak)}"

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for k, v in cohorts.items():
        (out / f"{k}.txt").write_text("\n".join(v) + "\n")
    hashes = {k: sha256_file(out / f"{k}.txt") for k in cohorts}

    readme = [
        "# EXP-26 frozen cohorts",
        "",
        f"Generated: {datetime.date.today().isoformat()} by scripts/build_exp26_cohorts.py",
        "",
        "## Construction",
        f"- **train** ({len(train_ids)}): `{args.train_split}` (carved from train.txt; disjoint from val/test).",
        f"- **report40** ({len(report40)}): first {N_REPORT_POS} tumor-positive `{args.val_split}` cases, sorted by case_id. Held-out reporting cohort.",
        f"- **val20** ({len(val20)}): next {N_VAL_POS} tumor-positive `{args.val_split}` cases (DISJOINT from report40). best.pt selection only.",
        f"- **report40_neg** ({len(report40_neg)}): first {N_REPORT_NEG} tumor-free `{args.val_split}` cases. Specificity.",
        f"- Excluded ids: {len(excl)} (from `{args.exclude}`; not inlined here).",
        "",
        "## Geometry audit (fill from scripts/audit_subregions.py --cohorts on this dir)",
        "- H/B/T mutual overlap: max ____% / mean ____%",
        "- pancreas-union volume range: ____ - ____ mL",
        "- exclusion reasons: ____ empty subregion, ____ CT/mask affine mismatch, ____ union <20 mL",
        "- final re-audit VERDICT: ____",
        "",
        "## Disjointness (asserted at build + at train startup)",
        "train ∩ val20 = ∅ · train ∩ report40 = ∅ · val20 ∩ report40 = ∅ · report40_neg disjoint from positives · all outside official test.",
        "",
        "## SHA-256 (recorded in checkpoint metadata by train.py)",
    ]
    for k in ("train", "val20", "report40", "report40_neg"):
        readme.append(f"- `{k}.txt`  n={len(cohorts[k])}  `{hashes[k]}`")
    readme += [
        "",
        "## Provenance",
        "PanTS case IDs only (no PHI). Both EXP-26 arms consume these exact files; regenerate only",
        "via this script. If the geometry audit (scripts/audit_subregions.py) flags FATAL cases,",
        "re-run with `--exclude <fatal-list>` and re-audit before committing.",
    ]
    (out / "README.md").write_text("\n".join(readme) + "\n")

    print(f"wrote {out}/ :")
    for k in cohorts:
        print(f"  {k:14s} n={len(cohorts[k]):5d}  sha256={hashes[k][:16]}")
    print("all disjointness checks PASSED")
    print(f"\nNEXT: audit these cohorts on the drive ->")
    print(f"  python scripts/audit_subregions.py --cohorts {out}")


if __name__ == "__main__":
    main()
