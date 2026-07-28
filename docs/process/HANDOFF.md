# HANDOFF — Start Here (for a new agent/session)

You are picking up an in-progress ML project. **Read `CLAUDE.md` first**, then this file. The `docs/` folder holds the full design; this sheet is the fast on-ramp.

## What this project is
3D pancreas-aware pancreatic **lesion segmentation** on the Johns Hopkins **PanTS** CT dataset (MONAI/PyTorch, Apple Silicon/MPS). Primary target **Level 4.5** (background / pancreas / lesion) + a CADe "there could be a tumor here" flag. **Segmentation tool, not a diagnosis.** 5-week solo course project; 10-week capstone extends the same codebase.

## Onboarding order (read these)
1. `CLAUDE.md` — locked decisions + current state (the source of truth).
2. `docs/system-overview.md` — the whole system in one page.
3. `docs/data-pipeline.md` — on-disk layout, manifest, splits (finalized against real files).
4. `docs/training.md` §0 — the locked training recipe (exact hyperparameters).
5. `docs/architecture.md` — master design + index; `docs/experiment-tracking.md` (MLflow); `docs/ui.md` (React+NiiVue).

## Current state
- **Planning: complete.** All decisions locked (see `CLAUDE.md`).
- **Data: on the external drive** at `/Volumes/JHU-PanTS/PanTS/data/` — 9,000 train (`ImageTr/`), 901 test (`ImageTe/`), all labels (`LabelAll/<id>/segmentations/*.nii.gz` + `combined_labels.nii.gz`), `metadata.xlsx`.
- **Model weights:** SuPreM SegResNet at `pretrained_weights/supervised_suprem_segresnet_2100.pth` (git-ignored).
- **Scaffold started:** `requirements.txt`, `.gitignore`, `configs/level45.yaml` (the recipe as config). Helper scripts done + tested: `scripts/peek_case.py`, `scripts/find_lesions.py`, `scripts/view3d.py`.

## Immediate next task (build order)
1. `src/utils/config.py` — load `configs/level45.yaml`; `src/utils/seed.py`; `src/utils/paths.py`.
2. `scripts/build_manifest.py` — scan the drive, pair CT↔masks, compute `has_lesion` + lesion volume, left-join `metadata.xlsx`. **Also answer: is one case == one patient?** (check metadata for a patient id).
3. `scripts/create_splits.py` — patient-level, tumor-stratified train/val split (test = official `ImageTe`). Save id-lists to `outputs/splits/`.
4. MONAI dataset + transforms (`src/data/`), then `scripts/sanity_check_case.py` → correct 3-view overlays (**Week 1 milestone**).
5. `src/models/` (SegResNet + SuPreM loader), `src/training/` (losses, metrics, trainer, MLflow) → **Stage 0 overfit gate** (train Dice > 0.95 on 1–2 cases).

## Hard constraints (guardrails)
Never commit raw data · split by **patient**, not slice · full-volume sliding-window eval (never patch-only) · report pancreas & lesion Dice **separately** · tumor-positive patch sampling required · no clinical/diagnostic claims · don't start Level 5 before 4.5 works · keep pipeline **config-driven** · data path via config, never hardcoded.

## Environment gotchas (Apple Silicon)
- **PyTorch MPS, not CUDA.** `device="mps"`; set `PYTORCH_ENABLE_MPS_FALLBACK=1`. Keep **fp32** initially (MPS autocast is partial). Avoid nnU-Net (CUDA-oriented).
- **macOS BSD `tar`** rejects the PanTS scripts' `--checkpoint` flag → extract with plain `tar -xzf`. Keep the drive connected + lid open + `caffeinate` during long ops.
- Data is on an **external drive**; a fresh agent's sandbox may not see `/Volumes/...` — real-data + MPS runs happen on Quinn's machine.

## Working rhythm
Agent authors code + unit-tests pure logic on **synthetic** data (can't reach the drive/MPS). Quinn runs on the real drive/MPS and reports errors back. Update `CLAUDE.md`/docs as each module lands.

## Transfer-learning specifics (confirm at code time)
Match SuPreM's **exact SegResNet config** (init_filters, blocks, norm) from the checkpoint keys so weights load; match SuPreM's **spacing** and **intensity normalization** on the transfer arm, or transfer benefit drops. Clean-ablation rule: plain `SegResNet` (NOT `SegResNetDS`, no deep supervision) for scratch-vs-transfer; a separate Track B may add deep supervision etc.
