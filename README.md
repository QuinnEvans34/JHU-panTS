# JHU-PanTS — 3D Pancreas-Aware Pancreatic Lesion Segmentation

A 3D deep-learning pipeline that takes an abdominal CT scan, segments the **pancreas** and any **pancreatic lesion**, and flags *"there could be a tumor here."* Built on the Johns Hopkins **PanTS** dataset with MONAI/PyTorch, running on Apple Silicon (MPS).

> **This is an image-segmentation / annotation-assist tool, not a diagnostic system.** A human radiologist reviews and edits every output; no clinical determination is made or claimed.

---

## 📌 Graded deliverables — where to find everything

*(This table is the grader's map. Most recent week first.)*

### Week 3 (current) — M3P1: Experiment Review & Model Selection

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M3P1 — Presenter** | ML experimentation report (features, experiment comparison, model selection, plan status) | [`week3/ml-experimentation-report.md`](week3/ml-experimentation-report.md) |
| M3P1 — *presentation* | Slide deck (10-min talk) | [`week3/experiment-review-slides.pptx`](week3/experiment-review-slides.pptx) · [PDF](week3/experiment-review-slides.pdf) |
| **M3P1 — Audience** | Audience notes on peers' presentations | [`docs/audience-notes-week3.md`](docs/audience-notes-week3.md) |
| M3P1 — *experiment log* | Every run as a formal experiment (hypothesis → decision), EXP-01 → EXP-19 | [`docs/experiments.md`](docs/experiments.md) |
| M3P1 — *revised plan (Section 5)* | Where the project stands vs the 5-week plan | [`docs/implementation-plan.md`](docs/implementation-plan.md) |
| M3P1 — *AI docs (Section 6)* | AI context file + weekly usage log | [`CLAUDE.md`](CLAUDE.md) · [`docs/ai-usage-log.md`](docs/ai-usage-log.md) |
| M3P1 — *metrics audit* | Self + independent-AI audit of the scoring (no leakage; ROI-leak finding) | [`docs/codex-metrics-audit.md`](docs/codex-metrics-audit.md) |

**Supporting Week 3 work:** [`week3/diagrams/`](week3/diagrams/) (presentation diagrams: whole-box vs patches, the input array, metrics) · daily standups in [`docs/standup-log.md`](docs/standup-log.md).

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

## Current status (Week 3 — complete)

- ✅ **Data understood** — EDA built from the real 9,901-case manifest: 10.4% tumor prevalence, lesion volume spanning five orders of magnitude, extreme geometry heterogeneity (8 to 1,000+ slices).
- ✅ **Pipeline validated** — Stage 0 overfit gate passed; the ingestion → resample → patch → model path is proven end to end.
- ✅ **Over-prediction diagnosed and fixed** — first eval was pancreas Dice 0.72 / lesion 0.17 with only 8% specificity. A **whole-box ROI** change (feed the entire pancreas box as one cube) lifted specificity to 55% and became the winning recipe.
- ✅ **Data proven to be the lever (Week 3 headline)** — four recipe knobs (sampling, loss, field of view, resolution) were all nulls on tumor accuracy; scaling the tumor data was the only thing that moved it. Holding the whole-box recipe fixed and training on all 1,412 available cases lifted **lesion Dice 0.26 → 0.528** (≈ the ~0.53 published reference), **pancreas Dice 0.837**, and **90% per-case detection**. This is the selected model.
- ✅ **Metrics audited** — self + independent-AI pass confirmed the arithmetic and found no train/validation leakage; one honest finding (the ROI leaks lesion extent, making lesion Dice an upper bound) is documented and a control (EXP-19) is queued.
- 🔄 **Week 4** — a longer run on the max-data set, the pancreas-only de-leak control, and a final held-out test pass; the autonomous localize→segment cascade is the capstone direction.

*Every run is logged as a formal experiment (hypothesis → decision) in [`docs/experiments.md`](docs/experiments.md).*

---

## Repository structure

```
JHU-PanTS/
├── README.md              ← you are here (grader map)
├── CLAUDE.md              project state/decisions for AI agents
├── configs/               level45.yaml (the locked recipe as config)
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
