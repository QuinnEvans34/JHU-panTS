# Neuro-data — 3D Pancreatic Lesion Segmentation (PanTS)

A 3D medical-image segmentation pipeline for **pancreas-aware pancreatic lesion segmentation** in abdominal CT, using the Johns Hopkins **PanTS** dataset with MONAI/PyTorch. The model takes a CT volume and predicts a voxel-wise mask of the pancreas and any pancreatic lesion. The primary target is **Level 4.5** (background / pancreas / lesion); the codebase is config-driven so it can scale to Level 4 (lesion-only) or Level 5 (multi-structure).

> **This is an image-segmentation project, not a diagnostic system.** A human reviews and edits every output; no clinical determination is made or claimed.

> **Status:** Week 1 — proposal & pitch drafted; code scaffold next.

## Business framing

**User:** a medical-imaging annotator / radiologist who must outline the pancreas and lesion on CT. **Action supported:** accept, edit, or reject the model's proposed contour instead of drawing from scratch — saving time and standardizing outlines, with a human always in the loop.

## Dataset

PanTS (JHU, NeurIPS 2025) — 36,390 CT volumes, voxel-wise masks for pancreatic tumor, pancreas subregions, and 24 surrounding structures. Open-source (CC-BY-NC-SA-4.0), static benchmark. Dev uses the ~346 GB Mini release on a local subset.
GitHub: <https://github.com/MrGiovanni/PanTS> · HF: <https://huggingface.co/datasets/BodyMaps/PanTSMini> · Paper: <https://arxiv.org/abs/2507.01291>

## Repository layout

```
Neuro-data/
├── README.md
└── docs/                       # Living project documents
    ├── proposal.md             # (M1A1) Full project proposal — 7 sections
    ├── schedule.md             # (M1A1) 5-week plan with behind-schedule signals
    ├── Claude.md               # (M1A1) Claude / AI usage + agent plan (living)
    ├── AI-usage.md             # (M1A1) Weekly AI-usage log (living)
    ├── standup-log.md          # (M1A2) Daily standup log (living)
    ├── pitch.md                # (M1P1) Pitch talking points + anticipated Q&A
    └── assignments/            # Course assignment briefs (reference)
        ├── M1A1-project-proposal.md
        ├── M1A2-daily-check-ins.md
        └── M1P1-project-pitch-and-defense.md
```

_Code scaffold (`configs/`, `src/`, `scripts/`, `data/`, `outputs/`) is added in Week 1–2 — see `docs/schedule.md`._

## Deliverables at a glance

| ID | Assignment | Points | Available until |
|----|-----------|--------|-----------------|
| M1P1 | Project Pitch & Defense | 30 | Jul 9 |
| M1A1 | Project Proposal | 25 | Jul 12 |
| M1A2 | Daily Check-Ins | 10 | Jul 11 (weekly) |

## Hard constraints (project guardrails)

Never commit raw dataset files · split by patient, never by slice · evaluate with full-volume sliding-window inference, not patches · report pancreas and lesion Dice separately · no clinical/diagnostic claims · don't start Level 5 before 4.5 works · tumor-positive patch sampling required · keep the pipeline config-driven.
