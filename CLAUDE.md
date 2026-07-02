# CLAUDE.md — Agent Context

Context file so any AI session picks up this project correctly. Keep updated as things change.

## Project
3D pancreas-aware pancreatic lesion segmentation on the JHU **PanTS** dataset (MONAI/PyTorch). Primary target: **Level 4.5** (background / pancreas / lesion). Config-driven so Level 4 (lesion-only) and Level 5 (multi-structure) share one codebase. **Segmentation tool, not a diagnostic system** — no clinical claims.

## Owner / scope
Solo project (Quinn). Course: 5-week independent ML project, proposal → delivery (instructor-approved). Business framing: radiologist / imaging-annotator annotation-assist (accept/edit/reject proposed contours). **Capstone:** a follow-on 10-week project will extend this same codebase (ROI cascade, full-scale training, Level 5) — design for that now.

## Hardware & environment (important)
- **14" MacBook Pro, Apple M5 Pro** — 18-core CPU, **20-core GPU**, 16-core Neural Engine.
- **64 GB unified memory** (shared CPU/GPU — no separate VRAM limit; generous for 3D patches).
- **1 TB SSD** internal; dataset lives on an **external drive** (~340 GB), NOT on the laptop or in the repo.
- **Apple Silicon → PyTorch MPS backend, NOT CUDA.** Implications for tomorrow:
  - Use `device = "mps"`; some MONAI/PyTorch ops fall back to CPU on MPS (set `PYTORCH_ENABLE_MPS_FALLBACK=1`).
  - Mixed precision (`autocast`) support on MPS is partial — validate before relying on it; may keep fp32.
  - `nnU-Net` / heavy CUDA-only paths won't apply; stick to MONAI 3D U-Net / SegResNet.
  - Patch size is bounded by unified memory + MPS stability, not a fixed VRAM number — start moderate (e.g. 96×128×128) and tune.

## Hard constraints / guardrails
Never commit raw data · split by patient not slice · full-volume sliding-window inference for eval (not patch-only) · report pancreas & lesion Dice separately · tumor-positive patch sampling required · no clinical/diagnostic claims · don't start Level 5 before 4.5 works · keep pipeline config-driven · dataset on external drive, path via config not hardcoded.

## Key technical decisions (locked, 2026-06-30)
- **Scope:** segmentation (Level 4.5) + a derived **CADe detection wrapper** = "there could be a tumor here." No tumor-type call, no diagnosis. Tumor-type classification is a research-only stretch if core finishes early. Full design in `docs/architecture.md`.
- **Model:** SegResNet (MONAI) primary; Swin UNETR as optional later comparison.
- **Transfer model (LOCKED, 2nd-opinion verified):** fine-tune **SuPreM's SegResNet** (`supervised_suprem_segresnet_2100.pth`, ~4.7M params, AbdomenAtlas pretraining, same JHU lab). From-scratch SegResNet = baseline. **Two-track rule:** clean ablation uses plain checkpoint-compatible `SegResNet` (NOT `SegResNetDS`, no deep supervision/norm swap — would break weight loading + confound the comparison); a separate "Track B" practical model is free to add deep supervision etc. Fallback if it stalls = SuPreM U-Net, not Swin/nnU-Net. PanTS checkpoints (MedFormer/R-Super) = reference oracle only.
- **2nd-opinion refinements (adopted):** match SuPreM's input normalization; test wider HU window vs `[-100,300]`; harder negatives near pancreas; add NSD + per-case CC lesion sensitivity, `ignore_empty`; stitch sliding-window output on CPU (MPS memory); treat SuPreM repo as checkpoint-source-only (old deps). **Anatomy-context ablation** (add a few neighbor structures) is high-value: PanTS shows +10pp tumor Dice from richer anatomy labels.
- **Metrics:** report pancreas & lesion Dice separately; headline = patient-wise sensitivity + specificity (CADe). SOTA reference: tumor Dice ~0.53, P-sens ~80%, spec ~90% → lesion Dice ~0.35–0.50 is a respectable target.
- **Training recipe (LOCKED, 2026-07-01):** Track A starting recipe in `docs/training.md` §0 — SegResNet (init_filters=16, GroupNorm, match SuPreM), spacing 1.5³, HU [-100,300]→[0,1], ROI 96³, RandCropByPosNegLabel num_samples=4 pos:neg 2:1, DiceCELoss, AdamW wd 1e-5, LR 2e-4 scratch / 1e-4 transfer (freeze encoder 2-3 ep), warmup 2ep→cosine, fp32 on MPS, seed 42, 1 epoch=250 iters, val every 5 ep, best-by-lesion-Dice. Stage 0 overfit gate → Stage 1 pancreas → Stage 2 L4.5 → Stage 3 lesion-focus → Stage 4 sliding-window eval. Confirm SuPreM's exact config/spacing/normalization at code time.
- **UI (LOCKED, 2026-07-01):** **React + NiiVue** (WebGL NIfTI viewer) + Tailwind/shadcn — NOT Streamlit (Quinn dislikes the look). **Static-first:** pipeline pre-computes predictions (NIfTI + `results.json`); UI reads saved files, no backend for the demo. Live FastAPI inference = capstone stretch. Build in **Week 5** after the model works; `scripts/peek_case.py` PNGs are the fallback. Design in `docs/ui.md`.

## Design docs (the plan)
- `docs/architecture.md` — master design doc + index (scope ladder, 3D handling, model, transfer learning, metrics, capstone scope).
- `docs/training.md` — model/norm/deep-supervision, loss, AdamW+schedule, sampling, ROI cascade, training-time, checkpoint/resume.
- `docs/experiment-tracking.md` — MLflow (required): local setup, what to log, scratch-vs-transfer comparison.
- `docs/ui.md` — Streamlit: CADe summary + 3D mesh (marching cubes) + tri-planar viewer + mask export.
- `docs/data-pipeline.md` — **finalized against real files** (on-disk layout, manifest schema, label remapping per level, splits, dev subset).

## Current state (as of 2026-06-30, Week 1)
**Done:** Repo + docs scaffolded. Dataset verified incl. on-disk layout (sharded image tarballs + per-case label dirs + `metadata.xlsx`; partial download = labels + one ~34 GB shard). Proposal/schedule/pitch/logs drafted. **Full design captured** across architecture/training/experiment-tracking/ui docs. Decisions added: AdamW + cosine/warmup + differential LR; InstanceNorm + deep supervision; whole-body → single-stage ROI now / cascade for capstone; MLflow primary tracker; UI = slices + 3D mesh.

**Data acquisition COMPLETE (2026-07-01):** full PanTS Mini on the external drive at `/Volumes/JHU-PanTS/PanTS/data/` — **9,000 train images** (`ImageTr/`), **901 test images** (`ImageTe/`), all ~9,901 label sets (`LabelAll/<id>/segmentations/` + `combined_labels.nii.gz`), `metadata.xlsx`. 382 GiB used, 83 GiB free. Layout + manifest design finalized in `docs/data-pipeline.md`. (Gotcha for next time: macOS BSD `tar` rejects the scripts' `--checkpoint` flag → extract with plain `tar -xzf`; keep drive connected + lid open during long ops.)

**Open / to personalize:** proposal Sections 2 (Why) & 3 (Takeaway) need Quinn's voice. Confirm `Claude.md` vs `agent-plan.md` filename. Confirm on download: label filenames (tumor vs subtypes) + case==patient. Other open Qs in companion docs.

## Next session
Verify the downloaded files → finalize `docs/data-pipeline.md` → then **code scaffolding**: `configs/` (level4/45/5 YAML), `src/` (data, models, training, inference, evaluation, utils), `scripts/`, `requirements.txt`, `.gitignore`. Week 1 milestone: load one PanTS case from the external drive and save correct 3-view CT + pancreas + lesion overlays.
