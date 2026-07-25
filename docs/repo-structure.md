# Repository Structure & Training Walkthrough

A map of every part of the repo — where files live, what they do, and (most importantly) **how a training run actually turns CT scans into a model**. Written so I can explain any file and the end-to-end pipeline in an interview.

---

## 1. The 60-second mental model

The project has three phases, and the repo is organized around them:

1. **Data prep** — scan the dataset on the external drive, build a `manifest.csv` (one row per case with file paths + metadata), and carve patient-level train/val/test splits. (`scripts/build_manifest.py`, `scripts/create_splits.py`)
2. **Training** — run `scripts/train.py`, which loads the config, streams cases through a preprocessing pipeline, fine-tunes a SegResNet from SuPreM weights, and writes out model checkpoints (`.pt` files). (`scripts/train.py` + everything in `src/`)
3. **Inference / evaluation / UI** — score a checkpoint honestly (`scripts/evaluate.py`, `analyze_cases.py`, `cascade_eval.py`), export a case for the viewer (`scripts/export_case.py`), and view it in the React + NiiVue app (`ui/`).

**Training is not magic.** One terminal command kicks off a fixed pipeline: config → resolve file paths → build a dataset of preprocessed 3D cubes → load a pretrained network → loop (forward, compute loss, backpropagate, update weights) for N steps → periodically check validation accuracy → save the best weights to a `.pt` file. That `.pt` file *is* the model. Section 3 traces this step by step.

---

## 2. Where things live (data vs. code vs. outputs)

| Thing | Location | In git? | Notes |
|---|---|---|---|
| Raw dataset (CT + label masks, metadata.xlsx) | **External drive** `/Volumes/JHU-PanTS/PanTS/data/` | No (never) | Path set in the config, overridable via `PANTS_ROOT` env var |
| Source code | `src/`, `scripts/` | Yes | The pipeline |
| Config (the "recipe") | `configs/level45.yaml` | Yes | Every knob: model, preprocessing, loss, optimizer |
| Manifest + splits | `outputs/manifest.csv`, `outputs/splits/*.txt` | No (git-ignored) | Derived from the dataset |
| Preprocessing cache | `outputs/cache/` (internal SSD) | No | Speeds up repeated epochs |
| Model checkpoints | `outputs/checkpoints/pants-level45/` | No (too large) | `best.pt`, `last.pt`, per-run archives |
| Experiment tracking DB | `outputs/mlflow.db` (local SQLite) | No | Metrics/params for every run |
| UI | `ui/` | Yes | React + NiiVue viewer |
| Docs | `docs/`, `README.md`, `CLAUDE.md` | Yes | Plan, experiments log, AI usage, this file |

Rule of thumb: **code and config are committed; data, caches, checkpoints, and the MLflow DB are git-ignored** (they live on the drive / SSD and are regenerated).

---

## 3. How a training run actually works (end-to-end)

When I run, e.g.:

```
python scripts/train.py --split scaledmax_clean --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --loss tversky_focal --tversky-alpha 0.6 --max-iters 24000 --val-limit 20 --val-positive
```

here is exactly what happens, and which file does each part:

1. **Load the recipe.** `train.py` reads `configs/level45.yaml` via `src/utils/config.py` (`load_config`), then applies the command-line overrides (patch size, spacing, whole-box, loss, etc.) on top of it. The config is the single source of truth for every setting.
2. **Resolve paths.** `src/utils/paths.py` turns the config into concrete locations — where the dataset lives on the drive, where `manifest.csv` and the split files are, where checkpoints go.
3. **Seed everything** (`src/utils/seed.py`, seed 42) so runs are reproducible.
4. **Leakage guard.** `train.py` asserts the chosen training split shares **zero** cases with `val.txt`/`test.txt` and aborts if it doesn't. (This is the guard I added after the leakage bug.)
5. **Build the dataset.** `src/data/dataset.py` (`get_dataset`):
   - `build_records` reads `manifest.csv` and, for the case IDs in the chosen split, gathers each case's `ct_path`, `pancreas_path`, `lesion_path`.
   - Each case is fed through the **preprocessing pipeline** in `src/data/transforms.py` (`build_transforms`): load the CT + masks → merge the masks into one label (pancreas=1, lesion=2, `ComposeLabeld`) → reorient to RAS → **crop to the pancreas bounding box** → resample to 1.5mm → window HU to [0,1] → **resize the whole box into one 128³ cube** (the "whole-box" idea) → light augmentation (flips/rotations/intensity).
   - It's wrapped in a `CacheDataset` (RAM) or `PersistentDataset` (disk cache) so the expensive preprocessing runs once and is reused.
6. **Build the model.** `src/models/segresnet.py` (`build_model`) creates a MONAI **SegResNet** matched to the SuPreM config; `load_suprem` loads the pretrained weights and **re-initializes the final layer from 32 classes to our 3** (bg/pancreas/lesion). For a transfer run the encoder is frozen for a short warm-up, then unfrozen.
7. **Optimizer + schedule + loss.** `src/training/trainer.py` builds **AdamW** and a warmup→cosine learning-rate schedule; `src/training/losses.py` (`build_loss`) builds the loss (DiceFocal by default, or Tversky/Tversky-Focal via the flags).
8. **The training loop** (in `train.py`): for each step from `start` to `total_iters`:
   - pull a batch (one or a few 128³ cubes), run it **forward** through the network to get predictions,
   - compute the **loss** (how wrong the prediction is vs. the ground-truth mask),
   - **backpropagate** and take an **optimizer step** (nudge the weights to reduce the loss), advance the LR schedule,
   - log train loss + Dice to **MLflow** (`outputs/mlflow.db`).
9. **Validation, periodically** (every `--val-every` steps): `src/inference/sliding_window.py` (`validate`) runs the model over held-out validation cases with **full-volume sliding-window inference** and reports pancreas + lesion Dice (`src/training/metrics.py`, `DiceEvaluator`). If the lesion Dice is a new best, save `best.pt`.
10. **Checkpoints + archive.** `best.pt` (best validation) and `last.pt` (latest) are written to `outputs/checkpoints/pants-level45/`, **and** an immutable per-run copy is archived to `outputs/checkpoints/pants-level45/runs/<run_name>__<timestamp>/`, plus a row in `run_ledger.csv`. That archive is why a good model can't be silently overwritten.

**The output of all this is a `.pt` file** — a dictionary of the network's learned weights. That file is "the model." Evaluation and the UI just load it and run it forward on new scans.

---

## 4. `src/` — the pipeline library (imported by the scripts)

```
src/
├── utils/
│   ├── config.py      Load configs/level45.yaml; resolve paths; PANTS_ROOT env override.
│   ├── paths.py       Turn the config into concrete dataset/output file paths (Path objects).
│   └── seed.py        Seed Python/NumPy/torch/MPS for reproducible runs (seed 42).
├── data/
│   ├── transforms.py  The preprocessing pipeline: compose the 3-class label, orient, crop to the
│   │                  pancreas box, resample to 1.5mm, scale HU, whole-box resize to 128³, augment.
│   └── dataset.py     Build the MONAI dataset from manifest + split id-list; RAM/disk caching;
│                      the cache "tag" that keeps different recipes from colliding.
├── models/
│   └── segresnet.py   Build the SegResNet; load SuPreM pretrained weights + re-init the 3-class head.
├── training/
│   ├── losses.py      build_loss: DiceFocal (default) | DiceCE | Tversky | Tversky-Focal.
│   ├── metrics.py     DiceEvaluator: per-class Dice (pancreas + lesion reported separately).
│   └── trainer.py     Device (MPS) select, AdamW optimizer, warmup→cosine scheduler,
│                      save_checkpoint / load_checkpoint (+ the hardened resume).
└── inference/
    ├── sliding_window.py  Full-volume sliding-window inference; the in-loop validate(); flip-TTA.
    └── postprocess.py     CADe cleanup: largest-connected-component, small-blob removal,
                           lesion-must-be-near-pancreas anatomical constraint.
```

---

## 5. `scripts/` — the things I actually run (entry points)

Run roughly in this order across the project:

| Script | What it does | When |
|---|---|---|
| `build_manifest.py` | Scan the dataset, write `outputs/manifest.csv` (one row per case: paths + metadata + has_lesion). | Once, up front |
| `create_splits.py` | Carve patient-level, tumor-stratified `train/val/test.txt`. | Once, up front |
| `make_scaled_split.py` | Build tumor-enriched training splits (e.g. `scaledmax_clean`) sampled ONLY from `train.txt` (+ leakage assert). | Per data experiment |
| `make_clarity_splits.py` / `make_contrast_splits.py` | Build the clarity-curriculum / contrast-phase experiment splits. | For those experiments |
| `audit_masks.py` | Data-quality audit: flag empty/tiny/oversized pancreas masks; recover from head/body/tail subregions; write a clean split. | Data-quality checks |
| `sanity_check_case.py` | Run one case through the pipeline and save 3-view overlays — proves preprocessing is correct. | Milestone / debugging |
| **`train.py`** | **The trainer** (Section 3). Produces the model checkpoint. | The main event |
| `evaluate.py` | Score a checkpoint: lesion/pancreas Dice on tumor-positive cases + specificity on tumor-free + threshold sweep. | After each train |
| `analyze_cases.py` | Per-case breakdown: detection sensitivity, Dice by tumor size and by contrast phase. | After each train |
| `cascade_eval.py` | The autonomous localize-then-segment pipeline + the millimeter containment audit + localizer diagnostic. | Cascade / reliability work |
| `export_case.py` | Turn a prediction into the files the UI reads (NIfTI + 3D meshes + results.json). | For the demo |
| `log_run_to_mlflow.py` | Re-log a run to MLflow if it was trained in the no-MLflow environment. | Housekeeping |
| `inspect_checkpoint.py` | Print a checkpoint's tensor shapes (used to match our SegResNet to SuPreM). | Debugging |
| `peek_case.py` / `find_lesions.py` / `view3d.py` | Quick data-exploration helpers (slice PNGs, find tumor cases, 3D peek). | Ad-hoc exploration |

---

## 6. `configs/level45.yaml` — the recipe

One YAML file holding every setting: dataset paths, label mapping, split fractions, preprocessing (spacing 1.5mm, HU window, whole-box), sampling, the SegResNet architecture, transfer settings, the loss, the AdamW optimizer + schedule, the training loop length, validation, and inference/post-processing. Scripts read this so the pipeline is config-driven — I change behavior by editing the YAML or passing a `--flag` override, not by editing code.

---

## 7. `outputs/` — everything the pipeline produces (git-ignored)

```
outputs/
├── manifest.csv                    one row per case (paths + metadata)
├── splits/                         train.txt, val.txt, test.txt, scaledmax_clean.txt, ...
├── cache/                          preprocessed-tensor disk cache (internal SSD)
├── mlflow.db                       local MLflow SQLite DB (every run's metrics + params)
├── mask_audit.csv                  output of audit_masks.py
└── checkpoints/pants-level45/
    ├── best.pt, last.pt            current best / latest model weights
    ├── run_ledger.csv              one row per run (never overwritten)
    └── runs/<run_name>__<stamp>/   immutable per-run archive: best.pt + last.pt + run_info.txt
```

---

## 8. `ui/` — the business-facing viewer (React + NiiVue)

Static-first web app: the pipeline pre-computes predictions (`export_case.py`), and the UI reads those saved files — no live backend for the demo. `ui/src/App.jsx` is the viewer (tri-planar CT + pancreas/lesion overlays, rotatable 3D mesh, prediction-vs-ground-truth toggle, a plain-language "possible lesion" summary). Standard Vite/React project (`package.json`, `vite.config.js`, `index.html`).

---

## 9. Docs & root files

- `README.md` — the grader map (links every deliverable) + project overview.
- `CLAUDE.md` — living project-state/context file (decisions, current status).
- `docs/experiments.md` — every training run as a formal experiment (hypothesis → result → decision).
- `docs/implementation-plan.md` — the 5-week plan + status; `docs/ai-usage-log.md` — how AI was used.
- `docs/data-pipeline.md`, `docs/training.md`, `docs/architecture.md`, `docs/ui.md` — the design docs.
- `docs/codex-audit-week4.md`, `docs/codex-metrics-audit.md` — the independent code/metrics audits.
- `requirements.txt` — Python dependencies. `AGENTS.md` / `HANDOFF.md` / `PASSOFF.md` — handoff notes.

---

## 10. Interview cheat-sheet (likely questions, crisp answers)

- **"Where does training happen?"** Locally, on the MacBook's Apple-Silicon GPU (MPS backend, not CUDA), by running `scripts/train.py`. It produces a `.pt` checkpoint under `outputs/checkpoints/`.
- **"What actually is the model?"** A MONAI SegResNet (a 3D U-Net-style CNN) whose learned weights are saved in a `.pt` file. We fine-tune it from SuPreM pretrained weights rather than training from scratch.
- **"How does a scan become a prediction?"** Load CT → crop to the pancreas box → resample to a 128³ cube at 1.5mm → the network outputs a per-voxel class (bg / pancreas / lesion) → post-process → that mask is the prediction.
- **"How do you avoid data leakage?"** Splits are patient-level and stratified; the trainer asserts the training split is disjoint from val/test at startup; the official test set is untouched until the end.
- **"How do you track experiments?"** MLflow (local SQLite at `outputs/mlflow.db`) logs metrics/params for every run, and `docs/experiments.md` records each as a hypothesis → result → decision.
- **"What's the config for?"** `configs/level45.yaml` holds the whole recipe; the pipeline is config-driven so experiments are one flag or one YAML edit, not code changes.
