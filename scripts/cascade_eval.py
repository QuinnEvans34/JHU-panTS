#!/usr/bin/env python3
"""Autonomous cascade evaluation (EXP-20): the honest, comparable-to-published number.

Every lesion Dice so far was measured on a crop built from the GROUND-TRUTH pancreas
(an "oracle ROI" — the model was handed *where* before being asked *what*). Published
whole-scan numbers do not get that gift, so those numbers are not comparable. This script
removes the gift: a localizer finds the pancreas on the FULL scan, and ITS box (errors and
all) is what feeds the whole-box lesion segmenter.

Single-variable switch --roi-from {gt-union, gt-panc, pred} — everything downstream of the
crop (resize to a 128 cube, Stage-2 segmenter, scoring, post-processing, threshold sweep) is
identical, so the three modes isolate exactly one thing each:

  gt-union : crop to the GT pancreas UNION lesion box. Matches how EXP-12/17/17c were scored,
             so this should REPRODUCE the oracle number (~0.528) and thereby VALIDATE this
             harness. If it does not, the harness itself has drifted and nothing else is trusted.
  gt-panc  : crop to the GT pancreas-ONLY box (no lesion). This is EXP-19, the ROI-leak control:
             the gap gt-union -> gt-panc is how much the lesion-extent leak was inflating Dice.
  pred     : crop to the LOCALIZER's predicted pancreas box. This is EXP-20, the autonomous number.
             It is pancreas-only by construction (the localizer never sees a lesion label), so it
             is also leak-free; the gap gt-panc -> pred is the pure cost of imperfect localization.

Two stages, both full-volume sliding-window, NO retraining:
  Stage 1 (localizer): a full-scan pancreas model -> pancreas mask -> largest component -> bbox + buffer.
  Stage 2 (segmenter): the whole-box model on the cropped 128 cube -> pancreas + lesion.

Scoring matches evaluate.py exactly: lesion/pancreas Dice on tumor-positive cases (raw + cleaned),
specificity on tumor-free cases, and an optional threshold sweep. It also reports LOCALIZER
COVERAGE (does the predicted box actually contain the GT pancreas and the tumor?), because a box
that clips the tumor is the cascade's main failure mode.

Usage (see docs/experiments.md EXP-20 for the full runbook):
  # 1. harness check — should land near the oracle 0.528
  python scripts/cascade_eval.py --seg-ckpt .../wholebox_scaledmax_GOOD.pt \
      --loc-ckpt .../p128_ctx_step6000.pt --roi-from gt-union --n-pos 40 --n-neg 40
  # 2. the autonomous number
  python scripts/cascade_eval.py --seg-ckpt .../wholebox_scaledmax_GOOD.pt \
      --loc-ckpt .../p128_ctx_step6000.pt --roi-from pred --n-pos 40 --n-neg 40 --sweep
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import torch
from monai.inferers import sliding_window_inference
from monai.transforms import (
    Compose, LoadImaged, EnsureChannelFirstd, Orientationd, Spacingd,
    ScaleIntensityRanged, EnsureTyped, ResizeWithPadOrCrop,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.transforms import ComposeLabeld
from src.data.dataset import build_records, load_split_ids
from src.models.segresnet import build_model
from src.training import trainer as T
from src.inference.postprocess import postprocess, keep_largest_component, _dilate


def dice(pred: np.ndarray, gt: np.ndarray) -> float:
    """NaN-safe Dice (identical to evaluate.py): returns NaN when the GT is empty so the
    case is excluded via nanmean, never silently awarded 1.0 (metrics audit, 2026-07-17)."""
    pred, gt = np.asarray(pred).astype(bool), np.asarray(gt).astype(bool)
    g = int(gt.sum())
    if g == 0:
        return float("nan")
    return 2.0 * int((pred & gt).sum()) / (int(pred.sum()) + g)


def preprocess_transform(spacing, hu_lo, hu_hi):
    """Load a case and produce image (float [0,1]) + GT 3-class label on the SAME 1.5mm grid.
    No cropping here — the cascade decides the crop from a pancreas mask afterwards."""
    keys = ["image", "pancreas", "lesion"]
    return Compose([
        LoadImaged(keys=keys, allow_missing_keys=True),
        EnsureChannelFirstd(keys=keys, allow_missing_keys=True),
        ComposeLabeld("pancreas", "lesion", "label"),          # GT pancreas->1, lesion->2
        Orientationd(keys=["image", "label"], axcodes="RAS"),
        Spacingd(keys=["image", "label"], pixdim=spacing, mode=("bilinear", "nearest")),
        ScaleIntensityRanged(keys="image", a_min=hu_lo, a_max=hu_hi, b_min=0.0, b_max=1.0, clip=True),
        EnsureTyped(keys=["image", "label"]),
    ])


def sw(model, img_cpu, roi, device, inf):
    """Full-volume sliding-window inference. Windows run on `device` (MPS); the stitched
    output lives on CPU to relieve MPS memory — same policy as sliding_window.py."""
    return sliding_window_inference(
        inputs=img_cpu, roi_size=(roi, roi, roi),
        sw_batch_size=int(inf.get("sw_batch_size", 2)), predictor=model,
        overlap=float(inf.get("overlap", 0.5)), mode=inf.get("blend_mode", "gaussian"),
        sw_device=device, device=torch.device(inf.get("stitch_device", "cpu")),
    )


def bbox_from_mask(mask: np.ndarray, margin: int):
    """Axis-aligned bounding box of a binary mask, expanded by `margin` voxels and clipped
    to the volume. Returns [(lo,hi), (lo,hi), (lo,hi)] or None if the mask is empty."""
    idx = np.array(np.nonzero(mask))
    if idx.size == 0:
        return None
    shape = mask.shape
    lo = np.maximum(idx.min(axis=1) - margin, 0)
    hi = np.minimum(idx.max(axis=1) + 1 + margin, shape)
    return [(int(lo[i]), int(hi[i])) for i in range(3)]


def coverage(gt_mask: np.ndarray, box) -> float:
    """Fraction of a GT mask's voxels that fall inside the predicted box (NaN if GT empty)."""
    total = int(gt_mask.sum())
    if total == 0:
        return float("nan")
    sl = tuple(slice(lo, hi) for lo, hi in box)
    return int(gt_mask[sl].sum()) / total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--seg-ckpt", default=None, help="Stage-2 whole-box segmenter (e.g. wholebox_scaledmax_GOOD.pt); not needed for --audit-coverage")
    ap.add_argument("--loc-ckpt", required=True, help="Stage-1 full-scan pancreas localizer (e.g. p128_ctx_step6000.pt)")
    ap.add_argument("--roi-from", choices=["gt-union", "gt-panc", "pred"], default="pred",
                    help="crop-box source: gt-union (harness check ~oracle) | gt-panc (EXP-19 leak) | pred (EXP-20 autonomous)")
    ap.add_argument("--split", default="val")
    ap.add_argument("--n-pos", type=int, default=40)
    ap.add_argument("--n-neg", type=int, default=40)
    ap.add_argument("--roi", type=int, default=128, help="Stage-2 cube size; MUST match the segmenter's training patch")
    ap.add_argument("--loc-roi", type=int, default=128, help="Stage-1 sliding-window size; the localizer's training patch")
    ap.add_argument("--spacing", type=float, default=1.5, help="resample spacing (mm); MUST match both models' training")
    ap.add_argument("--margin-vox", type=int, default=12,
                    help="buffer added around the pancreas box, in resampled voxels (12 @1.5mm ~= 18mm)")
    ap.add_argument("--loc-thresh", type=float, default=None,
                    help="RECALL mode: build the box from voxels with pancreas prob >= this (e.g. 0.1) "
                         "instead of the argmax. Low threshold captures the uncertain tail -> higher coverage. "
                         "Default None = argmax (backward compatible).")
    ap.add_argument("--loc-dilate", type=int, default=0,
                    help="dilate the predicted pancreas mask by this many voxels before taking the box "
                         "(a shape-following safety skin; 0 = off)")
    ap.add_argument("--min-lesion-mm3", type=float, default=None)
    ap.add_argument("--lesion-within-pancreas-mm", type=float, default=None)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--thresholds", default="0.3,0.4,0.5,0.6,0.7,0.8,0.9")
    ap.add_argument("--sanity", type=str, default=None,
                    help="run ONE case id, save an overlay PNG to outputs/, and exit (verify the crop before trusting numbers)")
    ap.add_argument("--audit-coverage", action="store_true",
                    help="CONTAINMENT AUDIT: run the localizer ONLY (no Stage-2, fast) over a large cohort and report "
                         "per-case pancreas/tumor containment + per-face clearance in mm + a statistical failure bound")
    ap.add_argument("--diag-localizer", type=str, default=None,
                    help="comma-separated case ids: print a per-case localizer diagnostic (predicted vs GT pancreas "
                         "location/size along the body axis) to see WHY a box misses, and exit")
    ap.add_argument("--n-audit", type=int, default=200,
                    help="number of cases for --audit-coverage (all pancreas-bearing cases in the split, up to this)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    set_seed(get(cfg, "seed", 42))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)
    spacing = (args.spacing, args.spacing, args.spacing)
    hu_lo, hu_hi = get(cfg, "preprocessing.hu_window", [-100, 300])
    vox_mm3 = float(np.prod(spacing))
    min_mm3 = (args.min_lesion_mm3 if args.min_lesion_mm3 is not None
               else float(get(cfg, "inference.postprocess.lesion_min_volume_mm3", 50)))
    inf = cfg["inference"]
    within = args.lesion_within_pancreas_mm

    # --- two models, same architecture, different weights ---
    localizer = build_model(cfg).to(device)
    lstep, _ = T.load_checkpoint(args.loc_ckpt, localizer, map_location=device)
    localizer.eval()
    print(f"localizer: {args.loc_ckpt} (step {lstep})")
    segmenter = None
    if not (args.audit_coverage or args.diag_localizer):   # these modes are localizer-only
        if not args.seg_ckpt:
            sys.exit("--seg-ckpt is required unless you pass --audit-coverage or --diag-localizer")
        segmenter = build_model(cfg).to(device)
        sstep, _ = T.load_checkpoint(args.seg_ckpt, segmenter, map_location=device)
        segmenter.eval()
        print(f"segmenter: {args.seg_ckpt} (step {sstep})")
    print(f"roi-from={args.roi_from}  margin={args.margin_vox}vox  spacing={args.spacing}mm  "
          f"cube={args.roi}  min-lesion={min_mm3:.0f}mm3  device={device}\n")

    pre = preprocess_transform(spacing, hu_lo, hu_hi)
    resizer = ResizeWithPadOrCrop(spatial_size=(args.roi, args.roi, args.roi))
    thresholds = [float(x) for x in args.thresholds.split(",") if x.strip()] if args.sweep else []

    @torch.no_grad()
    def predict_pancreas_box(image, label):
        """Single source of truth for the crop box. Returns (box, box_dims, oversize, loc_failed).
        The box is built from the chosen source mask (predicted pancreas / GT pancreas / GT union)
        plus the buffer; oversize flags a box larger than the cube (would be center-cropped)."""
        if args.roi_from == "pred":
            loc_logits = sw(localizer, image.unsqueeze(0), args.loc_roi, device, inf)  # (1,3,H,W,D) on CPU
            if args.loc_thresh is not None:   # RECALL mode: low prob threshold captures the uncertain tail
                panc = torch.softmax(loc_logits, dim=1)[0, 1].numpy() >= args.loc_thresh
            else:                             # argmax (backward compatible)
                panc = loc_logits.argmax(1)[0].numpy() == 1
            panc = keep_largest_component(panc)
            if args.loc_dilate > 0:
                panc = _dilate(panc, args.loc_dilate)
            loc_failed = not panc.any()
        elif args.roi_from == "gt-panc":
            panc, loc_failed = (label == 1), False
        else:  # gt-union
            panc, loc_failed = (label > 0), False

        box = bbox_from_mask(panc, args.margin_vox)
        if box is None:  # localizer found nothing -> fall back to the whole volume (honest penalty, not a skip)
            box = [(0, s) for s in label.shape]
        box_dims = [hi - lo for lo, hi in box]
        oversize = any(d > args.roi for d in box_dims)  # box bigger than the cube -> ResizeWithPadOrCrop center-crops it
        return box, box_dims, oversize, loc_failed

    @torch.no_grad()
    def run_case(rec):
        """Full cascade for one case. Returns dict with pred cube, gt cube, spacing, coverage."""
        d = pre({k: rec[k] for k in ("image", "pancreas", "lesion") if k in rec})
        image = d["image"].as_tensor().float()          # (1,H,W,D) on CPU
        label = d["label"].as_tensor().long()[0].numpy()  # (H,W,D) GT {0,1,2}

        box, box_dims, oversize, loc_failed = predict_pancreas_box(image, label)
        cov_panc = coverage(label == 1, box)
        cov_les = coverage(label == 2, box)

        sl = tuple(slice(lo, hi) for lo, hi in box)
        img_cube = resizer(image[:, sl[0], sl[1], sl[2]])          # (1,roi,roi,roi)
        gt_cube = resizer(torch.from_numpy(label[None, sl[0], sl[1], sl[2]]))[0].numpy()

        seg_logits = sw(segmenter, img_cube.unsqueeze(0), args.roi, device, inf)  # (1,3,roi,roi,roi)
        probs = torch.softmax(seg_logits, dim=1)[0].numpy()
        pred = probs.argmax(0)
        return dict(pred=pred, probs=probs, gt=gt_cube, cov_panc=cov_panc, cov_les=cov_les,
                    loc_failed=loc_failed, box_dims=box_dims, oversize=oversize)

    def face_clearance_mm(true_mask, box):
        """Signed clearance (mm) on each of the 6 box faces vs the TRUE mask's extent.
        Positive = the box wall sits OUTSIDE the true organ (safe margin); negative = the box
        wall cuts INTO the true organ (a clip). Returns the 6 values, or None if the mask is empty."""
        tb = bbox_from_mask(true_mask, 0)
        if tb is None:
            return None
        out = []
        for a in range(3):
            out.append((tb[a][0] - box[a][0]) * args.spacing)   # low face: box_lo before true_lo -> positive
            out.append((box[a][1] - tb[a][1]) * args.spacing)   # high face: box_hi after true_hi -> positive
        return out

    # ---- localizer diagnostic: WHY does a box miss? (predicted vs GT pancreas geometry) ----
    if args.diag_localizer:
        from skimage import measure
        cids = [c.strip() for c in args.diag_localizer.split(",") if c.strip()]
        print("Body axis = index 2 (superior-inferior) in voxels @1.5mm. 'predZ far from gtZ' = mislocalized blob.\n")
        print(f"{'case':16s} {'gtvox':>7} {'predvox':>8} {'ncomp':>5} {'lccvox':>8} {'gtZ':>11} {'predZ(lcc)':>12} {'boxZ':>11} {'cont':>5} {'over':>4}")
        for cid in cids:
            recs = build_records(dp["manifest"], [cid])
            if not recs:
                print(f"{cid:16s}  not found"); continue
            d = pre({k: v for k, v in recs[0].items() if k in ("image", "pancreas", "lesion")})
            image = d["image"].as_tensor().float()
            label = d["label"].as_tensor().long()[0].numpy()
            loc_logits = sw(localizer, image.unsqueeze(0), args.loc_roi, device, inf)
            panc_pred = loc_logits.argmax(1)[0].numpy() == 1
            ncomp = int(measure.label(panc_pred).max())
            lcc = keep_largest_component(panc_pred) if panc_pred.any() else panc_pred
            gt = label == 1
            box, _, oversize, _ = predict_pancreas_box(image, label)

            def zr(m):
                z = np.nonzero(m)[2]
                return f"{z.min()}-{z.max()}" if z.size else "none"
            cont = coverage(gt, box)
            print(f"{cid:16s} {int(gt.sum()):7d} {int(panc_pred.sum()):8d} {ncomp:5d} {int(lcc.sum()):8d} "
                  f"{zr(gt):>11} {zr(lcc):>12} {f'{box[2][0]}-{box[2][1]}':>11} {cont:5.2f} {str(oversize):>4}")
        return

    # ---- containment audit: localizer only, large cohort, the trust number ----
    if args.audit_coverage:
        ids = set(load_split_ids(dp["splits_dir"], args.split))
        import pandas as pd
        man = pd.read_csv(dp["manifest"])
        cohort = man[man["case_id"].isin(ids)]["case_id"].tolist()[:args.n_audit]
        print(f"[CONTAINMENT AUDIT]  localizer only, {len(cohort)} cases from '{args.split}', "
              f"roi-from={args.roi_from} loc-thresh={args.loc_thresh} dilate={args.loc_dilate} margin={args.margin_vox}vox\n")
        panc_cont, les_cont, worst_face, panc_fail, les_fail, oversz = [], [], [], [], [], 0
        for cid in cohort:
            d = pre({k: v for k, v in build_records(dp["manifest"], [cid])[0].items() if k in ("image", "pancreas", "lesion")})
            image = d["image"].as_tensor().float()
            label = d["label"].as_tensor().long()[0].numpy()
            box, _, oversize, _ = predict_pancreas_box(image, label)
            oversz += int(oversize)
            pc = coverage(label == 1, box)
            lc = coverage(label == 2, box)
            panc_cont.append(pc)
            if not np.isnan(lc):
                les_cont.append(lc)
            fc = face_clearance_mm(label == 1, box)
            if fc is not None:
                mn = min(fc)
                worst_face.append(mn)
                if pc < 0.999:
                    panc_fail.append((cid, pc, mn))
            if (not np.isnan(lc)) and lc < 0.999:
                les_fail.append((cid, lc))

        pc = np.array(panc_cont); wf = np.array(worst_face)
        n = len(pc)
        full = int(np.sum(pc >= 0.999))
        print(f"PANCREAS containment (fraction of GT pancreas inside the box):")
        print(f"  mean {np.nanmean(pc):.4f} | min {np.nanmin(pc):.4f} | fully contained {full}/{n} = {100*full/n:.1f}%")
        print(f"  worst per-face clearance across cases: min {wf.min():.1f}mm | 1st pct {np.percentile(wf,1):.1f}mm | "
              f"median {np.percentile(wf,50):.1f}mm   (negative = the box cut into the pancreas)")
        if les_cont:
            lc = np.array(les_cont); lfull = int(np.sum(lc >= 0.999))
            print(f"TUMOR containment (n={len(lc)} tumor cases): mean {lc.mean():.4f} | min {lc.min():.4f} | "
                  f"fully contained {lfull}/{len(lc)} = {100*lfull/len(lc):.1f}%")
        print(f"OVERSIZE boxes (> cube, would be center-cropped): {oversz}/{n}")
        # statistical bound: rule of three — 0 failures in n -> 95% upper bound on failure rate ~= 3/n
        fails = len(panc_fail)
        if fails == 0:
            print(f"\nGUARANTEE: 0/{n} pancreas-containment failures -> failure rate < {300.0/n:.2f}% (95% CI, rule of three).")
        else:
            need = max(0.0, -wf.min())
            print(f"\n{fails} containment failure(s) — the box cut into the pancreas on these cases:")
            for cid, cov, mn in sorted(panc_fail, key=lambda x: x[2])[:10]:
                print(f"    {cid}: {100*cov:.1f}% contained, worst face {mn:+.1f}mm")
            print(f"  To clear the WORST case, increase the buffer by ~{need:.0f}mm "
                  f"(= {int(np.ceil(need/args.spacing))} vox on top of the current {args.margin_vox}).")
        return

    # ---- sanity: one case, save an overlay, exit ----
    if args.sanity:
        recs = build_records(dp["manifest"], [args.sanity])
        if not recs:
            sys.exit(f"case {args.sanity} not found in manifest")
        r = run_case(recs[0])
        save_sanity_png(r, args.sanity, spacing)
        print(f"[sanity] {args.sanity}: pancreas coverage {r['cov_panc']:.2f}, "
              f"lesion coverage {r['cov_les'] if not np.isnan(r['cov_les']) else float('nan'):.2f}, "
              f"lesion Dice {dice(r['pred'] == 2, r['gt'] == 2):.3f}. Overlay saved to outputs/.")
        return

    # ---- cohort ----
    ids = set(load_split_ids(dp["splits_dir"], args.split))
    import pandas as pd
    man = pd.read_csv(dp["manifest"])
    vdf = man[man["case_id"].isin(ids)]
    pos = vdf[vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_pos]
    neg = vdf[~vdf["has_lesion"].astype(bool)]["case_id"].tolist()[:args.n_neg]
    print(f"scoring {len(pos)} tumor-positive + {len(neg)} tumor-free {args.split} cases "
          f"(two sliding-window stages each, takes a while)...\n")

    # tumor-positive: Dice + coverage
    p_d, l_raw, l_pp, cov_p, cov_l, fails, oversz = [], [], [], [], [], 0, 0
    clip_report = []  # (cid, cov_les, box_dims, oversize) for cases that clip the tumor
    sweep_pos = {t: [] for t in thresholds}
    for cid in pos:
        r = run_case(build_records(dp["manifest"], [cid])[0])
        pred, gt, probs = r["pred"], r["gt"], r["probs"]
        p_d.append(dice(pred == 1, gt == 1))
        l_raw.append(dice(pred == 2, gt == 2))
        l_pp.append(dice(postprocess(pred, spacing, lesion_min_mm3=min_mm3,
                                     lesion_within_pancreas_mm=within) == 2, gt == 2))
        cov_p.append(r["cov_panc"]); cov_l.append(r["cov_les"]); fails += int(r["loc_failed"])
        oversz += int(r["oversize"])
        if (not np.isnan(r["cov_les"])) and r["cov_les"] < 0.90:
            clip_report.append((cid, r["cov_les"], r["box_dims"], r["oversize"]))
        for t in thresholds:
            lesion = probs[2] >= t
            out = np.where(probs[1] >= probs[0], 1, 0).astype(np.int16); out[lesion] = 2
            sweep_pos[t].append(dice(out == 2, gt == 2))

    n_excl = int(np.isnan(l_raw).sum())
    print(f"[TUMOR-POSITIVE cases, n={len(pos)}]"
          + (f"  ({n_excl} excluded: lesion empty after preprocessing)" if n_excl else ""))
    print(f"  pancreas Dice         : {np.nanmean(p_d):.3f}")
    print(f"  lesion Dice (raw)     : {np.nanmean(l_raw):.3f}")
    print(f"  lesion Dice (cleaned) : {np.nanmean(l_pp):.3f}")
    if args.roi_from == "pred":
        miss = len(clip_report)
        print(f"  [localizer] pancreas coverage {np.nanmean(cov_p):.3f} | tumor coverage {np.nanmean(cov_l):.3f} | "
              f"{miss} case(s) clip >10% of tumor | {fails} full miss(es) | {oversz}/{len(pos)} box > cube (would center-crop)")
        for cid, cl, dims, ov in sorted(clip_report, key=lambda x: x[1]):
            why = "OVERSIZE box>cube (need coarser spacing, NOT more buffer)" if ov else "small box (localizer missed tail -> lower threshold / more buffer)"
            print(f"      {cid}: tumor coverage {cl:.2f}, box {dims} vox -> {why}")

    # tumor-free: specificity
    n = len(neg)
    if neg:
        clean_raw = clean_pp = 0
        sweep_neg = {t: 0 for t in thresholds}
        for cid in neg:
            r = run_case(build_records(dp["manifest"], [cid])[0])
            pred, probs = r["pred"], r["probs"]
            if int((pred == 2).sum()) * vox_mm3 < min_mm3:
                clean_raw += 1
            if int((postprocess(pred, spacing, lesion_min_mm3=min_mm3,
                                lesion_within_pancreas_mm=within) == 2).sum()) * vox_mm3 < min_mm3:
                clean_pp += 1
            for t in thresholds:
                lesion = probs[2] >= t
                if int(lesion.sum()) * vox_mm3 < min_mm3:
                    sweep_neg[t] += 1
        print(f"\n[MASK-NEGATIVE cases, n={n}]  (specificity@{min_mm3:.0f}mm3 = predicted lesion below threshold)")
        print(f"  specificity (raw)     : {clean_raw}/{n} = {100*clean_raw/n:.0f}%")
        print(f"  specificity (cleaned) : {clean_pp}/{n} = {100*clean_pp/n:.0f}%")

    if thresholds:
        print(f"\n[LESION THRESHOLD SWEEP]  higher threshold = fewer lesion calls = higher specificity")
        print(f"  {'thresh':>7} | {'lesion Dice (pos)':>18} | {'specificity (neg)':>18}")
        print("  " + "-" * 52)
        for t in thresholds:
            ld = np.nanmean(sweep_pos[t]) if sweep_pos[t] else float("nan")
            sp = f"{sweep_neg[t]}/{n} = {100*sweep_neg[t]/n:.0f}%" if neg else "n/a"
            print(f"  {t:>7.2f} | {ld:>18.3f} | {sp:>18}")

    print(f"\nDone (roi-from={args.roi_from}). Compare gt-union (harness ~oracle) -> gt-panc (leak) -> pred (autonomous).")


def save_sanity_png(r, cid, spacing):
    """Save a mid-tumor-slice overlay: image + GT (green pancreas / red lesion) vs prediction."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from src.utils import paths as P  # noqa

    gt, pred = r["gt"], r["pred"]
    # pick the slice with the most GT lesion, else the most GT pancreas
    axis_sum = (gt == 2).sum(axis=(0, 1)) if (gt == 2).any() else (gt == 1).sum(axis=(0, 1))
    z = int(np.argmax(axis_sum))
    out = Path("outputs") / f"cascade_sanity_{cid}_z{z}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(9, 5))
    for a, lab, title in ((ax[0], gt, "ground truth"), (ax[1], pred, "cascade prediction")):
        a.imshow(np.rot90(lab[:, :, z] > -1), cmap="gray")  # background frame
        a.imshow(np.rot90(np.ma.masked_where(lab[:, :, z] != 1, lab[:, :, z])), cmap="summer", alpha=0.6)
        a.imshow(np.rot90(np.ma.masked_where(lab[:, :, z] != 2, lab[:, :, z])), cmap="autumn", alpha=0.9)
        a.set_title(title); a.axis("off")
    fig.suptitle(f"{cid}  (slice {z})  green=pancreas red=lesion")
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig)


if __name__ == "__main__":
    main()
