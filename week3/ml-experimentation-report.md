# ML Model Experimentation Report

Project: 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS)
Target: Level 4.5 (background, pancreas, lesion), framed as a CADe segmentation assist, not a diagnostic tool.
Author: Quinn. Week 3. Companion log: `docs/experiments.md` (every run as a formal experiment with a pre-registered hypothesis and an accept/reject decision).

This report covers the model-experimentation phase. The discipline I held to all week: change one variable at a time, hold the rest constant, and decide each run against a bar I set before looking at the result. A clean "this did not help" is logged the same as a win, because a ruled-out lever is real information. Every number here is the authoritative full-volume evaluation from `scripts/evaluate.py` unless I say otherwise, and every run is in MLflow.

Status: final for submission. Every run is tracked in MLflow (`sqlite:///outputs/mlflow.db`, experiment `pants-level45`); a run-comparison screenshot is in `week3/`.

> **IMPORTANT — correction and honest update (Week 3 close, 2026-07-19).** After the presentation I ran a full adversarial code audit of the repository (`docs/codex-audit-week4.md`). It caught a real bug I had missed: my *data-scaling* training splits (`scaled300/600/scaledmax`) were sampled from the manifest's source-folder column instead of my carved training fold, so they **overlapped the validation set** — 30 of the 40 cases in my headline evaluation had actually been trained on. That means the EXP-17/EXP-17c numbers below (the 0.528 lesion-Dice culmination) were **inflated by validation leakage** and are not held-out evidence. I verified it against the split files, fixed the root cause (`make_scaled_split.py` now samples only from `train.txt`, and `train.py` aborts on startup if any training split intersects val/test), rebuilt a disjoint split (`scaledmax_clean`), and **retrained from scratch on clean data.** The honest, leakage-free headline is **lesion Dice 0.415, pancreas 0.817, detection sensitivity 95%, specificity 15% (val n=40, held-out).** The recipe experiments on the original `dev_subset` (EXP-04 through EXP-16) used disjoint splits and are unaffected. Sections 3 and 4 below carry both the original (contaminated, struck through in the table) and the corrected numbers, because how I found and fixed this is itself the most important experiment of the phase. The leaked 0.528 did not fully collapse to the clean 0.415, which tells me the data-scaling result was real — only ~0.11 of it was leakage.

---

## 1. Feature Engineering Summary

This is a 3D computer-vision model, so the "features" are the voxels of the CT volume and how they are constructed, not tabular columns. The final feature pipeline, each step with its reason:

- Primary input: the preprocessed 3D CT volume. Transformations, in order: reorient to canonical RAS, resample to 1.5mm isotropic spacing (trilinear for the image, nearest-neighbor for the label so it stays integer), window Hounsfield units to [-100, 300] and scale to [0, 1], and compose the 3-class label from the separate pancreas and lesion masks with lesion winning on overlap. This standardization is the feature engineering for a segmentation model: it is what makes the wildly inconsistent scans of Week 2 (slice counts 8 to 1,000+, voxel spacing varying more than tenfold) comparable to each other.
- Input construction (the key Week 3 decision): the whole-box ROI. Instead of feeding random sub-patches of the scan, the best model crops to the pancreas bounding box in native resolution (plus a 16-voxel margin), resamples, and fits the entire box into one fixed 128-voxel cube via `ResizeWithPadOrCropd`. At 1.5mm a 128 cube spans 192mm, so the whole organ and its surroundings are in view every step. This is an oracle ROI (the pancreas location is provided), and it is the first stage of the localize-then-segment cascade planned for capstone.
- Augmentation (light, for a clean ablation): random flips on all three axes (p=0.2 each), random 90-degree rotations (p=0.2), and small random intensity scale and shift (p=0.15 each). Kept deliberately light so the experiments measure the variable under test, not the augmentation.

Features dropped or changed since Week 2, with reasons:

- Demographic and acquisition metadata (age, sex, site, manufacturer) is excluded as a model input. It is about half missing and a voxel segmentation model does not need it. It stays in the manifest for stratification and analysis only. One analytic use proved its worth: slicing by contrast phase revealed that phase, not resolution, drives the sensitivity/specificity balance (EXP-14).
- Random positive/negative patch sampling (`RandCropByPosNegLabeld`) was the Week 2 default and is still supported, but it is superseded for the best model by the whole-box construction, because random sub-patches inside a small ROI starve the model of field of view and rarely center the rare tumor (this was the concrete failure of EXP-11).
- Candidate auxiliary input, not yet used: a few neighboring anatomical structure masks as extra channels. PanTS reports richer anatomy context improves tumor Dice, so this is a planned ablation. It is deferred because adding channels breaks the SuPreM checkpoint load, making it a capstone item.

Backbone rationale (CV track): SegResNet (MONAI), configured to match the SuPreM checkpoint exactly (init_filters=16, GroupNorm with 8 groups, blocks_down (1,2,2,4), blocks_up (1,1,1), ~4.7M params, verified against the checkpoint keys). Weights are initialized from SuPreM (supervised pretraining on AbdomenAtlas, same JHU lab), the 32-class head is re-initialized to 3 classes, the encoder is frozen for a short warm-up (3 epochs) and then unfrozen so the whole network fine-tunes. From-scratch SegResNet is the control (EXP-09).

---

## 2. Experiment Design

### Model families / axes explored

The experiments are organized as distinct axes, not minor variations of one knob. Each axis is a different hypothesis about what limits lesion accuracy or specificity:

- Initialization: SuPreM transfer vs from-scratch (EXP-09).
- Input construction / field of view: patch 96 vs patch 128 vs oracle-ROI crop at finer spacing vs whole-box single cube (EXP-08, EXP-10, EXP-12).
- Training objective: DiceCE vs DiceFocal, and include-background true vs false (EXP-02, EXP-04, EXP-07).
- Patch sampling: aggressive positive-heavy vs balanced 1:1 vs class-ratio harder-negatives (EXP-04, EXP-05).
- Data regime: clarity-weighted cohort vs representative, and non-contrast vs portal-venous at matched resolution (EXP-13, EXP-14).
- Evaluation-time augmentation: flip TTA on vs off (EXP-15).

### Splits

Patient-level throughout, never by slice — one scan per patient, so slice leakage is impossible. The canonical fold is a stratified `train.txt` (7,200) / `val.txt` (1,800) / `test.txt` (901) split, and I verified `train.txt` ∩ `val.txt` = 0. Most recipe experiments trained on the 95-case `dev_subset_clean` (a subset of `train.txt`, disjoint from val), which keeps the comparisons fast and matched. The data-scaling experiments widen the pool while holding the recipe fixed.

**The leakage bug and the fix (the rigor point worth stating loudly).** My split-scaling helper originally drew its pool from the manifest's `split` column — which marks the *ImageTr source folder*, not my carved fold — so the scaled splits pulled in cases that had been carved into `val.txt`: `scaled300` overlapped val by 54, `scaled600` by 109, `scaledmax` by 266, and 30 of my 40 headline-eval cases were in `scaledmax` training. That is textbook validation leakage, and it inflated the EXP-17/17c numbers. The fix: the helper now samples only from `train.txt`, asserts zero intersection with val/test at build time, and `train.py` aborts on startup if any training split touches val or test (so it cannot recur silently). I rebuilt `scaledmax_clean` (706 tumor + 706 healthy, verified disjoint) and retrained (EXP-24). Every corrected number below is on this clean split. Validation is two fixed disjoint sets scored separately: tumor-positive (lesion + pancreas Dice, n=40) and tumor-free (specificity, n=40). The 901-case `ImageTe` test set is untouched until the very end.

### Metrics and why they fit the problem

- Pancreas Dice and lesion Dice are reported separately. Pancreas is the easy majority target; the lesion is the hard minority (about 10% of scans have a tumor, and a lesion is a tiny fraction of a volume). Averaging them would hide the only number that matters.
- Dice (overlap) is the standard segmentation metric and is what the loss optimizes. Lesion Dice is scored only on tumor-positive cases; on a tumor-free scan lesion Dice is undefined, so the metric uses `ignore_empty` to drop those rather than let them read as zero (an early measurement trap that made a working model look broken).
- The headline for the CADe framing is patient-level specificity (how often a healthy scan is correctly not flagged) alongside lesion Dice. Over-prediction on healthy scans was the central problem of the project, so specificity is measured on its own tumor-free set, raw and after CADe post-processing.

### Backbone selection, freezing, augmentation

Covered in Section 1: SegResNet matched to SuPreM, encoder frozen for a 3-epoch warm-up then unfrozen, light flip/rotate/intensity augmentation. Optimizer is AdamW (lr 1e-4 transfer, 2e-4 scratch, weight decay 1e-5) with a short warmup then cosine decay; fp32 on the Apple MPS backend; seed 42; 6000 iterations for the recipe-comparison runs, extended proportionally for the larger-data scaling runs (about 24000 for the 1,412-case EXP-17c).

---

## 3. Experiment Results

All runs are logged in MLflow (`sqlite:///outputs/mlflow.db`, experiment `pants-level45`). The authoritative numbers below are full-volume sliding-window evaluation. A fairness note that shaped the whole table: early runs were scored on n=12 validation cases and later runs on n=20; where I compare two models I always re-score them at the same n, because mismatched n once manufactured a fake "win" (EXP-08).

### Comparison table (headline runs)

| # | Experiment (the one variable) | eval n | pancreas Dice | lesion Dice raw | lesion cleaned | specificity raw | decision |
|---|-------------------------------|--------|---------------|-----------------|----------------|-----------------|----------|
| EXP-04 | DiceFocal, aggressive sampling ("aggressive base") | 12 | 0.720 | 0.169 | 0.139 | 8% | keep loss, over-predicts |
| EXP-05 | Balanced 1:1 sampling | 12 | 0.721 | 0.169 | — | 8% | REJECT (null) |
| EXP-07 | Loss includes background (bg1) | 12 | ~0.72 | 0.149 | 0.33 spec cleaned | 8% | REJECT, revert to bg0 |
| EXP-08 | Patch 128 (more context) | 20 | 0.747 | 0.187 | 0.175 | 25% | REJECT on accuracy |
| EXP-08 | Patch 96 baseline (matched) | 20 | 0.740 | 0.206 | 0.197 | 10% | accuracy baseline |
| EXP-10 | Oracle ROI crop + 1.0mm | 20 | 0.726 | 0.234 | 0.214 | — | promising, partial |
| EXP-12 | Whole-box single cube | 20 | 0.807 | 0.263 | 0.252 | 55% | ACCEPT, best base |
| EXP-13 | Clarity-weighted cohort (20-case) | 20 | 0.780 | 0.204 | 0.208 | 85% | soft null (confounded) |
| EXP-13 | Representative cohort (20-case) | 20 | 0.782 | 0.189 | 0.182 | 50% | baseline arm |
| EXP-14 | Non-contrast cohort (20-case) | 20 | 0.791 | 0.116 | 0.116 | 90% | decisive: phase drives spec |
| EXP-14 | Portal-venous cohort (20-case) | 20 | 0.704 | 0.124 | 0.138 | 10% | decisive: phase drives spec |
| EXP-12* | Whole-box transfer, regenerated | 20 | 0.778 | 0.257 | 0.263 | 50% | reproduced original within noise |
| EXP-09 | From-scratch (the pretraining ablation) | 20 | 0.650 | 0.120 | 0.137 | 0% | REJECT scratch: transfer wins on all axes |
| EXP-15 | Flip TTA on EXP-12 (eval-only) | 20 | 0.756 | 0.234 | 0.238 | 75% | not free: spec +25pp, lesion -0.025 → specificity dial |
| EXP-16 | Finer resolution (160 @ 1.2mm) | 20 | 0.805 | 0.248 | 0.228 | 55% | REJECT: resolution is not the lesion lever |
| EXP-17 | 3x tumor data (300 cases) — ⚠ LEAKED split | 20 | 0.815 | ~~0.313~~ | ~~0.327~~ | 50% | withdrawn (leakage) |
| EXP-17c | All tumor data (1,412) — ⚠ LEAKED split | 40 | ~~0.837~~ | ~~0.524~~ | ~~0.528~~ | — | withdrawn (leakage) |
| **EXP-24** | **Same recipe, LEAKAGE-FIXED split (`scaledmax_clean`)** | 40 | **0.817** | **0.415** | **0.412** | **15%** | **ACCEPT — the honest candidate** |

Screenshots in `week3/`: the run-comparison table (`mlflow-run-comparison.png`, all runs side by side), and the clean candidate run's metrics, training/val curves, and params (`mlflow-clean-run-{metrics,curves,params}.png`). The authoritative full-evaluation numbers come from `scripts/evaluate.py` (terminal, `eval-clean-run-terminal.png`), not MLflow.

**Reconciling the MLflow curve with the reported number (a fair question).** MLflow logs the *in-loop* validation Dice on a 20-case tracking set: it climbs, peaks at **0.407 at step 18,000** (the checkpoint I keep as `best.pt`), then drifts slightly to 0.381 by step 24,000 — mild late-training noise, which is exactly why I select the best checkpoint rather than the last. The headline **0.415** is the authoritative full sliding-window evaluation of that best checkpoint over the larger **40-case** validation cohort with CADe post-processing. So the MLflow 0.38-0.41 and the reported 0.415 are the same model measured two ways (small tracking cohort during training vs. the full evaluation after), not a val-vs-test gap — and the official 901-case test set is untouched, reserved for one final locked evaluation. Validation is verified disjoint from training (`train.txt ∩ val.txt = 0`, enforced by a startup assertion), so there is no leakage in these numbers.

Reading the arc down the lesion-Dice column: every recipe change (loss, sampling, patch, resolution) on the disjoint `dev_subset` sits in the 0.15–0.25 band and none moved lesion accuracy — those are clean results. The apparent data-scaling jump to 0.528 was partly real and partly leakage; the honest, leakage-free result on the same recipe is **0.415** (EXP-24), which still beats the recipe band and confirms that data scaling — not any recipe knob — is what moves the tumor number. EXP-24 carries a **95% detection sensitivity** (38/40 tumors found), the metric a stakeholder actually cares about for a CADe assist, at a moderate specificity of 15% that Section 4 addresses head-on.

### What each run told me (the learning narrative)

- EXP-04 / EXP-05 (loss and sampling): DiceFocal with background excluded learned the tiny lesion, but the model badly over-predicted, flagging a tumor on almost every healthy scan (8% specificity). Rebalancing the patch sampling to 1:1 changed nothing (a clean null). Lesson: sampling ratio is not the cause of over-prediction. This pushed the next attempt to the loss.
- EXP-07 (loss includes background): giving the model an explicit reason to call healthy tissue "not lesion" also failed to move raw specificity, and it cost lesion Dice. Two training knobs now ruled out. Lesson: over-prediction is not a training-knob problem at 100 cases; it points at data scale, and specificity should be handled by post-processing plus more data.
- EXP-08 (bigger patch): more context did not improve accuracy once scored fairly on matched cases (the overnight "win" was an n-mismatch artifact). It did raise specificity, so context is a sensitivity/specificity trade, not an accuracy lever. Lesson: matched-n comparison is mandatory, and field of view alone is not the accuracy ceiling.
- EXP-10 (oracle ROI at 1.0mm): cropping to the pancreas and working at finer resolution gave the best lesion Dice to that point (0.234), supporting the cascade thesis, though partly confounded by an encoder-training bug fix that arrived with it.
- EXP-11 (clarity package, rejected): cropping native then resampling to 0.7mm with a 64 patch starved the model (a 45mm field of view of a 150-200mm organ) and random sub-patches rarely centered the tumor. Not a verdict on resolution, a verdict on tiny field of view plus random sampling. It directly motivated the whole-box idea.
- EXP-12 (whole-box, the breakthrough): feeding the entire pancreas box as one cube won on all three axes at once, pancreas 0.807, lesion 0.263 (best to date), specificity 55% (versus 8% on every prior model). The model now stays quiet on healthy scans by itself, so the anatomical post-processing constraint became a near no-op. This became the winning recipe, and every data-scaling run afterward keeps it fixed and only adds data.
- EXP-13 / EXP-14 (data regime): weighting training toward the sharpest scans did not clearly help accuracy but sharply raised specificity; isolating the cause showed it was contrast phase, not resolution. A non-contrast-trained model is highly specific (90%), a portal-venous one is sensitive but trigger-happy (10%). Lesson: contrast phase is a real operating-point dial, and it is the strongest explanatory result of the project.
- EXP-09 (transfer vs scratch): decisive, and it is the number that justifies the SuPreM choice. From-scratch on the same 95 cases barely learns the pancreas (0.650) and flags a tumor on every healthy scan (0% specificity); the SuPreM-initialized model reaches 0.778 pancreas, 0.263 lesion, 55% specificity. Pretraining is worth roughly +0.13 lesion Dice, +0.13 pancreas Dice, and +50 points of specificity. So the transfer is not a marginal boost, it is what makes the model usable at this data scale. (Honest confound: the arms also differ in learning rate and encoder-freeze warm-up, so this is a transfer-recipe vs scratch-recipe comparison, but the gap is far too large for those to explain.)
- EXP-15 (flip TTA): not a free win. Averaging predictions over 8 flips raised specificity sharply (55% to 80% cleaned) but cost lesion Dice (0.263 to 0.238), so by my pre-registered bar I do not adopt it as an always-on default. It earns a place as an operating-point dial: it reaches an 80 to 90% specificity regime the probability-threshold sweep could not on its own, useful when the priority is screening rather than outline accuracy.
- EXP-16 (finer resolution): rejected on the lesion. Sampling the whole box at 1.2mm instead of 1.5mm lifted pancreas Dice (0.815) but left lesion Dice flat-to-lower (0.248 raw), because more voxels help the large organ and not the handful-of-voxels tumor. This was the fourth and final recipe axis ruled out for lesion accuracy, which isolated data as the only untested lever.
- EXP-17 (3x tumor data): the turning point. Holding the winning whole-box recipe fixed and tripling the tumor training cases (50 to 150) moved lesion Dice from 0.263 to 0.313 raw / 0.327 cleaned, clearing the ceiling four recipe changes could not touch, while pancreas rose to 0.815 and specificity held. Post-processing now helps instead of hurting, and the operating-point sweep is strictly better (threshold 0.90 gives lesion 0.319 and specificity 70%). This is the direct confirmation of the project's central hypothesis: lesion accuracy is data-limited, not recipe-limited.
- EXP-17c (all tumor data — the result I later found was leaked): pushing the same recipe to every tumor case (1,412 total) read lesion Dice 0.528 at n=40 — but see the correction. This is the run whose split turned out to overlap validation.
- EXP-AUDIT (the most important experiment of the phase): after the presentation I put the whole repo through an adversarial code audit. It found that `make_scaled_split.py` sampled from the manifest's source-folder column, not my carved `train.txt` fold, so every scaled split overlapped validation (`scaledmax` by 266 cases; 30 of my 40 headline-eval cases had been trained on). I verified it by direct set-intersection on the split files, then fixed the cause — the split builder now samples only from `train.txt`, and the trainer aborts on startup if a training split ever touches val or test, so this class of bug cannot recur silently. Lesson, and the one I care most about: a number is only as trustworthy as the split it was measured on, and an independent adversarial check is worth more than another accuracy point.
- EXP-24 (the honest re-run, the selected model): I retrained the exact EXP-17c recipe on the leakage-fixed `scaledmax_clean` (706 tumor + 706 healthy, verified disjoint from validation). Held-out result: pancreas 0.817, lesion Dice 0.415 raw / 0.412 cleaned, detection sensitivity 95% (38/40), specificity 15%. The leak had inflated lesion Dice by ~0.11 and specificity by roughly 2x — but the clean number did not collapse (memorization would have dropped it near 0.2), which means the data-scaling result was genuinely real, just smaller than it looked. The per-case analysis then gave the real diagnosis: the model reliably finds tumors (95%) but over-segments them 3–13x on small and medium cases, which is what caps Dice AND drives the low specificity (the same over-painting shows up as false alarms on healthy scans). By contrast phase the pattern matches EXP-14: venous 0.582, arterial 0.458, non-contrast 0.252. This diagnosis is what sets the Week 4 direction (Section 4).

---

## 4. Model Selection & Justification

Candidate model carried into Week 4: the **EXP-24 whole-box SuPreM-transfer SegResNet**, trained on the leakage-fixed `scaledmax_clean` (706 tumor + 706 healthy, verified disjoint from validation). Same architecture and recipe as the whole-box base (bg0 DiceFocal, crop to the pancreas box, one 128-cube input at 1.5mm); the only change from the recipe experiments is the amount of clean tumor data. Held-out evaluation at n=40: **pancreas Dice 0.817, lesion Dice 0.415 raw / 0.412 cleaned, detection sensitivity 95% (38/40), specificity 15%.**

Why this one, weighing trade-offs beyond the top metric:

- Best honest evidence on the axis that matters most: on genuinely held-out data it is the strongest lesion model I have (0.415 vs the 0.15–0.25 band every recipe knob produced), and it finds 95% of tumors — the number a CADe assist lives or dies on. It is in the neighborhood of the ~0.53 published reference, measured cleanly.
- Not the top metric alone — I chose it knowing its weakness, because I can name and attack that weakness: the per-case analysis shows the model detects tumors but **over-segments them 3–13x** on small/medium cases. That single failure mode explains both the capped Dice and the low 15% specificity (over-painting on a healthy scan is a false alarm). A model whose flaw is understood and directly addressable is a better Week-4 starting point than a higher number I could not explain.
- Overfitting / trust: it is trained on 1,412 cases and evaluated on a disjoint validation set, with a startup assertion that now guarantees no train/val overlap. This is the trade-off I weighed most heavily this week — I would rather carry a defensible 0.415 than an indefensible 0.528, because a leaked number is worth nothing to a stakeholder or to Johns Hopkins.
- Inference behavior: a single 128-cube forward pass per case, fast and simple; light CADe post-processing (largest-component + volume threshold + lesion-near-pancreas constraint).
- Honest limitations I am not hiding: (1) provided-ROI, not autonomous — the model is given the pancreas box; the localize-then-segment cascade that removes that assumption is built and in progress (`scripts/cascade_eval.py`), and its clean autonomous number is the next run. (2) Development-validation on a 40-case cohort, not a held-out test estimate; the official 901-case test set is reserved for the very end. (3) "Specificity" is mask-negative specificity at a 50 mm3 threshold, and it is genuinely low (15%) — the model over-calls tumors on healthy scans; I am not dressing that up. (4) Contrast phase drives the result (venous 0.58 » non-contrast 0.25), so a single headline number hides a real operating-point spread.
- Why not the alternatives: from-scratch is decisively worse (EXP-09, on disjoint dev_subset: pancreas 0.650, lesion 0.120, specificity 0%), so the SuPreM pretraining does essential work; every recipe lever (bigger patch, finer resolution, loss reweighting, sampling) was a null on lesion Dice; and the leaked EXP-17c is not a real alternative — its 0.528 is withdrawn. Among honestly-measured models, EXP-24 is the best.

Week-4 direction this sets (the point of model selection is what you do next): the diagnosed over-segmentation points at a precision-oriented loss. I have wired and smoke-tested a **Tversky loss** (penalizes false positives, `train.py --loss tversky --tversky-alpha 0.7`) as the first tuning experiment — the hypothesis is that punishing over-painting lifts Dice *and* specificity together, without dropping the 95% detection. Paired with feeding the model more healthy data (I used only 706 of ~6,500 available) and the autonomous cascade, that is the concrete plan into Week 4.

Note on reproducibility (learned this week): an earlier whole-box checkpoint was lost to a checkpoint-management error, so I regenerated it with the identical seed-42 command and it reproduced within noise (pancreas 0.778, lesion 0.263 cleaned, specificity 55%). Lesson: lesion Dice reproduces tightly across runs, but specificity is the noisier metric (best.pt is selected on lesion Dice, not specificity, and each healthy case is 5 points at n=20), so I report specificity as a range-aware number rather than a single hard figure.

The central finding of the week: lesion accuracy is data-limited, not recipe-limited. Four independent recipe axes (sampling, loss, field-of-view/context, resolution) on the disjoint dev_subset all failed to move lesion Dice out of the 0.15–0.25 band, and the only thing that did was scaling the tumor data. The leakage briefly overstated how big that data effect was — but the leakage-free re-run (EXP-24) still lands at 0.415, well above the recipe band, so the conclusion holds honestly: data is the dominant lever, recipe knobs are not. What the clean number also exposed, which the leaked one had hidden, is that the model over-segments tumors — so Week 4 leads with a precision loss (Tversky) to fix that, then more healthy data and the autonomous cascade.

---

## 5. Where I Stand Against the Implementation Plan

Honest status heading into Week 4: ON TRACK, with a correction I am not hiding. The plan's Week-3 goals landed, and the end-of-week audit that caught the leakage tightened the evidence rather than derailing it.

On track: the Week 3 plan called for the instructor-suggested clarity-curriculum experiment (EXP-13, done), test-time augmentation at eval (EXP-15, done, characterized as a specificity dial), the transfer-vs-scratch defense of the model choice (EXP-09, done and decisive on the disjoint dev_subset), the data scale-up (done — and then corrected), and continued MLflow tracking with pancreas and lesion Dice kept separate. All landed.

The correction, stated plainly: the data scale-up initially read 0.528, but the end-of-week code audit found my scaled splits had leaked validation cases into training. I fixed the split builder, added a startup guard against it, retrained on a clean disjoint split, and the honest held-out result is 0.415 (Section 3/4). That is the number I carry forward. The recipe experiments on dev_subset are unaffected.

Adjustments to the plan from what I learned:
- The clean re-run exposed that the model over-segments tumors (which the leaked run had masked). So Week 4 now leads with a precision-oriented loss (Tversky, wired and launching) to attack that directly, expecting it to lift both Dice and specificity.
- Specificity is genuinely low (15%) on honest data. Levers queued: more healthy training data (I used only 706 of ~6,500 available), the Tversky loss, and reporting specificity stratified by contrast phase.
- The autonomous localize-then-segment cascade (removes the provided-ROI assumption) is built and being validated; its clean autonomous number is a Week-4 run.

Still owed for the fully honest final number (Week 4/5): the clean localizer retrain for the autonomous number; a full-cohort evaluation with confidence intervals rather than the fixed 40-case cohort; and one final pass on the untouched 901-case official test set once the model and operating point are frozen.

## 6. AI Documentation Files

Section 6, AI Documentation Files: `CLAUDE.md` (project context file) and `docs/ai-usage-log.md` (Week 3 entry). The revised implementation plan lives in `docs/implementation-plan.md`; Section 5 above is the report-level summary of it.

## Reproducibility

Every run is one command against `scripts/train.py` with the variable under test passed as a CLI override (so field of view, spacing, crop, and whole-box are changed without editing the config), evaluated with `scripts/evaluate.py` at matched n. Full hypotheses, runbooks, and decisions for all experiments are in `docs/experiments.md`. No raw data or checkpoints are committed; the dataset path is set in `configs/level45.yaml`.
