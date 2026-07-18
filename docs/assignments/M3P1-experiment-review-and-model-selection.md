# M3P1: Experiment Review & Model Selection (Presentation)

> Due Friday by 11:59pm · Points: 25 · Submit via GitHub · Available until Jul 24

## Overview

Present the ML experimentation process to the class as if briefing a technical lead and a business stakeholder simultaneously. The technical lead wants rigorous, well-tracked experiments. The business stakeholder wants to understand what the model does, how good it is, and whether it is trustworthy enough to build on. Peers will challenge both dimensions.

## Instructions

Presenter — deliver a 10-minute presentation covering:

1. The features engineered and why — one or two key decisions worth highlighting.
2. A walk-through of the experiment comparison — what was tried, what the results showed, and what was learned from each run.
3. The selected model and the trade-offs weighed in choosing it.
4. Where you stand against the implementation plan heading into Week 4.

Be ready for 5 minutes of Q&A (expect questions about metric choice, overfitting, experiment fairness, and whether the model selection makes sense for the business problem).

Audience — same structured engagement as previous weeks. For the notes this week, focus on:

- Whether the experiments are genuinely distinct or just minor variations.
- Whether the model selection is justified by the evidence presented, not just the top metric.
- Whether a non-technical stakeholder could understand why this model was chosen.

## Deliverables

- Presenter: `ml-experimentation-report.md` via GitHub.
- Audience: `audience-notes-week3.md`.

## Rubric (25 pts)

| Criterion | Role | Description | Pts |
|-----------|------|-------------|-----|
| Experiment Communication | Presenter | Experiments presented as a learning narrative — the audience understands what was tried, what was learned from each run, and how it led to the next decision. Both technical and non-technical dimensions addressed. | 5 |
| Model Selection Defense | Presenter | Selected model defended using specific evidence from experiments. Trade-offs acknowledged. A non-technical stakeholder could understand why this model was chosen over others. | 4 |
| Plan Transparency | Presenter | Honest account of where you stand against the implementation plan — on track, ahead, or behind — and what adjustments are being made if needed. | 4 |
| Q&A Confidence & Depth | Presenter | Responds to technical questions (metric choice, overfitting, data leakage) and business questions (what does this model do, can we trust it) with clarity and appropriate depth. | 4 |
| Question Quality | Audience | Questions probe experiment rigor, metric appropriateness, or the business case for model selection. Specific and substantive — not answerable with yes or no. | 4 |
| Audience Notes Quality | Audience | Notes for all presentations include a summary, questions asked, and an assessment of whether experiments are rigorous and whether model selection is justified by evidence — not just the top metric. | 4 |

## Learning Outcomes

- Apply experiment tracking, hyperparameter tuning, and evaluation in model development.
- Communicate and defend technical work to a non-technical audience.
