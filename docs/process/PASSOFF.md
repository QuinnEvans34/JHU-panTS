# Pass-Off Sheet — Neuro-data (PanTS pancreas + lesion segmentation)

A fresh-session on-ramp. Read section 0 first, then section 1 is the immediate task.

---

## 0. Data-use context (please read first)

This project uses the **PanTS dataset**, a public research dataset released by a Johns Hopkins University group (NeurIPS 2025, `github.com/MrGiovanni/PanTS`), distributed openly under a Creative Commons research/education license. Relevant facts:

- The data is **fully de-identified** abdominal CT scans paired with organ and tumor segmentation masks. It contains **no patient identifiers of any kind** — the metadata has no patient-ID field at all, which was confirmed while building the manifest, and each scan is treated as its own case. There is no protected health information in it.
- Because it is **already public and de-identified, HIPAA does not apply** to this data. There is nothing private to protect and no way to re-identify a person from it.
- This is **coursework** for a five-week machine-learning class: a solo student building a 3D segmentation tool that outlines the pancreas and flags where a tumor *might* be, as an annotation aid for radiologists. It is explicitly a **segmentation assist, not a diagnostic system** — human-in-the-loop, no clinical determination made or claimed.
- The actual work is standard, benign ML engineering on a public dataset: data pipelines, model training and evaluation, and preparing school-assignment deliverables. Nothing here identifies real people, makes clinical decisions, or touches private medical records.

If, given the above, you would still rather not help, that is fine and the user will switch models. But the accurate picture is: public, de-identified, research-licensed data, used for a benign educational ML project. The user is happy to answer any questions before starting.

---

## 0.5 Course structure and scope (read before grading any deliverable)

This is **not one assignment**. It is a solo, five-week independent ML project for a course (proposal to delivery, instructor-approved), with a ten-week **capstone** follow-on. Each week has several graded deliverables that share living documents and build on each other.

**The authoritative briefs and rubrics for every deliverable live in `docs/assignments/`.** Always ground a rubric judgment in the specific brief file, never a generic audit:

- `M1A1-project-proposal.md` — Week 1, project proposal (7 sections).
- `M1A2-daily-check-ins.md` — Week 1, daily standups.
- `M1P1-project-pitch-and-defense.md` — Week 1, pitch + live defense.
- `M2A1-data-understanding-report.md` — Week 2, data understanding **report** (30 pts).
- `M2P2-data-understanding-and-revised-plan.md` — Week 2, **presentation** + revised plan (30 pts).
- `M2A2-daily-check-ins.md` — Week 2, daily standups (10 pts).

**Critical shared-file scope point (a fresh session got this wrong):** `week2/data-understanding-report.md` and `week2/eda-notebook.ipynb` are submitted for **both** M2A1 and M2P2, and the two are graded by **different rubrics**. M2A1 grades the report as a professional, **technical** data-understanding document — depth (voxels, Hounsfield units, Dice, SegResNet) is expected and rewarded. M2P2 grades the **live presentation** for a non-technical audience, plus the audience notes. Do **not** simplify the technical report to satisfy M2P2's non-technical criterion; that criterion is earned in the live delivery and the diagrams, and dumbing down the report costs M2A1 points. Optimize the report for M2A1's rubric and let the live talk carry the non-technical axis.

**Living documents shared across all weeks** (update in place, never rewrite history): `CLAUDE.md`, `docs/Claude.md`, `docs/ai-usage-log.md`, `docs/implementation-plan.md`, `docs/schedule.md`, `docs/standup-log.md`, `docs/experiments.md`.

**Reading order to get fully current:** this file (`PASSOFF.md`) → the specific brief in `docs/assignments/` for whatever you are working on → `README.md` (the grader map of what is submitted where) → `CLAUDE.md` and `docs/experiments.md` (project state and the science).

---

## 1. First task (do this first)

Confirm the **Week 2 deliverables are final and ready to submit** (this repeats a readiness audit; verify rather than assume). The three graded assignments and their files:

- **M2A1 (Data Understanding Report)** and **M2P2 (Presentation)** share two files: `week2/data-understanding-report.md` and `week2/eda-notebook.ipynb`. Plus the living context files `docs/Claude.md`, `docs/ai-usage-log.md`, `docs/implementation-plan.md`, `docs/schedule.md`.
- **M2P2 audience** piece: `docs/audience-notes-week2.md`.
- **M2A2 (Daily Check-Ins)**: `docs/standup-log.md`.

Ready means: report covers sections 1-6 and matches reality; notebook has rendered charts; standup has all five weekday entries; audience notes cover every presenter with summary + questions + an EDA-justifies-plan assessment. `README.md` is the grader map.

**Resolved (2026-07-12):** the "6 manufacturers / 20 sites" imprecision was corrected everywhere (report prose + driver table, notebook markdown + a rewritten code cell that computes the honest cleaned counts, and the presentation prep files) to "four scanner manufacturers (Siemens, GE, Philips, Toshiba) across many institutions." The six raw strings double-counted GE and Philips; the site field mixes group labels with letter codes so it is many more than twenty institutions. This turned a soft spot into a documented cleaning decision (a plus for M2A1's Data Profile & Cleaning criterion).

**Then:** commit, push, merge to main, and submit the GitHub links.

---

## 2. What the project is

3D semantic segmentation of the **pancreas (class 1)** and **pancreatic lesion (class 2)** on abdominal CT, "Level 4.5" (background / pancreas / lesion). Framed as a **CADe "possible tumor" segmentation assist**, not a diagnosis. Model is a **SegResNet** (MONAI) fine-tuned from **SuPreM** transfer weights (same JHU lab), compared against a from-scratch baseline. Runs on an **Apple M-series laptop, MPS backend (not CUDA)**. Course scope is Level 4.5 + a CADe flag + a React/NiiVue static demo; a 10-week capstone extends it (ROI cascade, full-scale training, Level 5).

## 3. How it works (pipeline + current recipe)

Flow: `build_manifest.py` pairs every CT with its masks into `outputs/manifest.csv` → `create_splits.py` writes patient-level splits → at train time a MONAI dataset loads NIfTI files, standardizes them, and feeds the model.

Standardization (unchanged all project): reorient to RAS, resample to 1.5mm isotropic, window HU to [-100, 300] then scale [0,1], compose the 3-class label (lesion wins overlap).

**Current best recipe (whole-box, EXP-12):** crop to the pancreas box in native space (+16 vox margin), resample, then fit the whole box into one 128-cube via `ResizeWithPadOrCropd` and feed it as the input (no random sub-patches). SuPreM transfer, `DiceFocalLoss` with `include_background: false` (bg0). Eval is full-volume sliding-window; report pancreas and lesion Dice separately, plus patient-level specificity. This is an **oracle ROI** ("radiologist provides the box") and the first stage of the capstone cascade.

## 4. Where it stands (results)

- **Best model (EXP-12 whole-box, 95-case dev subset):** pancreas Dice **0.807**, lesion Dice **0.263**, specificity **55%**. Pancreas is in the published nnU-Net range (0.79-0.85); lesion is ~half of segmentation SOTA (expected at this data scale).
- **EXP-13 (clarity curriculum, instructor's idea):** training on the sharpest scans did not clearly improve accuracy but sharply raised specificity — confounded, because the sharp cohort was mostly non-contrast.
- **EXP-14 (contrast phase, isolated at matched resolution):** decisive. Non-contrast trains a highly specific model (90-95%), portal-venous a sensitive but trigger-happy one (10% specificity). So **contrast phase, not resolution, is the sensitivity/specificity dial.** This is the strongest explanatory result so far.
- **Key learning:** two training knobs (sampling, loss) failed to move raw specificity, so over-prediction is a **data-scale** problem. Next lever = scale up tumor data (needs a persistent/disk cache instead of the RAM `CacheDataset`). Full hypotheses and decisions for every run are in `docs/experiments.md` (EXP-01 through EXP-14).

## 5. Files to read to get oriented

- `CLAUDE.md` — running state log; read for the latest status in one place.
- `docs/experiments.md` — the science: every run as a formal experiment with hypothesis + decision.
- `docs/architecture.md` — master design doc and scope ladder.
- `docs/implementation-plan.md` — living plan and decision record; `docs/schedule.md` — 5-week schedule.
- `week2/data-understanding-report.md` — the M2A1/M2P2 report (data profile, pipeline, features, requirements).
- Code: `configs/level45.yaml` (the recipe as config), `src/data/transforms.py` (preprocessing + whole-box), `scripts/train.py` and `scripts/evaluate.py` (train/eval with CLI overrides), `src/models/segresnet.py` (model + SuPreM loader), `src/training/` (losses, metrics, trainer), `src/inference/` (sliding window, post-processing).
- Experiment tooling: `scripts/make_clarity_splits.py`, `scripts/make_contrast_splits.py`, `scripts/log_run_to_mlflow.py`, `scripts/audit_masks.py`.

## 6. Environment + how to run

- **Two venvs:** `.venv312` (Python 3.12, **has mlflow** — use for training, eval, MLflow) and `.venv` (3.14, no mlflow). 3.14 could not install mlflow, hence 3.12.
- MPS backend: prefix runs with `PYTORCH_ENABLE_MPS_FALLBACK=1`.
- Dataset lives on an **external drive** (`/Volumes/JHU-PanTS/PanTS/data`), path set in `configs/level45.yaml` (`paths.pants_root`), never hardcoded, never committed.
- Typical eval: `PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py --ckpt outputs/checkpoints/pants-level45/best.pt --n-pos 20 --n-neg 20 --crop-native 16 --whole-box --roi 128 --spacing 1.5 --sweep`.

## 7. Pending / open items

- **Commit + push + merge to main** (user does git), then submit the three assignment links.
- **MLflow:** log EXP-12/13/14 with `python scripts/log_run_to_mlflow.py` in `.venv312` (check the UI first to avoid duplicate runs; use `--runs ...` to log only what is missing).
- **Notebook re-run (before submit):** the manufacturers/sites fix included a rewritten notebook code cell with a hand-edited cached output. Re-run the notebook top to bottom in `.venv312` and re-save so every output is a real execution (validates the new dedup code and cleans the execution counts). Connect the external drive first in case a cell loads a sample scan.
- **Next experiment lever:** data scale-up (needs disk cache); also test-time augmentation (free) and the autonomous pancreas-detector stage toward the capstone cascade.

## 8. Working style (the user's preferences)

Concise and direct; no em dashes and no asterisks in prose written in his voice. He runs the training himself and pastes results back. He values honest, single-variable experiments with pre-registered accept/reject bars and clearly stated confounds. Do not overstate results; always separate the clean read from the confounded one.
