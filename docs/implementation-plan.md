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
2. Add a lesion decision-threshold knob. Instead of taking the raw argmax, require the lesion class probability to clear a threshold, and sweep that threshold to trade sensitivity for specificity. This is a cheap post-hoc dial and gives me a real sensitivity-specificity curve to show.
3. Constrain lesion predictions to lie inside the predicted pancreas. A pancreatic lesion outside the pancreas is anatomically impossible, and this alone should remove many false positives in healthy scans. This is a CADe-sound rule, not a hack.
4. Mine harder negatives near the pancreas. Sample negative patches from the pancreas region of healthy scans so the model actually learns what a normal pancreas looks like, rather than only seeing easy far-from-organ background.
5. If specificity is still weak by Week 4, the honest fallback is to widen the training pool beyond the 100-case dev subset, and to report a strong pancreas result with a documented analysis of why lesion specificity is hard. More data is the real long-term fix and is the capstone's job.

I will report specificity before and after each change, and I will keep pancreas and lesion Dice separate throughout.

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
