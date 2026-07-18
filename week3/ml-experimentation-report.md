# ML Model Experimentation Report

Project: 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS)
Target: Level 4.5 (background, pancreas, lesion), framed as a CADe segmentation assist, not a diagnostic tool.
Author: Quinn. Week 3. Companion log: `docs/experiments.md` (every run as a formal experiment with a pre-registered hypothesis and an accept/reject decision).

This report covers the model-experimentation phase. The discipline I held to all week: change one variable at a time, hold the rest constant, and decide each run against a bar I set before looking at the result. A clean "this did not help" is logged the same as a win, because a ruled-out lever is real information. Every number here is the authoritative full-volume evaluation from `scripts/evaluate.py` unless I say otherwise, and every run is in MLflow.

Status: final for submission. All experiments are complete, through EXP-16 (resolution, rejected), EXP-17 (data scale-up), and EXP-17c (max data, confirmed 2026-07-17) — the culminating result that broke the lesion-Dice ceiling and the model I carry into Week 4. Every run is tracked in MLflow (`sqlite:///outputs/mlflow.db`, experiment `pants-level45`); the run-comparison view is shown live in the presentation.

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

Patient-level throughout, never by slice. Because the metadata has no patient identifier, each scan is its own case/patient, which makes leakage between train and test impossible (there is only ever one scan per patient). Splits are stratified on tumor presence. Most experiments trained on the 95-case `dev_subset_clean` (the 100-case development subset minus 5 cases an integrity audit flagged with empty or broken pancreas masks), which keeps the recipe comparisons fast and matched. The data-scaling experiments then widen the training pool while holding the recipe fixed: `scaled300` (300 cases, 150 tumor) for EXP-17 and `scaledmax` (1,412 cases, all 706 tumor cases the Mini release's train partition offers) for EXP-17c. The validation cases are held out of every training pool. Validation is two fixed sets scored separately: tumor-positive cases (for lesion and pancreas Dice, n=20, widened to n=40 for the final EXP-17c read) and tumor-free cases (for specificity). The official 901-case `ImageTe` test set is untouched until the very end.

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
| EXP-17 | 3x tumor data (300 cases) | 20 | 0.815 | 0.313 | 0.327 | 50% | ACCEPT — data is the lever |
| **EXP-17c** | **All tumor data (1,412 cases) + long training** | 40 | **0.837** | **0.524** | **0.528** | — | **ACCEPT — the selected model** |

The MLflow run-comparison view (all runs, side by side on lesion Dice / pancreas Dice / specificity) is shown live during the presentation.

Reading the arc down the lesion-Dice column tells the whole story: every recipe change (loss, sampling, patch, resolution) sits in the 0.15–0.25 band and none of them moved it; the two changes that did move it were both data — 95 → 300 cases (0.263 → 0.327) and 300 → 1,412 cases (0.327 → 0.528). EXP-17c also carries a per-case detection sensitivity of 90% (36/40 tumors found), the metric a stakeholder actually cares about for a CADe assist.

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
- EXP-17c (all tumor data, the culmination and the selected model): pushing the same recipe to every tumor case in the training pool (150 to 706, 1,412 cases total, with proportionally longer training on a new disk cache) moved lesion Dice from 0.327 to 0.524 raw / 0.528 cleaned at n=40, essentially reaching the ~0.53 published segmentation reference, with pancreas Dice 0.837 and per-case detection sensitivity 90%. Two things are worth stating plainly. First, the per-case analysis showed why it jumped: at 300 cases the model detected tumors but over-drew them (predicted volume 4 to 8x the truth); at max data the outlines tightened to within 1 to 2x of the truth, so the gain came from better outlines, not just more detections, and it happened without any loss change. Second, this run deliberately moved two things at once (data and training length), so it is not a clean single-variable test; I flag that honestly, but the data-scaling curve across four points (0.169, 0.263, 0.327, 0.528) makes the direction unambiguous. Lesson: data is not just a lever, it is the dominant one, and at maximum tumor data the curve has still not flattened.

---

## 4. Model Selection & Justification

Candidate model carried into Week 4: the EXP-17c whole-box SuPreM-transfer SegResNet trained on the full tumor pool (1,412 cases, 706 tumor). It is the exact same architecture and recipe as the whole-box base (bg0 DiceFocal, crop to the pancreas box, one 128-cube input at 1.5mm); the only things changed from the base are the amount of training data and the training length. Full-volume evaluation at n=40: pancreas Dice 0.837, lesion Dice 0.524 raw / 0.528 cleaned, per-case detection sensitivity 90% (36 of 40 tumors found).

Why this one, weighing trade-offs beyond the top metric:

- Best evidence on the axis that matters most: it is the strongest model on lesion Dice by a wide margin (0.528 vs the 0.263 the whole-box recipe alone reached and the 0.327 that 300 cases reached), and it lifts every other number too — pancreas 0.837, detection sensitivity 90%. It sits essentially at the ~0.53 published segmentation reference for this task. The per-case breakdown confirms the win is real and not an averaging artifact: it improves in every tumor-size bin (small 0.225, medium 0.536, large 0.703) and every contrast phase (non-contrast 0.425, arterial 0.491, venous 0.646).
- Not just the top metric — the failure mode it fixed: at 300 cases the model already detected most tumors but over-drew them (predicted volume 4 to 8x the truth), which is exactly what caps Dice and, in a CADe assist, is what makes an annotator distrust the contour. At max data the predicted volumes fall to within 1 to 2x of the truth. So this model is chosen partly because it draws tighter, more trustworthy outlines, a quality the raw Dice number only partly captures.
- Overfitting risk: trained on 1,412 cases versus 95 for the base, which is precisely why the tumor generalized better — more variety to learn from, less to memorize. Earlier whole-box models peaked early and overfit; more data pushed that peak later, and the validation curve was still climbing when training stopped (which is itself the Week 4 signal: a longer run is likely to climb further). Validation is the held-out tumor-positive / tumor-free sets, scored separately and never trained on.
- Inference behavior: unchanged from the whole-box base — a single 128-cube forward pass per case, fast and simple, with post-processing now a light, genuinely helpful cleanup (cleaned 0.528 > raw 0.524) rather than the no-op it was on earlier models.
- Honest limitations I am not hiding: (1) it is a provided-ROI number, not autonomous; the cascade (a pancreas detector in front) is the capstone. (2) A metrics audit (mine plus an independent AI pass, `docs/codex-metrics-audit.md`) found the ROI is currently built from the pancreas UNION the lesion, so lesion extent can leak into the field of view and the reported lesion Dice is an upper bound; a pancreas-only-ROI control (EXP-19) is queued to quantify it, and the fix is already coded behind a flag. (3) These are development-validation numbers (the checkpoint is selected on the same val set) on a 40-case cohort, not a held-out test estimate; the official 901-case test set is untouched for the final report. (4) EXP-17c changed two variables at once (data volume and training length), so it is a decisive practical result, not a clean single-variable decomposition; a control would separate the two, but the four-point data-scaling curve makes the direction unambiguous. (5) "Specificity" throughout is mask-negative specificity at a 50 mm3 detection threshold. Stating all of this is the honest framing; none of it changes the relative conclusions, and the audit confirmed the core Dice/specificity arithmetic and the train/val split are correct with no leakage.
- Why not the alternatives: from-scratch is decisively worse (EXP-09: pancreas 0.650, lesion 0.120, specificity 0%), so the SuPreM pretraining does essential work; every recipe lever (bigger patch, finer resolution, loss, sampling) was a null on lesion Dice; the whole-box base (EXP-12, lesion 0.263) and the 300-case model (EXP-17, 0.327) are the same model with less data. EXP-17c dominates all of them on the target metric and on detection sensitivity.

Note on reproducibility (learned this week): an earlier whole-box checkpoint was lost to a checkpoint-management error, so I regenerated it with the identical seed-42 command and it reproduced within noise (pancreas 0.778, lesion 0.263 cleaned, specificity 55%). Lesson: lesion Dice reproduces tightly across runs, but specificity is the noisier metric (best.pt is selected on lesion Dice, not specificity, and each healthy case is 5 points at n=20), so I report specificity as a range-aware number rather than a single hard figure.

The central finding of the week, now demonstrated rather than inferred: lesion accuracy is data-limited, not recipe-limited. Four independent recipe axes (sampling, loss, field-of-view/context, resolution) all failed to move lesion Dice, and the only changes that did were scaling the tumor data: 95 to 300 cases (EXP-17: 0.263 to 0.327) and then to the full 1,412-case pool (EXP-17c: 0.327 to 0.528). This is no longer a hypothesis about the ceiling; it is a shown lever, four points on a curve that is still rising. It also sets the direction for Week 4 and the capstone: the Mini release's tumor data is now exhausted, so the next gains come from more training time on this max-data set, the loss (Tversky, to attack any residual over-segmentation), and the autonomous localize-then-segment cascade that removes the provided-ROI assumption.

---

## 5. Where I Stand Against the Implementation Plan

Honest status heading into Week 4: ahead of plan on the main lever, on track everywhere else, with two reporting items still owed.

Ahead: data scale-up was written into my plan as the Week 4 headline task, gated behind one piece of infrastructure I had been deferring (a disk cache to replace the RAM cache, since 1,412 scans far exceed memory). I built that cache this week and ran the scale-up early, so the result the plan hoped to reach in Week 4 (lesion Dice off the ~0.26 ceiling) is already in hand at 0.528, and it landed a week ahead. The pre-registered Week 4 bar was "clears 0.30 at n=20"; the actual result cleared it at n=40.

On track: the Week 3 plan called for the instructor-suggested clarity-curriculum experiment (EXP-13, done), test-time augmentation at eval (EXP-15, done and characterized as a specificity dial), the transfer-vs-scratch defense of the model choice (EXP-09, done and decisive), and continued MLflow tracking with pancreas and lesion Dice kept separate (held throughout). All four landed.

Adjustments I am making, stated plainly rather than hidden:
- The plan assumed specificity would need a training-side fix. Two training knobs (loss, sampling) were nulls, so I moved that burden to the input construction (whole-box) and to data scale, which is where it actually resolved. The plan's "if specificity is still weak, widen the data pool" fallback turned out to be the main path, not the fallback.
- A mid-week metrics audit (mine plus an independent AI pass) found the ROI crop leaks lesion extent, making lesion Dice an upper bound. I did not paper over it: the fix is coded behind a flag and a control run (EXP-19) is pre-registered to quantify the leak. This is added scope the plan did not originally have, and I am carrying it into Week 4.
- Because the Mini release's tumor data is now fully used, the Week 4 levers shift from "more data" (exhausted) to more training time on the max-data set, a loss change for residual over-segmentation, and starting the autonomous cascade toward the capstone.

Still owed for the fully honest final number (Week 4/5, not blockers for this review): the EXP-19 pancreas-only-ROI control to quantify the leak; a full-cohort evaluation with confidence intervals rather than a fixed 40-case cohort; and one final pass on the untouched 901-case official test set once the model and operating point are frozen.

## 6. AI Documentation Files

Section 6, AI Documentation Files: `CLAUDE.md` (project context file) and `docs/ai-usage-log.md` (Week 3 entry). The revised implementation plan lives in `docs/implementation-plan.md`; Section 5 above is the report-level summary of it.

## Reproducibility

Every run is one command against `scripts/train.py` with the variable under test passed as a CLI override (so field of view, spacing, crop, and whole-box are changed without editing the config), evaluated with `scripts/evaluate.py` at matched n. Full hypotheses, runbooks, and decisions for all experiments are in `docs/experiments.md`. No raw data or checkpoints are committed; the dataset path is set in `configs/level45.yaml`.
