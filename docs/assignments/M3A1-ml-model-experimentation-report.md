# M3A1: ML Model Experimentation Report

> Due Sunday by 11:59pm · Points: 25 · Submit via GitHub · Available until Jul 26

## Overview

This week moves from data to models. The goal is not to find the perfect model — it is to run disciplined experiments, track everything, and make defensible decisions about which direction to take into Week 4. The MLflow experiment log is as much a deliverable as the code.

## Required sections (report covers 1–4; 5–6 are living files)

1. Feature Engineering Summary
   - Document the final set of features used for modeling. For each feature, briefly describe any transformations applied (encoding, scaling, binning, embeddings, augmentation for CV) and why.
   - Note any features dropped since Week 2 and the reason.
2. Experiment Design (describe the approach before the results)
   - What model families or architectures were experimented with, and why?
   - How were the train / validation / test splits structured?
   - What evaluation metric(s) are being optimized for, and why are they appropriate for this problem?
   - CV / deep-learning tracks: describe backbone selection, whether weights were frozen or unfrozen, and the augmentation strategy.
3. Experiment Results
   - Document at least 3 distinct experiments logged in MLflow. For each: model type and key configuration, training and validation metrics, and a brief interpretation (what did this run tell you?).
   - Present a comparison table or MLflow screenshot showing all runs side by side.
4. Model Selection & Justification
   - Identify the candidate model for Week 4 tuning. Justify the selection based on experiment results — not just the highest metric, but the trade-offs considered (complexity, interpretability, inference speed, overfitting risk).
5. Revised Implementation Plan
   - Update `implementation-plan.md` to reflect any changes based on what was learned this week. If on track, note that explicitly.
6. AI Documentation Files
   - `claude.md` — update if the context definition or AI instructions have evolved based on how it is actually being used.
   - `ai-usage-log.md` — add the Week 3 entry: tasks assisted, prompts that worked well, and any cases where AI output needed correction or guidance.

## Deliverables

Submit via GitHub (branch → merge to main, inside a `week3/` documentation folder):

- `ml-experimentation-report.md` — full report covering sections 1–4 above.
- MLflow experiment screenshots or an exported run comparison, included in the report or as image files in the folder.

Live in root `docs/`, updated in place:

- `implementation-plan.md` — Week 3 update added.
- `claude.md` — updated if applicable.
- `ai-usage-log.md` — Week 3 entry added.

## Rubric (25 pts)

| Criterion | Description | Pts |
|-----------|-------------|-----|
| Feature Engineering | Final feature set documented with clear justification for inclusions, exclusions, and transformations. Choices visibly grounded in Week 2 EDA findings. CV tracks include augmentation strategy and backbone rationale. | 5 |
| Experiment Design Rigor | At least 3 distinct experiments logged in MLflow. Model families or architectures are meaningfully different. Splits and evaluation metrics are appropriate and justified for the business problem. | 5 |
| Results Interpretation | Each experiment is interpreted, not just reported. The student explains what each run revealed and how it informed the next decision. Comparison table or MLflow screenshot included. | 5 |
| Model Selection Justification | Candidate model clearly identified and the selection justified by weighing multiple trade-offs (not just best metric) — complexity, interpretability, overfitting risk, business fit. | 5 |
| AI Documentation Files | `ai-usage-log.md` Week 3 entry is specific — names tasks, describes effective prompts, and calls out at least one instance of AI output that required correction or guidance. `implementation-plan.md` updated with a clear Week 3 status. | 5 |

## Learning Outcomes

- Apply experiment tracking, hyperparameter tuning, and evaluation in model development.
- Manage an independent project from proposal to delivery.
