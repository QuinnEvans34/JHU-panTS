# JHU-PanTS — 3D Pancreas-Aware Pancreatic Lesion Segmentation

A 3D deep-learning pipeline that takes an abdominal CT scan, segments the **pancreas** and any **pancreatic lesion**, and flags *"there could be a tumor here."* Built on the Johns Hopkins **PanTS** dataset with MONAI/PyTorch, running on Apple Silicon (MPS).

> **This is an image-segmentation / annotation-assist tool, not a diagnostic system.** A human radiologist reviews and edits every output; no clinical determination is made or claimed.

---

## 📌 Graded deliverables — where to find everything

*(This table is the grader's map. Most recent week first.)*

### Week 4 (current) — M4A1: Tuning, Orchestration & Deployment · M4A2: Daily Check-Ins

| Assignment / rubric criterion | Deliverable | Location |
|-----------|-------------|----------|
| **M4A1 — full report (§1–5)** | Tuning, orchestration & deployment report | [`week4/tuning-orchestration-report.md`](week4/tuning-orchestration-report.md) |
| §1 Hyperparameter Tuning | Optuna (Bayesian TPE) study + single-variable ablation; all runs in MLflow; final model registered | report §1 · [`scripts/tune_optuna.py`](scripts/tune_optuna.py) · [`docs/experiments.md`](docs/experiments.md) |
| §1 — *MLflow tuning runs (image)* | `pants-level45-optuna` 15-trial run list | [`week4/img/mlflow-tuning-runs.png`](week4/img/mlflow-tuning-runs.png) |
| §1 — *registered model (image)* | `pancreas-lesion-segmenter` v1 + provenance | [`week4/img/mlflow-registered-model.png`](week4/img/mlflow-registered-model.png) |
| §2 Final Model Evaluation | Held-out TEST metrics (lesion Dice 0.474, pancreas 0.827, detection 96%, specificity 17%) + honest failure modes | report §2 · [`scripts/evaluate.py`](scripts/evaluate.py) · [`scripts/analyze_cases.py`](scripts/analyze_cases.py) |
| §2 — *test visualization (image)* | Lesion Dice by tumor size & contrast phase | [`week4/img/test-by-size-phase.svg`](week4/img/test-by-size-phase.svg) |
| §2 — *sample predictions, CV track (images)* | Clean catch + honest small-tumor miss, with CADe confidence | [`week4/img/sample-good-case.png`](week4/img/sample-good-case.png) · [`sample-small-miss.png`](week4/img/sample-small-miss.png) |
| §3 Pipeline Orchestration | End-to-end pipeline + trigger / data-versioning / model-logging / error-handling | report §3 |
| §3 — *pipeline diagram (image)* | Ingestion → training → eval → serving flowchart | [`week4/img/pipeline-diagram.svg`](week4/img/pipeline-diagram.svg) |
| §4 Model Deployment | FastAPI endpoint + MLflow registry + live smoke test | report §4 · [`scripts/serve.py`](scripts/serve.py) · [`scripts/register_model.py`](scripts/register_model.py) |
| §4 — *live endpoint (image)* | `/health` healthy-response page | [`week4/img/endpoint-health.png`](week4/img/endpoint-health.png) |
| §5 Decisions & reflection | Architectural trade-offs / what I'd do with more time | report §5 |
| §6 AI docs | AI context + Week 4 usage log + plan update | [`CLAUDE.md`](CLAUDE.md) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md) · [`docs/implementation-plan.md`](docs/implementation-plan.md) |
| **M4A2 — Daily Check-Ins** | Daily standup log (Mon–Fri, incl. the Week 4 technical-interview retrospective entry) | [`docs/standup-log.md`](docs/standup-log.md) |

**Supporting Week 4 work:** experiment log with the headline model (EXP-24), the rejected anatomy-aware experiment (EXP-26), and the pre-registered specificity experiment (EXP-25 — cleared spec 17%→46% but rejected on the ≥90% detection floor) in [`docs/experiments.md`](docs/experiments.md) · deployment regression tests in [`tests/`](tests/) · full-points checklist in [`week4/M4A1-checklist.md`](week4/M4A1-checklist.md).

### Week 3 — M3P1: Experiment Review & Model Selection · M3A2: Daily Check-Ins

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M3P1 — Presenter** | ML experimentation report (features, experiment comparison, model selection, plan status) | [`week3/ml-experimentation-report.md`](week3/ml-experimentation-report.md) |
| M3P1 — *presentation* | Slide deck (10-min talk) | [`week3/experiment-review-slides.pptx`](week3/experiment-review-slides.pptx) · [PDF](week3/experiment-review-slides.pdf) |
| **M3P1 — Audience** | Audience notes on peers' presentations | [`docs/audience-notes-week3.md`](docs/audience-notes-week3.md) |
| **M3A2 — Daily Check-Ins** | Daily standup log (Mon–Fri + the Week 3 1-on-1 retrospective) | [`docs/standup-log.md`](docs/standup-log.md) |
| M3P1 — *experiment log* | Every run as a formal experiment (hypothesis → decision), EXP-01 → EXP-22 | [`docs/experiments.md`](docs/experiments.md) |
| M3P1 — *revised plan (Section 5)* | Where the project stands vs the 5-week plan | [`docs/implementation-plan.md`](docs/implementation-plan.md) |
| M3P1 — *AI docs (Section 6)* | AI context file + weekly usage log | [`CLAUDE.md`](CLAUDE.md) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md) |
| M3P1 — *metrics audit* | Self + independent-AI audit of the scoring (no leakage; ROI-leak finding) | [`docs/codex-metrics-audit.md`](docs/codex-metrics-audit.md) |
| **M3A1 — MLflow screenshots** | Run-comparison + clean-candidate run (metrics / curves / params) + eval terminal | [`week3/mlflow-run-comparison.png`](week3/mlflow-run-comparison.png) · [`mlflow-clean-run-curves.png`](week3/mlflow-clean-run-curves.png) · [`mlflow-clean-run-metrics.png`](week3/mlflow-clean-run-metrics.png) · `eval-clean-run-terminal.png` |

**Supporting Week 3 work:** [`week3/diagrams/`](week3/diagrams/) (presentation diagrams: whole-box vs patches, the input array, metrics). Post-presentation, acting on the Week 3 check-in feedback, the pipeline is being made fully autonomous and leak-free (localize the pancreas from the full CT, then segment) — tracked in [`docs/experiments.md`](docs/experiments.md) (EXP-20/22) and the Saturday standup entry.

### Week 2

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M2A1 — Data Understanding Report** | Full report, sections 1–5 | [`week2/data-understanding-report.md`](week2/data-understanding-report.md) |
| M2A1 | EDA notebook (all visualizations, real data) | [`week2/eda-notebook.ipynb`](week2/eda-notebook.ipynb) |
| M2A1 — *revised plan* | Finalized Core Requirements + 5-week plan | [`docs/implementation-plan.md`](docs/implementation-plan.md) · [`docs/schedule.md`](docs/schedule.md) |
| M2A1 — *AI docs* | AI context file + weekly usage log | [`docs/Claude.md`](docs/Claude.md) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md) |
| **M2P2 — Presentation** | Presenter: report + notebook (above) | [`week2/`](week2/) |
| M2P2 — *audience deliverable* | Audience notes on peers' presentations | [`docs/audience-notes-week2.md`](docs/audience-notes-week2.md) |
| **M2A2 — Daily Check-Ins** | Daily standup log (Mon–Fri) | [`docs/standup-log.md`](docs/standup-log.md) |

**Supporting Week 2 work:** [`docs/experiments.md`](docs/experiments.md) (formal experiment log, EXP-01 → EXP-13) · [`week2/diagrams/`](week2/diagrams/) (presentation diagrams) · [`week2/presentation-runsheet.md`](week2/presentation-runsheet.md).

### Week 1

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M1A1 — Project Proposal** | Proposal (7 sections) · schedule · AI plan | [`docs/proposal.md`](docs/proposal.md) · [`docs/schedule.md`](docs/schedule.md) · [`docs/Claude.md`](docs/Claude.md) |
| M1A1 — *agent plan* | Agent operating guide + AI-vs-manual split | [`docs/agent-plan.md`](docs/agent-plan.md) |
| **M1A2 — Daily Check-Ins** | Standup log (incl. Week 1 retrospective) | [`docs/standup-log.md`](docs/standup-log.md) |
| **M1P1 — Pitch & Defense** | Pitch + Q&A · audience notes | [`docs/pitch.md`](docs/pitch.md) · [`docs/audience-notes-week1.md`](docs/audience-notes-week1.md) |

**Supporting context:** [`CLAUDE.md`](CLAUDE.md) (project state an AI agent reads) · full technical design in `docs/` (see below).

---

## What the project is

**Problem & user.** Radiologists and imaging annotators must hand-trace the pancreas and any tumor on 3D CT — slow, tedious work on a hard-to-see organ. The user is a **radiologist / imaging annotator** who, for each scan, **accepts, edits, or rejects** an automatically proposed outline instead of drawing it from scratch.

**Dataset.** [PanTS](https://github.com/MrGiovanni/PanTS) (Johns Hopkins, NeurIPS 2025) — open-source, a static benchmark. The Mini release used here is 9,000 training + 901 test CT volumes with voxel-wise masks for the pancreas, its subregions, the lesion, and ~28 surrounding structures. Real tumor prevalence: **10.4%**.

**ML approach.** Supervised **3D semantic segmentation** (background / pancreas / lesion) with a **SegResNet** (MONAI), fine-tuned from **SuPreM** pretrained weights and compared against a from-scratch baseline. Extreme class imbalance (lesion ≈ 0.04% of a volume) is handled with a Dice-based loss + tumor-positive patch sampling. Evaluation is full-volume sliding-window inference; **pancreas and lesion Dice are reported separately**, plus patient-wise sensitivity/specificity (the CADe "possible tumor" story).

**Business-facing layer.** A planned **React + NiiVue** web app: tri-planar CT with pancreas/lesion overlays, a rotatable 3D view, a "possible tumor" summary (location, volume, confidence), and mask export for editing in a real tool.

---

## Current status (Week 4 — complete)

- ✅ **Data understood** — EDA built from the real 9,901-case manifest: 10.4% tumor prevalence, lesion volume spanning five orders of magnitude, extreme geometry heterogeneity (8 to 1,000+ slices).
- ✅ **Pipeline validated** — Stage 0 overfit gate passed; the ingestion → resample → patch → model path is proven end to end.
- ✅ **Over-prediction diagnosed and fixed** — first eval was pancreas Dice 0.72 / lesion 0.17 with only 8% specificity. A **whole-box ROI** change (feed the entire pancreas box as one cube) lifted specificity to 55% and became the winning recipe.
- ✅ **Data is the lever (Week 3 headline)** — four recipe knobs (sampling, loss, field of view, resolution) were all nulls on tumor accuracy on the disjoint dev subset; scaling the tumor data was the only thing that moved it.
- ✅ **Validation leakage found, fixed, and re-measured (the honest headline)** — an end-of-week adversarial code audit caught a bug in my data-scaling split builder that leaked validation cases into training, inflating an earlier 0.528 result. I fixed the root cause (splits now sampled from the carved train fold + a startup guard that aborts on any train/val overlap), retrained on a clean disjoint split, and the real held-out numbers are **lesion Dice 0.415, pancreas Dice 0.817, detection sensitivity 95%, specificity 15%** (val n=40). It did not collapse, so the data-scaling result was genuine — just smaller than the leaked figure. The candidate model for Week 4 tuning is this clean whole-box SegResNet. Full write-up in [`week3/ml-experimentation-report.md`](week3/ml-experimentation-report.md); audit in [`docs/codex-audit-week4.md`](docs/codex-audit-week4.md).
- ✅ **Final held-out TEST evaluation (Week 4 headline)** — the registered whole-box SegResNet+SuPreM model, scored **once** on the untouched official 901-case test set: **lesion Dice 0.474 [95% CI 0.42–0.52], pancreas Dice 0.827, detection sensitivity 96%, specificity 17%** — right against the ~0.53 published reference, on a split I did not choose. Full write-up in [`week4/tuning-orchestration-report.md`](week4/tuning-orchestration-report.md).
- ✅ **Tuned, registered, deployed** — an Optuna (Bayesian TPE) search confirmed the hand-tuned learning rate was already near-optimal; the final model is registered in MLflow as `pancreas-lesion-segmenter` v1; and a FastAPI `/predict` endpoint serves it (live smoke-tested, ~1 s/case).
- ✅ **Two pre-registered experiments, honestly rejected** — anatomy-aware auxiliary supervision (EXP-26) looked like a win at an intermediate checkpoint but was a null at convergence; the more-healthy-data specificity run (EXP-25) cleared specificity 17%→46% but missed the pre-set ≥90% detection floor (88%). Both rejected against bars set in advance, so the plain whole-box model stays the headline. The over-segmentation of small tumors remains the known weakness and the Week-5 / capstone lever (a milder healthy ratio + the autonomous localize→segment cascade).

*Every run is logged as a formal experiment (hypothesis → decision) in [`docs/experiments.md`](docs/experiments.md).*

---

## Repository structure

```
JHU-PanTS/
├── README.md              ← you are here (grader map)
├── CLAUDE.md              project state/decisions for AI agents
├── configs/               level45.yaml (the locked recipe as config)
├── week4/                 M4A1 deliverables: tuning/orchestration/deployment report + img/ (diagram, MLflow, eval, samples, endpoint)
├── week3/                 M3P1 deliverables: experiment report, slide deck, diagrams
├── week2/                 M2A1/M2P2 deliverables: report, EDA notebook, diagrams, run sheet
├── docs/                  graded docs (standup, audience notes, plan, schedule, ai-usage)
│                          + full design docs + experiments.md + metrics audit
├── ui/                    React + NiiVue static demo viewer (Week 5 build)
├── src/
│   ├── utils/             config, seed, paths
│   ├── data/             transforms (label compose, patch/whole-box), dataset
│   ├── models/           SegResNet + SuPreM transfer loader
│   ├── training/         losses, metrics, trainer helpers
│   └── inference/        sliding-window prediction, validation, post-processing
├── scripts/              build_manifest, create_splits, sanity_check_case, train,
│                         evaluate, audit_masks, make_clarity_splits, log_run_to_mlflow
└── outputs/              (git-ignored) manifest, splits, checkpoints, mlflow, figures
```

*(Raw data, model weights, and outputs are git-ignored and never committed — the dataset lives on an external drive.)*

## Design documentation (the full plan)

- [`docs/system-overview.md`](docs/system-overview.md) — the whole system on one page
- [`docs/architecture.md`](docs/architecture.md) — master design doc + scope ladder
- [`docs/data-pipeline.md`](docs/data-pipeline.md) — on-disk layout, manifest, splits
- [`docs/training.md`](docs/training.md) — the locked training recipe (model, loss, optimizer, stages)
- [`docs/experiments.md`](docs/experiments.md) — formal experiment log with hypotheses and decisions
- [`docs/experiment-tracking.md`](docs/experiment-tracking.md) — MLflow plan
- [`docs/ui.md`](docs/ui.md) — React + NiiVue front-end plan

## Running it (on Apple Silicon)

```bash
python3.12 -m venv .venv312 && source .venv312/bin/activate
pip install -r requirements.txt

python scripts/build_manifest.py          # scan dataset → outputs/manifest.csv
python scripts/create_splits.py           # patient-level, tumor-stratified splits
python scripts/sanity_check_case.py       # Week 1 milestone: 3-view overlays

# train (whole-box ROI, SuPreM transfer) then evaluate on the val set
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --max-iters 6000 --val-positive
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt --n-pos 20 --n-neg 20 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5 --sweep
```

The dataset path is set in `configs/level45.yaml` (`paths.pants_root`) or via the `PANTS_ROOT` env var — never hardcoded.

## Scope & roadmap

**Course (5 weeks):** Level 4.5 segmentation + CADe "possible tumor" flag + the scratch-vs-transfer comparison + the React/NiiVue UI. **Capstone (10 weeks):** an ROI localize→segment cascade, full-scale training on all 9,000 cases, Level 5 multi-structure, and submitting the model to JHU for external validation.

## Guardrails

Never commit raw data · split by patient not slice · full-volume sliding-window evaluation · report pancreas & lesion Dice separately · tumor-positive sampling · no clinical/diagnostic claims · config-driven pipeline.
