# JHU-PanTS — 3D Pancreas-Aware Pancreatic Lesion Segmentation

A 3D deep-learning pipeline that takes an abdominal CT scan, segments the **pancreas** and any **pancreatic lesion**, and flags *"there could be a tumor here."* Built on the Johns Hopkins **PanTS** dataset with MONAI/PyTorch, running on Apple Silicon (MPS).

> **This is an image-segmentation / annotation-assist tool, not a diagnostic system.** A human radiologist reviews and edits every output; no clinical determination is made or claimed.

---

## 📌 Graded deliverables — where to find everything

*(Everything submitted for grading lives in the `docs/` folder. This table is the grader's map.)*

| Assignment | Deliverable | Location |
|-----------|-------------|----------|
| **M1A1 — Project Proposal** | Proposal (all 7 sections) | [`docs/proposal.md`](docs/proposal.md) |
| M1A1 | 5-week schedule | [`docs/schedule.md`](docs/schedule.md) |
| M1A1 | Claude / AI usage plan | [`docs/Claude.md`](docs/Claude.md) |
| M1A1 | Weekly AI-usage log | [`docs/AI-usage.md`](docs/AI-usage.md) |
| M1A1 — *Agent plan criterion* | Agent operating guide + AI-vs-manual task split | [`docs/agent-plan.md`](docs/agent-plan.md) |
| **M1A2 — Daily Check-Ins** | Daily standup log (Mon–Fri + Week 1 retrospective) | [`docs/standup-log.md`](docs/standup-log.md) |
| **M1P1 — Pitch & Defense** | Pitch talking points + anticipated Q&A | [`docs/pitch.md`](docs/pitch.md) |
| M1P1 — *Audience deliverable* | Audience notes on peers' pitches | [`docs/audience-notes-week1.md`](docs/audience-notes-week1.md) |

**Supporting context:** [`CLAUDE.md`](CLAUDE.md) (project state/decisions an AI agent reads) · [`HANDOFF.md`](HANDOFF.md) (session on-ramp) · full technical design in `docs/` (see below).

---

## What the project is

**Problem & user.** Radiologists and imaging annotators must hand-trace the pancreas and any tumor on 3D CT — slow, tedious work on a hard-to-see organ. The user is a **radiologist / imaging annotator** who, for each scan, **accepts, edits, or rejects** an automatically proposed outline instead of drawing it from scratch.

**Dataset.** [PanTS](https://github.com/MrGiovanni/PanTS) (Johns Hopkins, NeurIPS 2025) — open-source (CC-BY-NC-SA), a static benchmark. The public Mini release is 9,000 training + 901 test CT volumes with voxel-wise masks for the pancreas, its subregions, the lesion, and ~28 surrounding structures. Real tumor prevalence: **10.4%**.

**ML approach.** Supervised **3D semantic segmentation** (background / pancreas / lesion) with a **SegResNet** (MONAI), fine-tuned from **SuPreM** pretrained weights and compared against a from-scratch baseline. Extreme class imbalance (lesion ≈ 0.04% of a volume) is handled with Dice-based loss + tumor-positive patch sampling. Evaluation is full-volume sliding-window inference; **pancreas and lesion Dice are reported separately**, plus patient-wise sensitivity/specificity (the CADe "possible tumor" story).

**Business-facing layer.** A planned **React + NiiVue** web app: tri-planar CT with pancreas/lesion overlays, a rotatable 3D view, a "possible tumor" summary (location, volume, confidence), and mask export for editing in a real tool.

---

## Current status (Week 1 — complete)

- ✅ **Data acquired & verified** — full PanTS Mini (~410 GB) on an external drive; manifest + patient-level, tumor-stratified splits built (7,200 train / 1,800 val / 901 official test).
- ✅ **Pipeline validated end-to-end** — a real case runs through preprocessing → correct 3-view overlays (the Week 1 milestone).
- ✅ **Working model** — the SegResNet + SuPreM-transfer training loop runs on MPS with MLflow logging. **Stage 0 (overfit) passed:** the model fits both the pancreas (~0.89 Dice) and the lesion (~0.7 Dice), confirming it can detect tumors.
- 🔄 **In progress** — first real training run on the dev subset with held-out validation; next up is the scratch-vs-transfer comparison and tuning.

---

## Repository structure

```
JHU-PanTS/
├── README.md              ← you are here
├── CLAUDE.md              project context/state for AI agents
├── HANDOFF.md            fresh-session on-ramp
├── requirements.txt  ·  .gitignore
├── configs/              level45.yaml (the locked recipe as config)
├── docs/                 all graded deliverables + full design docs
├── src/
│   ├── utils/            config, seed, paths
│   ├── data/             transforms, dataset (label compose, patch sampling)
│   ├── models/           SegResNet + SuPreM transfer loader
│   ├── training/         losses, metrics, trainer helpers
│   └── inference/        sliding-window prediction + validation
├── scripts/              build_manifest, create_splits, sanity_check_case,
│                         train, inspect_checkpoint, peek_case, find_lesions, view3d
└── outputs/              (git-ignored) manifest, splits, checkpoints, mlflow, figures
```

*(Raw data, model weights, and outputs are git-ignored and never committed — the dataset lives on an external drive.)*

## Design documentation (the full plan)

- [`docs/system-overview.md`](docs/system-overview.md) — the whole system on one page
- [`docs/architecture.md`](docs/architecture.md) — master design doc + scope ladder
- [`docs/data-pipeline.md`](docs/data-pipeline.md) — on-disk layout, manifest, splits (finalized against real files)
- [`docs/training.md`](docs/training.md) — the locked training recipe (model, loss, optimizer, stages)
- [`docs/experiment-tracking.md`](docs/experiment-tracking.md) — MLflow plan
- [`docs/ui.md`](docs/ui.md) — React + NiiVue front-end plan

## Running it (on Apple Silicon)

```bash
python3.12 -m venv .venv312 && source .venv312/bin/activate
pip install -r requirements.txt

python scripts/build_manifest.py          # scan dataset → outputs/manifest.csv
python scripts/create_splits.py           # patient-level, tumor-stratified splits
python scripts/sanity_check_case.py       # Week 1 milestone: 3-view overlays
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py --overfit 2 --positive --scratch   # Stage 0 gate
```

The dataset path is set in `configs/level45.yaml` (`paths.pants_root`) or via the `PANTS_ROOT` env var — never hardcoded.

## Scope & roadmap

**Course (5 weeks):** Level 4.5 segmentation + CADe "possible tumor" flag + the scratch-vs-transfer comparison + the React/NiiVue UI. **Capstone (10 weeks):** an ROI localize→segment cascade, full-scale training on all 9,000 cases, Level 5 multi-structure, and submitting the model to JHU for external out-of-distribution validation.

## Guardrails

Never commit raw data · split by patient not slice · full-volume sliding-window evaluation · report pancreas & lesion Dice separately · tumor-positive sampling · no clinical/diagnostic claims · config-driven pipeline.
