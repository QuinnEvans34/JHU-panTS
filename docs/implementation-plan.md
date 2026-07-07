# Implementation Plan

Project: 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS), Level 4.5.

This is a living plan. I add to it as the project moves; I do not rewrite history. Each week I record what I actually intended to build, what got done, and what the results pushed me to change next. The finalized Core Requirements are the measurable version of this plan and they live in `week2/data-understanding-report.md` Section 5; the week-by-week milestones live in `schedule.md`. This file is the connective tissue between them, plus the running record of decisions.

---

## Where the project stands (updated 2026-07-06)

The full pipeline is built and validated end to end. Data pipeline (manifest, patient-level splits, preprocessing, patch sampling) is done. The model (SuPreM SegResNet), loss, metrics, training loop, sliding-window inference, and CADe post-processing are all written and running on the Apple Silicon MPS backend. The Week 2 overfit gate passed: on a fixed batch, training loss fell from 1.87 to 0.54, pancreas Dice reached 0.89, and on a tumor-positive overfit the lesion reached about 0.85. That proves the pipeline can learn both classes.

The first honest evaluation is in, and it defines the central problem for the rest of the project.

### The key finding (2026-07-06 evaluation)

On the validation split, scored correctly (lesion accuracy on tumor-positive cases, specificity on tumor-free cases):

- Pancreas Dice: 0.720
- Lesion Dice, raw: 0.169
- Lesion Dice, after CADe cleanup: 0.139
- Specificity, raw: 1 of 12 healthy cases correctly not flagged (8 percent)
- Specificity, after CADe cleanup: 1 of 12 (8 percent, unchanged)

What this means. The model does find tumors, so the core capability is there. But it is badly over-predicting: it flags a lesion in almost every healthy scan, which is a specificity of 8 percent. The most important detail is that post-processing did not help. Keeping the largest connected component and dropping sub-threshold blobs left specificity unchanged and actually lowered lesion Dice on positive cases from 0.169 to 0.139. That tells me the false positives are large, connected regions, not scattered specks, so cleanup cannot rescue them. The fix has to come from training the model to be less trigger-happy, plus an anatomical constraint, not from more aggressive post-processing.

This checkpoint was trained with the aggressive recipe (DiceFocal loss, no background class, heavy positive patch sampling), which maximizes sensitivity at the cost of specificity. The sampling has since been rebalanced to 1:1 in the config but not yet trained. So the immediate next step is a retrain, then a re-evaluation, before reaching for anything more complex.

---

## The sensitivity and specificity strategy (Weeks 3 and 4)

The whole model-improvement effort is now organized around moving specificity up without collapsing lesion detection. Planned levers, in the order I will try them, cheapest and most likely first:

1. Retrain with balanced 1:1 patch sampling (already in config) and re-evaluate. The current checkpoint predates this change, so this is the honest baseline before anything else.
2. Add a lesion decision-threshold knob. Instead of taking the raw argmax, require the lesion class probability to clear a threshold, and sweep that threshold to trade sensitivity for specificity. This is a cheap post-hoc dial and gives me a real sensitivity-specificity curve to show. Coded and unit-tested: `evaluate.py --sweep`.
3. Constrain lesion predictions to lie inside the predicted pancreas. A pancreatic lesion outside the pancreas is anatomically impossible, and this alone should remove many false positives in healthy scans. This is a CADe-sound rule, not a hack. Coded and unit-tested: `postprocess(..., lesion_within_pancreas_mm=10)`, exposed as `evaluate.py --lesion-within-pancreas-mm 10`.
4. Mine harder negatives near the pancreas. Sample negative patches from the pancreas region of healthy scans so the model actually learns what a normal pancreas looks like, rather than only seeing easy far-from-organ background. Coded: set `sampling.strategy: classes` in the config (uses class-ratio patch sampling, default ratios bg:pancreas:lesion = 1:1:2), then retrain.
5. If specificity is still weak by Week 4, the honest fallback is to widen the training pool beyond the 100-case dev subset, and to report a strong pancreas result with a documented analysis of why lesion specificity is hard. More data is the real long-term fix and is the capstone's job.

I will report specificity before and after each change, and I will keep pancreas and lesion Dice separate throughout.

Status note (2026-07-06): levers 2, 3, and 4 are now coded and their logic is unit-tested on synthetic volumes (the threshold produces a monotonic sensitivity-specificity tradeoff; the anatomical constraint keeps a lesion inside the pancreas, removes one that floats away, and safely does nothing when no pancreas is predicted). They are waiting on the balanced retrain (lever 1) to be run against. The order tonight is: run the balanced retrain, evaluate with `--sweep --lesion-within-pancreas-mm 10` to read the whole tradeoff at once, then decide whether the threshold and constraint are enough or whether the class-ratio retrain (lever 4) is worth a run.

First real read on the levers (2026-07-06, aggressive `best.pt` step 6000, val split, n=12/12): the anatomical constraint is the strong lever. Specificity went from 8 percent raw (1/12) to 42 percent cleaned (5/12) once lesion components that float more than 10mm from the predicted pancreas were demoted, with no retraining. The probability-threshold sweep was a weak lever on this model: lesion Dice stayed flat around 0.16 to 0.18 and specificity held at 8 percent until threshold 0.90, where it only reached 25 percent (3/12). Interpretation: the false positives on healthy scans are high-confidence and near the organ boundary, so a probability cutoff cannot remove them but a geometric rule can. Cost: cleaned lesion Dice on tumor cases dropped from 0.169 to 0.139, the expected sensitivity-for-specificity trade. This all sits on the over-predicting checkpoint; the balanced retrain (running overnight 2026-07-06) is the other half, and the hope is that a less trigger-happy base model plus the anatomical constraint stack for both a higher base specificity and fewer far-field false positives. A later refinement worth testing: apply the anatomical constraint while relaxing the largest-component step, since true lesions sit inside the pancreas and should not need that step, which may recover the lost lesion Dice.

Balanced-sampling retrain result (2026-07-07, balanced `best.pt` step 6000, val split, n=12/12): a null result, and a useful one. The balanced 1:1 model came out essentially identical to the aggressive model on every metric: pancreas Dice 0.721 versus 0.720, lesion Dice 0.169 versus 0.169, raw specificity 8 percent versus 8 percent, and cleaned specificity 42 percent versus 42 percent. Changing the positive-to-negative patch ratio did not move the over-prediction at all. That cleanly rules out sampling as the cause and points at two remaining suspects: the loss, which currently excludes background so the model is never rewarded for correctly calling healthy tissue not-lesion, and the small 100-case dataset. The anatomical constraint is confirmed as the one robust lever, giving the same 8 to 42 percent lift on both models because it is a geometric post-hoc rule independent of training. Revised lever order below: the loss moves to the front of the model-side work, ahead of any more sampling changes.

Revised priority after the null result (2026-07-07):

1. Attack the loss. Give the model an explicit reason to predict background, so it is penalized for false lesion calls on healthy tissue. First experiment: keep DiceFocal (its focal term is built for class imbalance, so it should not bury the lesion the way plain Dice-plus-cross-entropy did in the earliest runs) but flip `include_background` to true. This is a single-variable change against the current balanced run, so it is a clean comparison. Fallback knobs if it over-corrects toward under-prediction: down-weight the Dice term relative to the focal term, or add class weights that keep the lesion up-weighted.
2. Keep the anatomical constraint as the banked specificity lever (8 to 42 percent), applied at evaluation.
3. Try the harder-negatives sampler (`sampling.strategy: classes`) only if the loss change is not enough, since sampling already proved a weak lever here.
4. Scale past 100 cases. The null result strongly suggests data volume is the real ceiling; this is the capstone direction.

Separate accuracy lever (field of view): the 96-cube patch at 1.5mm sees a 14.4cm window, which can clip the long pancreas tail and gives each inference tile only local context. EXP-02 in `docs/experiments.md` tests whether a 128-cube (19.2cm, whole-pancreas) improves pancreas and/or lesion Dice, as a clean single-variable run wired behind `train.py --patch 128` and `evaluate.py --roi 128`. Queued behind the loss experiment; adopt 128 for the rest of the project only if it clears the pre-registered +0.03 pancreas / +0.02 lesion Dice bar. Growing the field of view (patch) is transfer-safe; growing the network width/depth is not (breaks SuPreM loading) and is deferred to capstone.

---

## Week-by-week execution log

### Week 1 (Jun 29 – Jul 5): setup and data validation. Done.
Repo and design docs scaffolded. Full PanTS Mini downloaded to the external drive and verified. Manifest of 9,901 cases built, patient-level splits created, preprocessing and a single-case sanity check passed. Model, SuPreM transfer loader, loss, metrics, and training loop written. Overfit gate passed. Environment moved to a Python 3.12 virtual environment because 3.14 would not install MLflow.

### Week 2 (Jul 6 – Jul 12): wired pipeline, EDA, and first honest evaluation. In progress.
Planned: finish the EDA notebook and data understanding report from real data, run a proper evaluation, and set the tuning direction. Done so far: EDA notebook and report built from the real manifest; overfit figure pulled from MLflow; evaluation run and interpreted (the key finding above). Next in the week: draft the presentation and audience notes, keep the daily standup, and start the balanced retrain so Week 3 opens with fresh numbers.

### Week 3 (Jul 13 – Jul 19): baseline training and the sensitivity-specificity work begins.
Run a quick pancreas-only training as a fast pipeline check, then the balanced Level 4.5 retrain on the dev subset with MLflow tracking and validation curves for both classes. Apply levers 1 and 2 above (balanced sampling, then the threshold sweep) and produce a first sensitivity-specificity curve. Week 3 one-on-one check-in focuses on model choice reasoning and plan health.

### Week 4 (Jul 20 – Jul 26): lesion-focused training and full-volume evaluation.
Apply levers 3 and 4 (anatomical constraint, harder negatives). Evaluate with sliding-window inference across full volumes, reporting pancreas and lesion Dice separately plus patient-level sensitivity and specificity. Target a lesion Dice in the 0.35 to 0.50 range and a real, defensible specificity number.

### Week 5 (Jul 27 – Aug 2): evaluation, demo, and delivery.
Failure-case analysis with three-view overlays. Build the React and NiiVue static demo (reads precomputed predictions, no live backend). Write the final report with honest limitations and the non-diagnostic framing. Week 5 one-on-one check-in on the interface and final prep.

---

## Guardrails that do not change

Never commit raw data. Split by patient, never by slice. Full-volume sliding-window inference for evaluation, not patch-only. Report pancreas and lesion Dice separately. Level 4.5 is the line that has to hold; Level 5 is dropped first if a week slips. This is a segmentation assist, not a diagnostic system.
