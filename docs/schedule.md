# 5-Week Schedule

**Project:** 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS)
**Primary target:** Level 4.5 (background / pancreas / lesion)
**Solo project.** Dates are approximate — confirm against the official course calendar.

Weeks 1–2 are setup and data validation; meaningful technical milestones begin Week 2 and compound from there. Each week lists what "behind schedule" looks like so problems are caught early.

---

## Week 1 — Setup & Data Validation (≈ Jun 29 – Jul 5)

**Goal:** Repo exists, dataset access works, one case is proven correct end to end.

- Finalize proposal + pitch (M1A1 / M1P1).
- Scaffold repo: `configs/`, `src/`, `scripts/`, `data/`, `outputs/`, `.gitignore`, `requirements.txt`.
- Download a small **local subset** of PanTS (raw data never committed).
- Build `manifest.csv` (`build_manifest.py`).
- **Sanity-check one case** (`sanity_check_case.py`): load CT + pancreas + lesion, print shape/spacing/affine/intensity range, verify mask alignment, save axial/coronal/sagittal overlays.

**Milestone:** The repo can load one PanTS case and save correct 3-view overlays of CT + pancreas + lesion.
**Behind-schedule signal:** Cannot load or align a single CT+mask pair, or overlays don't line up, by end of week.

---

## Week 2 — Preprocessing & Pipeline Wiring (≈ Jul 6 – Jul 12)

**Goal:** A real preprocessing pipeline and a proven-correct training loop on a trivial target.

- MONAI preprocessing: orientation (RAS), spacing resample, HU window `[-100, 300]` → normalize `[0, 1]`, channel-first.
- Patient-level train/val/test splits (`create_splits.py`) — **never split by slice**.
- Training transforms: `RandCropByPosNegLabeld`, flips, rot90, intensity jitter.
- Build model + loss + metrics (`monai_unet.py`, `losses.py`, `metrics.py`, `trainer.py`).
- **Stage 0 — overfit one case:** force the model to reproduce the mask on 1–2 cases.

**Milestone:** Model overfits 1–2 cases (near-perfect Dice on the training case).
**Behind-schedule signal:** Model cannot overfit a tiny subset → the pipeline is broken (data, loss, or label wiring).

---

## Week 3 — Baseline Training (≈ Jul 13 – Jul 19)

**Goal:** Pipeline validated on an easy target, then first real pancreas+lesion run.

- **Stage 1 — pancreas-only** training (CT → pancreas) as a fast pipeline-validation run. Don't linger here.
- **Stage 2 — pancreas + lesion** (CT → background / pancreas / lesion) on a small subset.
- Validation loop, checkpoint saving, TensorBoard logging.
- _Week 3 1-on-1 retrospective (model selection reasoning, plan health)._

**Milestone:** Model trains on a subset and produces validation Dice curves + visual overlays for pancreas and lesion.
**Behind-schedule signal:** No validation Dice curve, training diverges, or lesion Dice is stuck at ~0.

---

## Week 4 — Lesion-Focused Training & Full-Volume Inference (≈ Jul 20 – Jul 26)

**Goal:** Make the model actually find lesions, and evaluate the right way.

- **Stage 3 — lesion-focused:** positive/negative patch sampling (~70% lesion-positive) so the model sees tumor voxels; tune loss/class weighting (Dice-CE / Dice-Focal).
- **Stage 4 — sliding-window inference** over full volumes (not patch-only scoring).
- Per-class metrics: pancreas Dice, lesion Dice, lesion IoU, sensitivity, precision, false-positive volume.

**Milestone:** Full-volume sliding-window results with pancreas and lesion reported **separately**, plus non-trivial lesion Dice.
**Behind-schedule signal:** Lesion Dice ≈ 0 or model predicts only background; no full-volume evaluation.

---

## Week 5 — Evaluation, Demo & Delivery (≈ Jul 27 – Aug 2)

**Goal:** Polished results, a working demo, and a final report/presentation.

- Failure-case analysis (false negatives, over-segmentation), visual overlays in all 3 planes.
- **React + NiiVue demo:** load case → tri-planar + 3D overlays + CADe summary + mask export (static app reading precomputed predictions).
- Final report: methods, metrics tables, visuals, limitations, honest "not diagnostic" framing.
- Presentation prep.
- _Week 5 1-on-1 retrospective (UI/business layer readiness, final prep)._

**Milestone:** Complete repo + report + working demo + separated pancreas/lesion metrics.
**Behind-schedule signal:** Demo not running, or no full-volume metrics/visuals ready for the final.

---

## Risk buffer

If any stage slips, **Level 4.5 is the line that must hold** — Level 5 (multi-structure) is explicitly a stretch goal and is dropped first. If lesion segmentation underperforms by Week 4, fall back to delivering a strong pancreas-segmentation result plus a documented analysis of *why* the lesion is hard (still a complete, honest project).
