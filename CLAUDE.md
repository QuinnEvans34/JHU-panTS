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

**Pipeline code (2026-07-01):** `src/utils/` (config/seed/paths) + `scripts/build_manifest.py` + `scripts/create_splits.py` written, tested on synthetic, and RUN on real data. Real facts locked: **no patient id in metadata → each scan = its own case/patient** (case==patient RESOLVED); metadata join key = `PanTS ID`; **tumor prevalence 10.4%** (1,033/9,901); lesion volume 2–732,388 mm³ (median ~4,700); splits = **7,200 train / 1,800 val (both 9.8% tumor) / 901 official test (16.8%)** + dev subset 100 @ 50%. Manifest → `outputs/manifest.csv` (29 cols); splits → `outputs/splits/`.

**Data pipeline VALIDATED end-to-end (2026-07-01):** `src/data/transforms.py` + `dataset.py` written; `sanity_check_case.py` RAN on real case PanTS_00001070 and PASSED (**Week 1 milestone hit**) — resampled 190×134×131 @1.5mm, intensities [0,1], label {0=bg,1=panc,2=lesion} with lesion ~0.04% of volume, 96³ patches with 3/4 containing lesion (pos sampling works), overlays correct. Data pipeline (manifest→splits→transforms→patches) DONE.

**Model + training DONE + STAGE 0 VALIDATED (2026-07-03):** `src/models/segresnet.py` (SuPreM config matched: init_filters=16, GroupNorm num_groups=8, blocks (1,2,2,4)/(1,1,1); loader strips `module.`, unwraps `net`, re-inits 32→3 head), `src/training/` (losses/metrics/trainer), `scripts/train.py`, `scripts/inspect_checkpoint.py`. Overfit run: **pancreas Dice 0→0.888, loss 1.87→0.54 — pipeline proven end-to-end**, MLflow logging. **Env moved to Python 3.12 venv (`.venv312`)** — 3.14 broke mlflow install; 3.12 fixes it. **MPS ~0.29 it/s (~3.4s/step) — slow; course stays on dev subset.** **Lesion Dice stuck at 0** (0.04% class ignored under the loss) → set `loss.include_background: false`; next lever DiceFocal. Fixes en route: GroupNorm needs num_groups tuple; SpatialPadd (some scans <96 deep); CacheDataset for speed; flat LR + pancreas-based gate for overfit.

**STAGE 0 PASSED + LESION LEARNS (2026-07-03):** with `loss.include_background: false` + `--positive` overfit (2 tumor cases), **lesion Dice climbed 0→~0.7** and pancreas learned too — the model can fit both classes. Key learning: earlier lesion=0.000 was because the first dev_subset cases were tumor-FREE (metric NaN printed as 0); `train.py` now prints `n/a` vs real 0, and `--positive` draws overfit cases from tumor-positive only. Dynamics: lesion learns later than pancreas; classes compete (include_bg=False); train-crop Dice is noisy. **Validation added:** `src/inference/sliding_window.py` (`predict_volume` + `validate`), wired into `train.py` (`--val-limit/--val-every`, best.pt by val lesion Dice).

**Next:** first real Stage 2 run — SuPreM transfer on dev_subset (100) with held-out validation (`--split dev_subset --val-limit 8 --val-every 1000`), ~6h on MPS. Then scratch-vs-transfer ablation, tune, scale up (capstone). MPS ~0.29 it/s.

**Open / to personalize:** proposal Sections 2 (Why) & 3 (Takeaway) need Quinn's voice. Confirm `Claude.md` vs `agent-plan.md` filename.

## Next session
Verify the downloaded files → finalize `docs/data-pipeline.md` → then **code scaffolding**: `configs/` (level4/45/5 YAML), `src/` (data, models, training, inference, evaluation, utils), `scripts/`, `requirements.txt`, `.gitignore`. Week 1 milestone: load one PanTS case from the external drive and save correct 3-view CT + pancreas + lesion overlays.
