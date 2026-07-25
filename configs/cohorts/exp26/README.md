# EXP-26 frozen cohorts

Generated: 2026-07-20 by scripts/build_exp26_cohorts.py (rebuilt from clean pool after audit).

## Construction
- **train** (1249): `scaledmax_clean` (carved from train.txt; disjoint from val/test), minus audit exclusions.
- **report40** (40): first 40 tumor-positive `val` cases, sorted by case_id. Held-out reporting cohort.
- **val20** (20): next 20 tumor-positive `val` cases (DISJOINT from report40). best.pt selection only.
- **report40_neg** (40): first 40 tumor-free `val` cases. Specificity.
- Excluded ids: 420 (union of `outputs/exp26_exclude_ids.txt` + `outputs/excl_val.txt`; see `outputs/excl_all.txt`).

## Disjointness (asserted at build + at train startup)
train ∩ val20 = ∅ · train ∩ report40 = ∅ · val20 ∩ report40 = ∅ · report40_neg disjoint from positives · all outside official test.

## Geometry audit (scripts/audit_subregions.py — VERDICT: PASS on this dir, 1349 cases)
- **H/B/T mutual overlap: max 0.00% / mean 0.000%** — head/body/tail never overlap, so the single
  mutually-exclusive 5-class label is provably lossless for the auxiliary domain (Codex's approval condition).
- pancreas-union volume range: 20.2 – 278.7 mL (all within [20, 300]; no corrupt-huge masks — the
  head∪body∪tail resolver avoids the corrupt combined-mask failure mode).
- lesion-outside-union max: 100% (informational only; lesion is class 4 regardless, and the aux domain
  excludes lesion voxels).
- Exclusion reasons (across the audited train + full val pools, 420 unique ids): empty head/body/tail
  subregion mask, CT/mask affine inconsistency (e.g. LAS CT vs LPS mask + zeroed origin, PanTS_00000259),
  and pancreas-union volume <20 mL. ~14% of the val pool and ~11% of the train pool.
- Final re-audit on the frozen cohorts: **0 fatal, 0 overlap-fail, 0 volume-fail → PASS.**

## SHA-256 (recorded in checkpoint metadata by train.py)
- `train.txt`  n=1249  `56e195a5608ff2cdf6ef26154647791f167de2161b65c3735a0712f6fa3a027c`
- `val20.txt`  n=20  `308bb957a8d629aa390e12d6f9dc3e6f7b30550943581261087fb41e5518f5e8`
- `report40.txt`  n=40  `ede0e737203513a34692afe87cb080d9fa261700709148a67ef5b611d97983e4`
- `report40_neg.txt`  n=40  `9e5c79cb3adef51053b54b8c4c35e9d2895eadbe7ebb022a59cb32bafd00e5b1`

## Provenance
PanTS case IDs only (no PHI). Both EXP-26 arms consume these exact files; regenerate only via
scripts/build_exp26_cohorts.py. Rebuilt once after the geometry audit flagged 420 defective cases
(empty subregions / affine mismatch / tiny union); the frozen files above re-audit to PASS.
