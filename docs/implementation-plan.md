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

## Plan review and status, end of Week 2 (2026-07-11)

I reviewed the whole plan at the end of the week to confirm it still holds. It does, and the review is worth recording because the week produced a real breakthrough.

What happened after the 2026-07-07 null result, in order. The loss experiment (flip `include_background` to true) was rejected: it left raw specificity at 8 percent and hurt the deployable numbers, so I reverted it. A larger 128-patch experiment was rejected on accuracy once scored on matched cases. An oracle-ROI experiment (crop to the ground-truth pancreas, train at finer resolution) gave my best lesion Dice at the time, 0.234. Then the breakthrough: instead of taking random sub-patches out of the pancreas crop, feed the entire pancreas box to the model as one fixed cube every step (the whole-box change). That became the new best on every axis at once: pancreas Dice 0.807, lesion Dice 0.263, and specificity 55 percent, up from 8 percent, with the anatomical constraint now a near no-op because the model self-corrects. Full hypotheses and decisions for every run are in `docs/experiments.md` (EXP-07 through EXP-13).

The scientific takeaway sharpened the plan rather than changing it. Two training knobs, sampling (EXP-05) and the loss (EXP-07), both failed to move raw specificity, which is strong evidence that over-prediction is a data-scale problem, not a training-knob problem. The thing that finally moved it was structural, giving the model the whole organ in context, not a hyperparameter. So the plan's existing routing of the real fix to more data (Week 4 and capstone) is confirmed, and the whole-box result is the first stage of the localize-then-segment cascade the plan already names as the capstone direction.

What changed and what did not. The architecture and scope are unchanged from the Week 1 proposal: same SuPreM SegResNet, same Level 4.5 target, same data pipeline, same non-diagnostic CADe framing, same React and NiiVue delivery. Every change this week was a model-side improvement inside that outline. I also caught and fixed a measurement bug in the evaluation script (a crop flag that parsed but never applied), which had briefly made a good model look broken, a reminder that train-and-eval preprocessing must match exactly.

Next levers (Week 3): (1) the clarity-curriculum experiment (EXP-13), suggested by my instructor, testing whether weighting training toward the sharpest scans helps; (2) scaling up the tumor data, which needs a switch from the RAM cache to a persistent or disk cache; (3) test-time augmentation at evaluation, which is free; (4) beginning the autonomous pancreas-detector stage in front of the whole-box segmenter, toward the capstone cascade.

---

## Week-by-week execution log

### Week 1 (Jun 29 – Jul 5): setup and data validation. Done.
Repo and design docs scaffolded. Full PanTS Mini downloaded to the external drive and verified. Manifest of 9,901 cases built, patient-level splits created, preprocessing and a single-case sanity check passed. Model, SuPreM transfer loader, loss, metrics, and training loop written. Overfit gate passed. Environment moved to a Python 3.12 virtual environment because 3.14 would not install MLflow.

### Week 2 (Jul 6 – Jul 12): wired pipeline, EDA, and first honest evaluation. Done, and ran ahead.
EDA notebook and data understanding report built from the real manifest; overfit figure pulled from MLflow; the first honest evaluation run and interpreted (the key finding above). The week then ran ahead of plan: I worked the full sensitivity-specificity program (sampling, loss, patch, oracle-ROI, and whole-box experiments), landed the whole-box result as the new best (pancreas 0.807, lesion 0.263, specificity 55 percent), delivered the M2P2 presentation, and kept the daily standup and audience notes. See the plan-review section above and `docs/experiments.md`.

### Week 3 (Jul 13 – Jul 19): data scale and the clarity curriculum.
Baseline training and the first pass of sensitivity-specificity levers already landed in Week 2, so Week 3 moves to the levers the null results pointed at.

Instructor-suggested experiment (EXP-13, clarity curriculum), done. My instructor suggested testing whether training on the clearest scans helps. I built two matched 20-case training sets, one weighted toward the sharpest scans (median 0.80mm slices) and one representative of the pool (1.50mm), holding tumor count and everything else constant, and evaluated both on the same held-out cases. On the metric I pre-registered, segmentation accuracy, it was a soft null: lesion Dice rose only from 0.189 to 0.204 (under my +0.02 bar) and pancreas Dice was flat, consistent with the fact that resampling to 1.5mm normalizes most of the native resolution away before the model sees it. The surprise was specificity: the clarity-trained model was far less likely to flag a tumor on a healthy scan, jumping from 50 to 85 percent raw and 60 to 90 percent cleaned. I treated that as a lead rather than a settled result, because the sharp scans also differ in site and contrast phase, so the gain could have been a domain effect rather than sharpness itself. The clean follow-up, EXP-14, isolated contrast phase at matched resolution and answered it decisively: a non-contrast-trained model was highly specific (90 to 95 percent), while a portal-venous one was sensitive but trigger-happy (10 percent specificity). So contrast phase, not resolution, drove the EXP-13 surprise, and it gives a genuine operating-point dial: train toward non-contrast for specificity or portal-venous for sensitivity. Full numbers for both experiments are in `docs/experiments.md`.

The rest of Week 3: begin scaling the training pool past the 100-case dev subset (the lever every null result points at), which requires switching from the RAM cache to a persistent or disk cache; add test-time augmentation at evaluation (free, no retrain); and keep MLflow tracking and validation curves for both classes throughout. The Week 3 one-on-one check-in focuses on model-choice reasoning and plan health, and the whole-box result plus this experiment log are the evidence I will bring to it.

### Week 4 (Jul 20 – Jul 26): lesion-focused training and full-volume evaluation.
Apply levers 3 and 4 (anatomical constraint, harder negatives). Evaluate with sliding-window inference across full volumes, reporting pancreas and lesion Dice separately plus patient-level sensitivity and specificity. Target a lesion Dice in the 0.35 to 0.50 range and a real, defensible specificity number.

### Week 5 (Jul 27 – Aug 2): evaluation, demo, and delivery.
Failure-case analysis with three-view overlays. Build the React and NiiVue static demo (reads precomputed predictions, no live backend). Write the final report with honest limitations and the non-diagnostic framing. Week 5 one-on-one check-in on the interface and final prep.

---

## Guardrails that do not change

Never commit raw data. Split by patient, never by slice. Full-volume sliding-window inference for evaluation, not patch-only. Report pancreas and lesion Dice separately. Level 4.5 is the line that has to hold; Level 5 is dropped first if a week slips. This is a segmentation assist, not a diagnostic system.
