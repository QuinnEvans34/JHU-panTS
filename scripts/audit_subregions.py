#!/usr/bin/env python3
"""EXP-26 STEP 0 — subregion data audit (gates the whole experiment).

Verifies, over the EXACT cohorts EXP-26 will train/eval on (not just the train pool), that the
head/body/tail (+lesion) masks are geometrically sound against the CT, so the single mutually-
exclusive label is a valid supervision target and pancreas = head∪body∪tail is a valid resolver.

For every case it checks:
  * missing / empty individual subregion masks (head, body, tail);
  * for a manifest tumor-POSITIVE case: a present, NON-EMPTY lesion mask (else FATAL);
  * affine + shape agreement of EVERY mask (head, body, tail, lesion) against the CT itself
    (ResolveLabeld composes masks BEFORE MONAI orientation/spacing, so a CT/mask geometry
    mismatch would crash or create invalid supervision) — mismatch is FATAL, not treated as zero;
  * pairwise head/body/tail OVERLAP voxels (the single-label target is only lossless for the aux
    domain when this is negligible);
  * gap between (head∪body∪tail) and the combined pancreas.nii.gz mask;
  * lesion voxels OUTSIDE head∪body∪tail (context for the collapse GT);
  * head∪body∪tail volume outliers (upper + lower guards) — a volume failure is non-PASS.

Any FATAL / overlap-fail / volume-fail case must be excluded from BOTH arms. Writes a per-case
CSV, an EXCLUSION id file (fatal ∪ overlap-fail ∪ volume-fail), and prints a PASS/REVIEW verdict.
RUN WITH THE EXTERNAL DRIVE CONNECTED.

Usage:
  python scripts/audit_subregions.py --cohorts configs/cohorts/exp26
  python scripts/audit_subregions.py --ids configs/cohorts/exp26/train.txt
  python scripts/audit_subregions.py --split val --limit 40
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils import paths as P

try:
    import nibabel as nib
except ImportError:
    print("nibabel required: pip install nibabel --break-system-packages")
    sys.exit(1)

OVERLAP_FRAC_MAX = 0.02        # pairwise H/B/T overlap as a fraction of the union — must be tiny
VOL_MIN_ML = 20.0              # pancreas union lower guard (mL)
VOL_MAX_ML = 300.0            # pancreas union upper guard (mL) — > this = corrupt combined-style blob
AFFINE_TOL = 1e-3


def _load(path):
    """Return (bool_mask, affine, shape) or (None, None, None) if missing/unreadable."""
    if not path or not isinstance(path, str) or not Path(path).exists():
        return None, None, None
    img = nib.load(path)
    arr = np.asarray(img.dataobj) > 0
    return arr, img.affine, arr.shape


def _geom(path):
    """Header-only geometry (affine, shape) — no array materialization. Used for the CT, which
    we only need as the geometric reference (Codex non-blocking note: avoids reading 1,500 volumes)."""
    if not path or not isinstance(path, str) or not Path(path).exists():
        return None, None
    img = nib.load(path)
    return img.affine, tuple(img.shape)


def _geom_ok(shape, affine, ref_shape, ref_affine):
    return (shape == ref_shape) and (affine is not None) and np.allclose(affine, ref_affine, atol=AFFINE_TOL)


def audit_case(row):
    cid = row["case_id"]
    has_lesion = bool(row.get("has_lesion", False))
    rec = {"case_id": cid, "has_lesion": has_lesion, "fatal": False, "note": ""}

    # CT is the geometric reference EVERY mask must match (masks are composed before resample).
    ct_aff, ct_shape = _geom(row.get("ct_path"))
    if ct_shape is None:
        rec["fatal"] = True
        rec["note"] = "CT unreadable"
        return rec

    head, aff_h, sh_h = _load(row.get("head_path"))
    body, aff_b, sh_b = _load(row.get("body_path"))
    tail, aff_t, sh_t = _load(row.get("tail_path"))
    comb, aff_c, sh_c = _load(row.get("pancreas_path"))
    les, aff_l, sh_l = _load(row.get("lesion_path"))

    rec["head_missing"] = head is None
    rec["body_missing"] = body is None
    rec["tail_missing"] = tail is None
    rec["any_subregion_missing"] = (head is None) or (body is None) or (tail is None)

    # geometry of each subregion vs CT
    geom_bad = []
    for nm, m, aff, sh in (("head", head, aff_h, sh_h), ("body", body, aff_b, sh_b), ("tail", tail, aff_t, sh_t)):
        if m is None:
            geom_bad.append(f"{nm}:missing")
        elif not _geom_ok(sh, aff, ct_shape, ct_aff):
            geom_bad.append(f"{nm}:geom")
    # lesion geometry / presence
    if has_lesion:
        if les is None or int(les.sum()) == 0:
            geom_bad.append("lesion:missing/empty")
        elif not _geom_ok(sh_l, aff_l, ct_shape, ct_aff):
            geom_bad.append("lesion:geom")
    elif les is not None and not _geom_ok(sh_l, aff_l, ct_shape, ct_aff):
        geom_bad.append("lesion:geom")  # a present lesion on a negative case must still be aligned
    rec["geom_bad"] = ";".join(geom_bad)

    present_geom_ok = [m for nm, m, aff, sh in
                       (("head", head, aff_h, sh_h), ("body", body, aff_b, sh_b), ("tail", tail, aff_t, sh_t))
                       if m is not None and _geom_ok(sh, aff, ct_shape, ct_aff)]
    if len(present_geom_ok) < 3:
        rec["fatal"] = True
        rec["note"] = f"subregion issues: {rec['geom_bad']}"
        # still record whatever union we can, but this case is out
    if "lesion:" in rec["geom_bad"]:
        rec["fatal"] = True
        rec["note"] = (rec["note"] + "; " if rec["note"] else "") + "lesion geom/presence"

    # build union on the CT grid (all present subregions passed geom, so shapes == ct_shape)
    z = np.zeros(ct_shape, dtype=bool)
    H = head if (head is not None and sh_h == ct_shape) else z
    B = body if (body is not None and sh_b == ct_shape) else z
    Tl = tail if (tail is not None and sh_t == ct_shape) else z
    union = H | B | Tl

    rec["head_vox"], rec["body_vox"], rec["tail_vox"] = int(H.sum()), int(B.sum()), int(Tl.sum())
    rec["union_vox"] = int(union.sum())
    rec["head_empty"] = rec["head_vox"] == 0
    rec["body_empty"] = rec["body_vox"] == 0
    rec["tail_empty"] = rec["tail_vox"] == 0
    if rec["head_empty"] or rec["body_empty"] or rec["tail_empty"]:
        rec["fatal"] = True
        rec["note"] = (rec["note"] + "; " if rec["note"] else "") + "empty subregion"

    ov = int((H & B).sum()) + int((H & Tl).sum()) + int((B & Tl).sum())
    rec["pairwise_overlap_vox"] = ov
    rec["overlap_frac"] = (ov / rec["union_vox"]) if rec["union_vox"] else 0.0

    vox_mm3 = abs(np.linalg.det(ct_aff[:3, :3]))
    rec["union_ml"] = rec["union_vox"] * vox_mm3 / 1000.0

    if comb is not None and sh_c == ct_shape:
        cv = int(comb.sum())
        rec["combined_vox"] = cv
        rec["hbt_vs_combined"] = (abs(rec["union_vox"] - cv) / cv) if cv else float("nan")
    else:
        rec["combined_vox"] = 0
        rec["hbt_vs_combined"] = float("nan")

    if les is not None and sh_l == ct_shape:
        lv = int(les.sum())
        rec["lesion_vox"] = lv
        rec["lesion_outside_union_vox"] = int((les & ~union).sum())
        rec["lesion_outside_frac"] = (rec["lesion_outside_union_vox"] / lv) if lv else 0.0
    else:
        rec["lesion_vox"] = 0
        rec["lesion_outside_union_vox"] = 0
        rec["lesion_outside_frac"] = 0.0

    rec["fail_overlap"] = rec["overlap_frac"] > OVERLAP_FRAC_MAX
    rec["fail_volume"] = (rec["union_ml"] < VOL_MIN_ML) or (rec["union_ml"] > VOL_MAX_ML)
    return rec


def gather_ids(args, dp):
    if args.cohorts:
        ids = []
        for name in ("train", "val20", "report40", "report40_neg"):
            f = Path(args.cohorts) / f"{name}.txt"
            if f.exists():
                ids += [x.strip() for x in f.read_text().split() if x.strip()]
        return list(dict.fromkeys(ids))
    if args.ids:
        return [x.strip() for x in Path(args.ids).read_text().split() if x.strip()]
    if args.split:
        f = dp["splits_dir"] / f"{args.split}.txt"
        ids = [x.strip() for x in f.read_text().split() if x.strip()]
        return ids[: args.limit] if args.limit else ids
    raise SystemExit("provide --cohorts, --ids, or --split")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--cohorts", default=None, help="a configs/cohorts/exp26 dir (audits all 4 files)")
    ap.add_argument("--ids", default=None, help="a single id file")
    ap.add_argument("--split", default=None, help="a named split under outputs/splits")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="outputs/exp26_subregion_audit.csv")
    ap.add_argument("--exclude-out", default="outputs/exp26_exclude_ids.txt")
    args = ap.parse_args()

    cfg = load_config(args.config)
    dp = P.data_paths(cfg)
    man = pd.read_csv(dp["manifest"])
    ids = gather_ids(args, dp)

    # every requested id MUST exist in the manifest, else the cohort is malformed
    man_ids = set(man["case_id"])
    not_found = [c for c in ids if c not in man_ids]
    assert not not_found, f"{len(not_found)} requested id(s) absent from manifest: {not_found[:8]}"

    sub = man[man["case_id"].isin(set(ids))]
    print(f"auditing {len(sub)} cases (of {len(ids)} requested)...\n")

    recs = []
    for _, row in sub.iterrows():
        r = audit_case(row)
        recs.append(r)
        flag = "FATAL" if r.get("fatal") else ("fail" if (r.get("fail_overlap") or r.get("fail_volume")) else "ok")
        print(f"  {r['case_id']}  union_ml={r.get('union_ml', 0):6.1f}  "
              f"overlap={r.get('overlap_frac', 0) * 100:5.2f}%  "
              f"les_outside={r.get('lesion_outside_frac', 0) * 100:5.1f}%  [{flag}] {r.get('note', '')}")

    df = pd.DataFrame(recs)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    def _col(name):
        return df[name] if name in df else pd.Series([], dtype=bool)

    fatal = df[df["fatal"]] if "fatal" in df else df.iloc[0:0]
    n_overlap = int(_col("fail_overlap").sum())
    n_volume = int(_col("fail_volume").sum())

    # exclusion set = fatal ∪ overlap-fail ∪ volume-fail
    excl = set(fatal["case_id"].tolist())
    if "fail_overlap" in df:
        excl |= set(df[df["fail_overlap"]]["case_id"].tolist())
    if "fail_volume" in df:
        excl |= set(df[df["fail_volume"]]["case_id"].tolist())
    Path(args.exclude_out).write_text("\n".join(sorted(excl)) + ("\n" if excl else ""))

    print("\n" + "=" * 64)
    print(f"SUMMARY  ({len(df)} cases)")
    print(f"  missing a subregion : {int(_col('any_subregion_missing').sum())}")
    print(f"  empty head/body/tail: {int(_col('head_empty').sum())}/{int(_col('body_empty').sum())}/{int(_col('tail_empty').sum())}")
    if "overlap_frac" in df:
        print(f"  overlap_frac max/mean : {df['overlap_frac'].max() * 100:.2f}% / {df['overlap_frac'].mean() * 100:.3f}%  "
              f"(>{OVERLAP_FRAC_MAX * 100:.0f}% fails; {n_overlap} cases)")
        print(f"  union_ml range      : {df['union_ml'].min():.1f} - {df['union_ml'].max():.1f} mL  "
              f"({n_volume} outside [{VOL_MIN_ML},{VOL_MAX_ML}])")
        print(f"  lesion_outside max  : {df['lesion_outside_frac'].max() * 100:.1f}%")
    print(f"  FATAL cases         : {len(fatal)}")
    if len(fatal):
        print("    -> " + ", ".join(fatal["case_id"].tolist()[:20]))
    verdict = "PASS" if (len(fatal) == 0 and n_overlap == 0 and n_volume == 0) else "REVIEW"
    print("=" * 64)
    print(f"VERDICT: {verdict}")
    print(f"  overlap-fail={n_overlap}  volume-fail={n_volume}  fatal={len(fatal)}")
    print(f"CSV: {args.out}")
    print(f"EXCLUSION ({len(excl)}): {args.exclude_out}")
    if excl:
        print(f"  -> rebuild cohorts: python scripts/build_exp26_cohorts.py --exclude {args.exclude_out}")
    print("Record the max/mean overlap statistics in the cohort README (Codex: document overlap stats).")


if __name__ == "__main__":
    main()
