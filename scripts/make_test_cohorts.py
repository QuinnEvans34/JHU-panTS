"""Build deterministic, provenance-checked TEST cohorts for the final held-out evaluation (M4A1 §2).

Writes outputs/splits/test_pos.txt (all tumor-positive test cases) and test_neg.txt (tumor-free test
cases), sorted, so the final eval uses explicit --pos-ids/--neg-ids rather than "first N" ordering.

Per Codex review it: verifies every id is in the official test split, asserts positive/negative are
disjoint, asserts expected counts, writes sorted ids, prints SHA-256 for provenance, and refuses to
overwrite an existing file unless the content is identical.

Usage:
  python scripts/make_test_cohorts.py            # all 151 pos + all 750 neg (final headline eval)
  python scripts/make_test_cohorts.py --n-neg 151  # balanced 151-neg subset (dev/quick spec read)
"""
import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils import paths as P


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def write_ids(path: Path, ids: list):
    content = "\n".join(ids) + ("\n" if ids else "")
    if path.exists() and path.read_text() != content:
        raise SystemExit(f"REFUSING to overwrite {path} with different content "
                         f"(delete it first if you really mean to regenerate).")
    path.write_text(content)
    return sha256_text(content)


def build_cohorts(man: pd.DataFrame, test_ids: set, n_pos=None, n_neg=None,
                  expected_pos=None, expected_neg=None):
    """Return (pos, neg) sorted id lists from the test split, with real safety asserts.
    Separated from I/O so it is unit-testable. Raises AssertionError on any violation:
      * every test id must have a manifest row (real membership check, not a tautology);
      * no duplicate case_ids in the manifest for the test subset;
      * if expected_pos/expected_neg given, the FULL pool counts must match (guards drift);
      * pos/neg disjoint and non-empty after any limiting."""
    tdf = man[man["case_id"].isin(test_ids)]
    dups = tdf["case_id"][tdf["case_id"].duplicated()].tolist()
    assert not dups, f"duplicate case_id in manifest for test subset: {dups[:5]}"
    missing = set(test_ids) - set(tdf["case_id"])
    assert not missing, f"{len(missing)} test id(s) absent from manifest: {sorted(missing)[:5]}"

    pos_all = sorted(tdf[tdf["has_lesion"].astype(bool)]["case_id"].tolist())
    neg_all = sorted(tdf[~tdf["has_lesion"].astype(bool)]["case_id"].tolist())
    if expected_pos is not None:
        assert len(pos_all) == expected_pos, f"expected {expected_pos} positives, got {len(pos_all)}"
    if expected_neg is not None:
        assert len(neg_all) == expected_neg, f"expected {expected_neg} negatives, got {len(neg_all)}"

    pos = pos_all[:n_pos] if n_pos else pos_all
    neg = neg_all[:n_neg] if n_neg else neg_all
    assert not (set(pos) & set(neg)), "positive and negative cohorts overlap"
    assert len(pos) > 0 and len(neg) > 0, "empty cohort"
    return pos, neg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--n-neg", type=int, default=None, help="limit negatives (default: all)")
    ap.add_argument("--n-pos", type=int, default=None, help="limit positives (default: all)")
    ap.add_argument("--expect-pos", type=int, default=151, help="assert this many test positives exist")
    ap.add_argument("--expect-neg", type=int, default=750, help="assert this many test negatives exist")
    args = ap.parse_args()

    # validate limits are positive integers (0 / negatives are user errors, not "no limit")
    for name, v in (("--n-pos", args.n_pos), ("--n-neg", args.n_neg)):
        if v is not None and v <= 0:
            raise SystemExit(f"{name} must be a positive integer (got {v})")

    cfg = load_config(args.config)
    dp = P.data_paths(cfg)
    man = pd.read_csv(dp["manifest"])
    test_ids = {x.strip() for x in (dp["splits_dir"] / "test.txt").read_text().split() if x.strip()}
    assert test_ids, "test.txt is empty"

    pos, neg = build_cohorts(man, test_ids, args.n_pos, args.n_neg,
                             expected_pos=args.expect_pos, expected_neg=args.expect_neg)

    # A subset must NEVER occupy the canonical filenames (that would block the full generation).
    is_subset = bool(args.n_pos or args.n_neg)
    suffix = "_subset" if is_subset else ""
    sp = write_ids(dp["splits_dir"] / f"test_pos{suffix}.txt", pos)
    sn = write_ids(dp["splits_dir"] / f"test_neg{suffix}.txt", neg)

    print(f"[test-cohorts] {'SUBSET (dev/quick — label as such; NOT the final headline)' if is_subset else 'FULL (final headline eval)'}")
    print(f"  test_pos{suffix}.txt  n={len(pos)}  sha256={sp[:16]}")
    print(f"  test_neg{suffix}.txt  n={len(neg)}  sha256={sn[:16]}")
    print("  disjoint + all in official test split  OK")
    print(f"Final eval: evaluate.py --split test --pos-ids .../test_pos{suffix}.txt --neg-ids .../test_neg{suffix}.txt")


if __name__ == "__main__":
    main()
