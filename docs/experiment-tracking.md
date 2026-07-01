# Experiment Tracking (MLflow)

**Living doc.** MLflow is a hard project requirement and the spine of the experiment story — it doubles as the engine for the scratch-vs-transfer comparison. Pairs with `training.md`.

---

## 1. Setup (local, no server needed)

- **Tracking backend:** local SQLite (`mlflow.set_tracking_uri("sqlite:///mlruns.db")`) or a plain file store (`./mlruns`).
- **Artifact store:** point to the **external drive** — checkpoints are large and will fill the laptop SSD otherwise.
- **View:** `mlflow ui` → browse runs, compare metrics, view artifacts.
- Keep it config-driven: tracking URI + experiment name come from the YAML, never hardcoded.

## 2. Experiment & run organization

- **Experiment per level/stage**, e.g. `pants-level45`, `pants-pancreas-only`.
- **One MLflow run per training run.** Name runs descriptively (`segresnet_scratch_seed0`, `swinunetr_transfer_seed0`).
- **Tags** for filtering/comparison: `model=scratch|transfer`, `arch=segresnet|swinunetr`, `level=4.5`, `stage=2`, `config_hash=...`.
- **Resumed runs** continue the same `run_id` (or log as a child run) so a multi-session training shows as one timeline.

## 3. What to log

**Params (once, at start):**
- The full resolved config (all YAML values), model arch, `label_mode`, patch size, LR, optimizer, loss, sampling ratio, seed.
- Pretrained-weights source (if transfer).

**Metrics (per epoch / per validation):**
- `train/loss`, `val/loss`.
- `val/dice_pancreas`, `val/dice_lesion` (logged **separately** — never just the average).
- `val/iou_lesion`, `val/sensitivity_patient`, `val/sensitivity_tumor`, `val/specificity`, `val/auc`, `val/fp_per_scan`.
- LR (track the schedule).

**Artifacts:**
- Best checkpoint (by lesion Dice).
- Config snapshot + **git commit hash** (reproducibility).
- Example prediction overlays (axial/coronal/sagittal PNGs) each validation — visual progress over time.
- Final metrics table (CSV) and failure-case list.

## 4. Comparison workflow (the payoff)

Because every run is tagged `model=scratch` vs `model=transfer`, the MLflow UI gives a direct side-by-side of lesion Dice and sensitivity/specificity curves. That single view **is** your "did pretraining help?" ablation and satisfies the logging requirement at the same time. Same mechanism compares loss functions, patch sizes, and (later) single-stage vs cascade.

## 5. Integration approach

- **Explicit `mlflow.log_metrics` calls in a plain PyTorch loop** (preferred) — transparent, easy to debug on MPS.
- MONAI ships an `MLFlowHandler` for the Ignite-engine route as an alternative.
- Log at the same cadence as validation to keep the metric timeline clean.

## 6. Relationship to TensorBoard

MLflow is the required, primary tracker. TensorBoard is optional and off by default to avoid double-bookkeeping; can be re-enabled for live loss curves if useful.

## 7. Open questions

- SQLite vs file store (SQLite gives nicer UI querying).
- Exact artifact-retention policy (checkpoints are large — keep best + last only?).
- Whether to log the 3D mesh / interactive HTML as an artifact for demo runs.
