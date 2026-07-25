#!/usr/bin/env python3
"""Paired 26B-26A comparison (EXP-26 primary inference).

Takes the two per-case CSVs from evaluate.py --per-case-csv (same frozen report cohort, so cases
pair by case_id) and reports, for lesion Dice (and pancreas Dice as the non-regression guard):
  * paired MEAN difference + bootstrap 95% CI   <- PRIMARY decision rule
  * descriptive: median diff, IQR, win/loss/tie (tolerance-based ties)

Accept 26B if the lesion mean diff CI excludes 0 (target mean >= +0.02) AND pancreas mean diff
is not worse than -0.01.

Usage:
  python scripts/paired_bootstrap.py --a exp26A_percase.csv --b exp26B_percase.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def boot_ci(diffs, n=10000, seed=42):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diffs), size=(n, len(diffs)))
    means = diffs[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def report(name, a, b, tol):
    d = b - a
    lo, hi = boot_ci(d)
    wins = int((d > tol).sum()); losses = int((d < -tol).sum()); ties = int((np.abs(d) <= tol).sum())
    print(f"\n[{name}]  n={len(d)} paired")
    print(f"  26A mean {a.mean():.4f}   26B mean {b.mean():.4f}")
    print(f"  mean diff (26B-26A): {d.mean():+.4f}   bootstrap 95% CI [{lo:+.4f}, {hi:+.4f}]"
          f"   {'** CI excludes 0 **' if (lo > 0 or hi < 0) else '(CI includes 0)'}")
    print(f"  median diff {np.median(d):+.4f}   IQR [{np.percentile(d,25):+.4f}, {np.percentile(d,75):+.4f}]")
    print(f"  win/loss/tie (tol {tol}): {wins}/{losses}/{ties}")
    return d.mean(), lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="26A per-case CSV (control)")
    ap.add_argument("--b", required=True, help="26B per-case CSV (treatment)")
    ap.add_argument("--tol", type=float, default=0.01, help="tie tolerance for win/loss")
    ap.add_argument("--col", default="lesion_raw", help="lesion column to compare (lesion_raw|lesion_cleaned)")
    ap.add_argument("--expect-n", type=int, default=40, help="required paired case count (frozen report cohort)")
    ap.add_argument("--require-ids", default=None,
                    help="optional cohort id file; both CSVs must contain exactly this set")
    args = ap.parse_args()

    A = pd.read_csv(args.a)
    B = pd.read_csv(args.b)

    # FAIL CLOSED (Codex fix #4): the frozen paired design requires identical, unique, complete
    # case sets and finite metrics — anything else is a silent invalidation, so abort.
    for nm, df in (("A", A), ("B", B)):
        dups = df["case_id"][df["case_id"].duplicated()].tolist()
        assert not dups, f"{nm} has duplicate case_ids: {dups[:5]}"
    sa, sb = set(A["case_id"]), set(B["case_id"])
    assert sa == sb, (f"case sets differ: only in A={sorted(sa - sb)[:5]}  only in B={sorted(sb - sa)[:5]}")
    if args.require_ids:
        want = {x.strip() for x in Path(args.require_ids).read_text().split() if x.strip()}
        assert sa == want, (f"cohort mismatch vs {args.require_ids}: "
                            f"missing={sorted(want - sa)[:5]} extra={sorted(sa - want)[:5]}")
    assert len(sa) == args.expect_n, f"expected n={args.expect_n} paired cases, got {len(sa)}"

    A = A.set_index("case_id")
    B = B.set_index("case_id").loc[A.index]     # reindex B to A's explicit order after set equality
    for col in (args.col, "pancreas_dice"):
        for nm, df in (("A", A), ("B", B)):
            bad = df[col][~np.isfinite(df[col])]
            assert bad.empty, f"{nm}.{col} has non-finite values at {bad.index.tolist()[:5]}"
    common = A.index

    print("=" * 60)
    print(f"EXP-26 paired comparison on {len(common)} cases   lesion col='{args.col}'")
    print("=" * 60)
    lm, llo, lhi = report(f"LESION Dice ({args.col})", A[args.col].values, B[args.col].values, args.tol)
    pm, plo, phi = report("PANCREAS Dice (non-regression guard)", A["pancreas_dice"].values, B["pancreas_dice"].values, args.tol)

    print("\n" + "=" * 60)
    accept_lesion = (llo > 0)
    no_regress = (pm >= -0.01)
    print(f"VERDICT: lesion CI excludes 0 (>0): {accept_lesion}   "
          f"pancreas mean diff >= -0.01: {no_regress}")
    print("ACCEPT 26B" if (accept_lesion and no_regress) else "DO NOT ACCEPT (null/negative or pancreas regressed)")
    print("  (pre-registered target: lesion mean diff >= +0.02)")


if __name__ == "__main__":
    main()
