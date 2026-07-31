# Deliverables index — Weeks 1–4

Archive of the per-week grader maps from Weeks 1 through 4. The **current week's** map lives at the
top of the root [`README.md`](../README.md); this file keeps the earlier weeks addressable without
crowding the project README.

All weekly deliverable folders now live under [`deliverables/`](../deliverables/).

---

### Week 4 — M4A1: Tuning, Orchestration & Deployment · M4A2: Daily Check-Ins

| Assignment / rubric criterion | Deliverable | Location |
|-----------|-------------|----------|
| **M4A1 — full report (§1–5)** | Tuning, orchestration & deployment report | [`deliverables/week4/tuning-orchestration-report.md`](../deliverables/week4/tuning-orchestration-report.md) |
| §1 Hyperparameter Tuning | Optuna (Bayesian TPE) study + single-variable ablation; all runs in MLflow; final model registered | report §1 · [`scripts/tune_optuna.py`](../scripts/tune_optuna.py) · [`docs/experiments.md`](../docs/experiments.md) |
| §1 — *MLflow tuning runs (image)* | `pants-level45-optuna` 15-trial run list | [`deliverables/week4/img/mlflow-tuning-runs.png`](../deliverables/week4/img/mlflow-tuning-runs.png) |
| §1 — *registered model (image)* | `pancreas-lesion-segmenter` v1 + provenance | [`deliverables/week4/img/mlflow-registered-model.png`](../deliverables/week4/img/mlflow-registered-model.png) |
| §2 Final Model Evaluation | Held-out TEST metrics (lesion Dice 0.474, pancreas 0.827, detection 96%, specificity 17%) + honest failure modes | report §2 · [`scripts/evaluate.py`](../scripts/evaluate.py) · [`scripts/analyze_cases.py`](../scripts/analyze_cases.py) |
| §2 — *test visualization (image)* | Lesion Dice by tumor size & contrast phase | [`deliverables/week4/img/test-by-size-phase.svg`](../deliverables/week4/img/test-by-size-phase.svg) |
| §2 — *sample predictions, CV track (images)* | Clean catch + honest small-tumor miss, with CADe confidence | [`deliverables/week4/img/sample-good-case.png`](../deliverables/week4/img/sample-good-case.png) · [`sample-small-miss.png`](../deliverables/week4/img/sample-small-miss.png) |
| §3 Pipeline Orchestration | End-to-end pipeline + trigger / data-versioning / model-logging / error-handling | report §3 |
| §3 — *pipeline diagram (image)* | Ingestion → training → eval → serving flowchart | [`deliverables/week4/img/pipeline-diagram.svg`](../deliverables/week4/img/pipeline-diagram.svg) |
| §4 Model Deployment | FastAPI endpoint + MLflow registry + live smoke test | report §4 · [`scripts/serve.py`](../scripts/serve.py) · [`scripts/register_model.py`](../scripts/register_model.py) |
| §4 — *live endpoint (image)* | `/health` healthy-response page | [`deliverables/week4/img/endpoint-health.png`](../deliverables/week4/img/endpoint-health.png) |
| §5 Decisions & reflection | Architectural trade-offs / what I'd do with more time | report §5 |
| §6 AI docs | AI context + Week 4 usage log + plan update | [`CLAUDE.md`](../CLAUDE.md) · [`docs/ai-usage-log.md`](../docs/ai-usage-log.md) · [`docs/implementation-plan.md`](../docs/implementation-plan.md) |
| **M4A2 — Daily Check-Ins** | Daily standup log (Mon–Fri, incl. the Week 4 technical-interview retrospective entry) | [`docs/standup-log.md`](../docs/standup-log.md) |

**Supporting Week 4 work:** experiment log with the headline model (EXP-24), the rejected anatomy-aware experiment (EXP-26), and the pre-registered specificity experiment (EXP-25 — cleared spec 17%→46% but rejected on the ≥90% detection floor) in [`docs/experiments.md`](../docs/experiments.md) · deployment regression tests in [`tests/`](../tests/) · full-points checklist in [`deliverables/week4/M4A1-checklist.md`](../deliverables/week4/M4A1-checklist.md).

### Week 3 — M3P1: Experiment Review & Model Selection · M3A2: Daily Check-Ins

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M3P1 — Presenter** | ML experimentation report (features, experiment comparison, model selection, plan status) | [`deliverables/week3/ml-experimentation-report.md`](../deliverables/week3/ml-experimentation-report.md) |
| M3P1 — *presentation* | Slide deck (10-min talk) | [`deliverables/week3/experiment-review-slides.pptx`](../deliverables/week3/experiment-review-slides.pptx) · [PDF](../deliverables/week3/experiment-review-slides.pdf) |
| **M3P1 — Audience** | Audience notes on peers' presentations | [`docs/audience-notes-week3.md`](../docs/audience-notes-week3.md) |
| **M3A2 — Daily Check-Ins** | Daily standup log (Mon–Fri + the Week 3 1-on-1 retrospective) | [`docs/standup-log.md`](../docs/standup-log.md) |
| M3P1 — *experiment log* | Every run as a formal experiment (hypothesis → decision), EXP-01 → EXP-22 | [`docs/experiments.md`](../docs/experiments.md) |
| M3P1 — *revised plan (Section 5)* | Where the project stands vs the 5-week plan | [`docs/implementation-plan.md`](../docs/implementation-plan.md) |
| M3P1 — *AI docs (Section 6)* | AI context file + weekly usage log | [`CLAUDE.md`](../CLAUDE.md) · [`docs/ai-usage-log.md`](../docs/ai-usage-log.md) |
| M3P1 — *metrics audit* | Self + independent-AI audit of the scoring (no leakage; ROI-leak finding) | [`docs/codex-metrics-audit.md`](../docs/codex-metrics-audit.md) |
| **M3A1 — MLflow screenshots** | Run-comparison + clean-candidate run (metrics / curves / params) + eval terminal | [`deliverables/week3/mlflow-run-comparison.png`](../deliverables/week3/mlflow-run-comparison.png) · [`mlflow-clean-run-curves.png`](../deliverables/week3/mlflow-clean-run-curves.png) · [`mlflow-clean-run-metrics.png`](../deliverables/week3/mlflow-clean-run-metrics.png) · `eval-clean-run-terminal.png` |

**Supporting Week 3 work:** [`deliverables/week3/diagrams/`](../deliverables/week3/diagrams/) (presentation diagrams: whole-box vs patches, the input array, metrics). Post-presentation, acting on the Week 3 check-in feedback, the pipeline is being made fully autonomous and leak-free (localize the pancreas from the full CT, then segment) — tracked in [`docs/experiments.md`](../docs/experiments.md) (EXP-20/22) and the Saturday standup entry.

### Week 2

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M2A1 — Data Understanding Report** | Full report, sections 1–5 | [`deliverables/week2/data-understanding-report.md`](../deliverables/week2/data-understanding-report.md) |
| M2A1 | EDA notebook (all visualizations, real data) | [`deliverables/week2/eda-notebook.ipynb`](../deliverables/week2/eda-notebook.ipynb) |
| M2A1 — *revised plan* | Finalized Core Requirements + 5-week plan | [`docs/implementation-plan.md`](../docs/implementation-plan.md) · [`docs/schedule.md`](../docs/schedule.md) |
| M2A1 — *AI docs* | AI context file + weekly usage log | [`docs/Claude.md`](../docs/Claude.md) · [`docs/ai-usage-log.md`](../docs/ai-usage-log.md) |
| **M2P2 — Presentation** | Presenter: report + notebook (above) | [`deliverables/week2/`](../deliverables/week2/) |
| M2P2 — *audience deliverable* | Audience notes on peers' presentations | [`docs/audience-notes-week2.md`](../docs/audience-notes-week2.md) |
| **M2A2 — Daily Check-Ins** | Daily standup log (Mon–Fri) | [`docs/standup-log.md`](../docs/standup-log.md) |

**Supporting Week 2 work:** [`docs/experiments.md`](../docs/experiments.md) (formal experiment log, EXP-01 → EXP-13) · [`deliverables/week2/diagrams/`](../deliverables/week2/diagrams/) (presentation diagrams) · [`deliverables/week2/presentation-runsheet.md`](../deliverables/week2/presentation-runsheet.md).

### Week 1

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M1A1 — Project Proposal** | Proposal (7 sections) · schedule · AI plan | [`docs/proposal.md`](../docs/proposal.md) · [`docs/schedule.md`](../docs/schedule.md) · [`docs/Claude.md`](../docs/Claude.md) |
| M1A1 — *agent plan* | Agent operating guide + AI-vs-manual split | [`docs/agent-plan.md`](../docs/agent-plan.md) |
| **M1A2 — Daily Check-Ins** | Standup log (incl. Week 1 retrospective) | [`docs/standup-log.md`](../docs/standup-log.md) |
| **M1P1 — Pitch & Defense** | Pitch + Q&A · audience notes | [`docs/pitch.md`](../docs/pitch.md) · [`docs/audience-notes-week1.md`](../docs/audience-notes-week1.md) |

**Supporting context:** [`CLAUDE.md`](../CLAUDE.md) (project state an AI agent reads) · full technical design in `docs/` (see below).

---
