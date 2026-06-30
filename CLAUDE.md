# CLAUDE.md — Agent Context

Context file so any AI session picks up this project correctly. Keep updated as things change.

## Project
3D pancreas-aware pancreatic lesion segmentation on the JHU **PanTS** dataset (MONAI/PyTorch). Primary target: **Level 4.5** (background / pancreas / lesion). Config-driven so Level 4 (lesion-only) and Level 5 (multi-structure) share one codebase. **Segmentation tool, not a diagnostic system** — no clinical claims.

## Owner / scope
Solo project (Quinn). Course: 5-week independent ML project, proposal → delivery. Business framing: radiologist / imaging-annotator annotation-assist (accept/edit/reject proposed contours).

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

## Current state (as of 2026-06-29, Week 1)
**Done:** Repo scaffolded with docs. Assignment briefs saved (`docs/assignments/`). Dataset verified. Drafted: `proposal.md`, `schedule.md`, `pitch.md`, `Claude.md`, `AI-usage.md`, `standup-log.md`, README.

**Open / to personalize:** proposal Sections 2 (Why) & 3 (Takeaway) need Quinn's own voice. Confirm with instructor whether `Claude.md` and `agent-plan.md` should be separate files.

## Next session (tomorrow morning)
Pick up at **code scaffolding**: `configs/` (level4 / level45 / level5 YAML), `src/` (data, models, training, inference, evaluation, utils), `scripts/`, `requirements.txt`, `.gitignore`. Then Week 1 milestone: load one PanTS case from the external drive and save correct 3-view CT + pancreas + lesion overlays. Configs should reference the external-drive data path and target the MPS device.
