# Metrics & Training Audit (2026-07-17)

Two independent audits of how the project computes its reported numbers, prompted by a
concern that healthy scans might be biasing the lesion Dice. One by the working AI
(Claude), one by Codex from a written prompt. Both read `metrics.py`, `evaluate.py`,
`analyze_cases.py`, `sliding_window.py`, `transforms.py`, `dataset.py`, `train.py`,
`losses.py`, `configs/level45.yaml`.

## Overall verdict

The core Dice and specificity arithmetic is correct. No train/validation case overlap
(train.txt 7,200 IDs, val.txt 1,800 IDs, intersection zero). No class-order corruption.
Lesion Dice is a per-case mean over mask-positive cases; specificity is over mask-negative
cases. The original concern (healthy scans diluting or inflating lesion Dice) is ruled out:
`ignore_empty=True` excludes empty-GT cases as NaN (they are never scored 1.0 or 0.0), and
`evaluate.py` averages lesion Dice over tumor-positive cases only.

These are NOT unbiased autonomous full-volume numbers. They are mean per-case Dice on
mask-positive cases and mask-negative specificity at a 50 mm3 threshold, computed inside a
GROUND-TRUTH-defined ROI. Reported honestly with that scope, they are correct.

## Findings

### Moderate

1. **ROI is pancreas UNION lesion, not pancreas alone.** `_foreground_label = label>0`
   (transforms.py:34) and both crops use the composed label as source (transforms.py:110,123).
   A lesion protruding past the pancreas mask enlarges/shifts the crop, leaking lesion extent
   into the field of view. Biases lesion Dice UPWARD. Fix: build the crop from the pancreas
   mask alone. STATUS: fixed behind `roi_source` flag (default union preserved); EXP-19 will
   quantify the leak.

2. **Eval preprocessing is not restored from the checkpoint** — it depends on the user
   repeating CLI flags (evaluate.py:73,87). A whole-box checkpoint could silently be evaluated
   with the wrong recipe if flags are omitted. Not a confirmed error in the quoted runs (the
   documented commands match), but a reproducibility risk. Fix: embed the resolved config in
   each checkpoint and assert on load. STATUS: queued (extends checkpoint-hygiene work).

3. **Best checkpoint and headline metrics use the same val set** (train.py selects best.pt by
   val lesion Dice; evaluate.py defaults to the same `val` split). Ordinary validation use, but
   optimistic — not a held-out test estimate, especially after many experiments. Fix: report
   these as development-validation; do one final pass on the untouched 901-case official test
   set. STATUS: framing corrected; final test pass planned for Week 4/5.

4. **Evaluated cohort is the first N manifest-ordered cases** (`[:n_pos]`, evaluate.py:129;
   analyze_cases.py:76), not random/complete, no confidence interval. At n=20 one negative =
   5 specificity points. Fix: evaluate all eligible val cases (or a seeded versioned subset),
   report bootstrap CIs and exact IDs. STATUS: morning evals moved to larger n; full-cohort +
   CI planned for final reporting.

### Minor

5. **Empty-GT handling differed between the two metric paths.** MONAI `ignore_empty=True`
   (metrics.py:16) excludes empty GT; the hand-rolled `dice()` returned 1.0 when both empty
   (evaluate.py, analyze_cases.py), which could inflate a positive-cohort mean if a tiny lesion
   vanished after 1.5mm resampling. Both audits verified all 20 current pos cases retain lesion
   voxels (smallest ~76 voxels), so NOT triggering now. STATUS: FIXED — `dice()` now returns
   NaN on empty GT and aggregates with `nanmean`.

6. **"Specificity" is mask-negative specificity.** 44 metadata-positive/mask-empty cases exist
   (9 in val, none in the first-20 negatives). Not a leak into the segmentation definition, but
   the metric is against masks, not clinical tumor status. STATUS: relabeled in eval output.

7. **`analyze_cases.py` averaged rounded per-case Dice** (~0.0005 error). STATUS: FIXED — full
   precision retained, rounded only at print.

8. **"Raw specificity" already applies the 50 mm3 detection threshold** (evaluate.py:166) — it
   is specificity@50mm3, not zero-voxel. STATUS: relabeled in eval output.

### No critical findings.

## Checks that passed (verified, not assumed)

- Positive/negative cohorts are disjoint, built from mask-derived `has_lesion`; only pos enters
  lesion Dice, only neg enters specificity.
- Class order pancreas=1 / lesion=2 preserved through AsDiscrete + DiceMetric(include_background=False)
  and evaluate.py's pred==1/pred==2. Pancreas Dice excludes lesion voxels (lesion paints last) —
  internally consistent.
- Per-case averaging (not per-voxel), so large tumors don't dominate.
- Sliding-window stitching correct; whole-box 128 input with 128 window = one complete cube.
- Argmax raw Dice and the threshold sweep are separate operating points, not mixed.
- Raw vs cleaned accumulated independently; cleaned not silently substituted.
- No train/val ID overlap; each case treated as its own patient (project assumption).
- With validation enabled, best.pt uses full-volume validation lesion Dice, not the noisy
  per-step training-patch Dice.

## Priority corrections (from the audit)

1. Build the ROI from pancreas alone, not pancreas+lesion.  [coded; EXP-19 to quantify]
2. Embed + enforce the resolved preprocessing config in checkpoints.  [queued]
3. Evaluate a fixed complete held-out cohort, not the first 20.  [planned]
4. Reserve an untouched final test cohort after model/operating-point selection.  [official 901-case test held]
5. Exclude transformed-positive cases whose lesion becomes empty.  [FIXED: NaN + nanmean]
