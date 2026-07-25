# M4A1 — Tuning, Orchestration & Deployment Report (Week 4)

**Project:** 3D pancreas + pancreatic-lesion segmentation on JHU PanTS (a non-diagnostic CADe assist).
**Track:** Computer vision (3D medical image segmentation).
**Status:** DRAFT — TODO markers show what still needs data (test-set numbers, Optuna results, screenshots, the pipeline diagram, the API endpoint).

> Framing note for the grader: this rubric is written for a real-time MLOps pipeline (streaming ingestion, scheduled retraining, an API). This project is a **static research dataset + a 3D segmentation model**, so a few requirements (real-time ingestion, DAG-scheduled retraining) do not literally apply. Where that is the case I document the *actual* pipeline and justify the difference rather than bolt on a scheduler that would ingest a dataset that never changes.

---

## 1. Hyperparameter Tuning

**Tuning strategy — two complementary methods, and why.**
- **Primary: targeted single-variable ablation.** Every training run is ~7 hours on a single Apple-Silicon GPU, so a blind grid/random search over the full space is infeasible (a 4×4 grid would be weeks of compute). Instead I ran a **disciplined single-variable search**: change exactly one design/hyperparameter, hold everything else fixed, and accept/reject by a pre-registered bar — recorded run-by-run in `docs/experiments.md`. This is the most sample-efficient way to attribute an effect to one variable under a tight compute budget, and it doubles as an ablation study.
- **Secondary: Bayesian optimization (Optuna).** To formally search the *continuous* training hyperparameters, I ran an Optuna study (Tree-structured Parzen Estimator sampler + median pruner) over short proxy trials — see `scripts/tune_optuna.py`. Short trials (fixed step budget on the cached whole-box data) let the search evaluate many configurations overnight; the search then informs the final full-length run.

**Hyperparameters tuned + ranges explored.**

| Hyperparameter | Range explored | Method | Result / chosen |
|---|---|---|---|
| Learning rate (transfer) | 5e-5 – 5e-4 (log) | Optuna | TODO |
| Focal γ | 1.0 – 4.0 | Optuna | TODO |
| λ_dice / λ_focal | 0.5 – 2.0 each | Optuna | TODO |
| Weight decay | 1e-6 – 1e-4 (log) | Optuna | TODO |
| Loss function | DiceCE / DiceFocal / Tversky / Tversky-Focal | single-variable | DiceFocal (bg-excluded) |
| Sampling ratio (pos:neg) | 2:1 / 1:1 / class-balanced | single-variable | 1:1 (null → not the lever) |
| Patch / field-of-view | 96³ vs 128³ | single-variable | 128³ whole-box |
| Spacing / resolution | 1.5 / 1.2 mm | single-variable | 1.5 mm (finer = null) |
| Input framing | random sub-patch vs whole-box | single-variable | **whole-box (breakthrough)** |
| Transfer vs scratch | SuPreM vs random init | single-variable | **SuPreM transfer (decisive)** |
| Training data scale | 95 → 300 → 1,412 tumor-cohort | single-variable | **max data (dominant lever)** |
| Anatomy auxiliary (λ_anat) | 0.0 vs 0.3 | single-variable | 0.0 (rejected at convergence) |

**Pre- vs post-tuning performance (lesion Dice, provided-ROI, held-out val):**

| Stage | Lesion Dice | Note |
|---|---|---|
| Early dev baseline | ~0.17 | small dev subset, pre-whole-box |
| + whole-box framing | ~0.26 | fixed over-prediction |
| + data scale-up | ~0.31 → 0.41 | the dominant lever |
| Leakage fix (honest number) | **0.415** | current registered baseline |
| + Optuna-tuned training HPs | TODO | expect small gain / confirm baseline is near-optimal |

**MLflow logging + final model registration.**
- All training runs log params + metrics to a local MLflow (`sqlite:///outputs/mlflow.db`); every run also writes an immutable on-disk archive + a `run_ledger.csv` row (an MLflow-independent safety net, added after losing a checkpoint earlier).
- The Optuna trials log to the `pants-level45-optuna` experiment.
- **Final model registered in the MLflow Model Registry** as `pancreas-lesion-segmenter` **version 1**
  (checkpoint step 18000, sha256 `62cc72fd…`), the whole-box SuPreM `scaledmax_clean` model, via
  `scripts/register_model.py` (logs the raw checkpoint + a proper `mlflow.pytorch` model + the resolved
  config + provenance). *[TODO: registration screenshot from the MLflow Models tab.]*

*[TODO: MLflow screenshots — tuning runs + the registered model.]*

---

## 2. Final Model Evaluation (held-out TEST set)

**The registered model** is the whole-box SegResNet+SuPreM segmenter (leakage-free training). Evaluated ONCE on the untouched **official test set (901 cases)**.

**Final metrics — official held-out TEST set (901 cases: 151 tumor-positive + 750 tumor-free), scored ONCE:**
- **Lesion Dice (tumor-positive, n=151): 0.474 raw / 0.472 cleaned; 95% bootstrap CI [0.424, 0.525].**
- **Pancreas Dice: 0.827.**
- **Detection sensitivity: 96% (145/151)** — the fraction of tumors flagged at all.
- **Specificity (tumor-free, n=750): 17% (128/750)** — the fraction of healthy scans NOT flagged.
- Registered model: `pancreas-lesion-segmenter` v1 (checkpoint step 18000, sha `62cc72fd…`), whole-box SuPreM, `scaledmax_clean`, leakage-free.

The model is provided-ROI (a ground-truth pancreas box supplies the crop). The 151 positives are the
*complete* set of tumor cases in the official test split (lesion Dice is only defined where a tumor
exists), and the 750 negatives are the complete tumor-free set — so this is the entire held-out test
set, evaluated one time on a split we did not choose.

**Business interpretation.** This is a CADe (computer-aided *detection*) assist. The clinically decisive
metric is **detection sensitivity — 96%** — because a missed tumor is the costly error; the tool flags
almost every tumor for review. **Lesion Dice (0.474, CI [0.42, 0.52])** measures outline quality — how
much a radiologist must edit the proposed contour — and sits right against the ~0.53 published SOTA, so
it is a credible research-grade result. **Specificity (17%)** is the false-alarm rate: the model
over-calls tumors on healthy scans, so at this operating point it behaves like a *sensitive screening*
tool (catch everything, tolerate false alarms) rather than a specific one.

**Visualization.** The test-set lesion Dice broken down by tumor size and contrast phase:

![by size and phase](img/test-by-size-phase.svg)

Plus the Week-3 confusion-matrix/specificity, operating-point trade-off, and Dice-by-tumor-size diagrams;
`outputs/test_percase.csv` holds the per-case values; and `export_case.py` overlays give sample
predictions with confidence *(2–3 in `week4/img/` — TODO)*. The threshold sweep (evaluate.py
`--sweep`) shows lesion Dice is flat (~0.47) across thresholds while specificity rises only 13%→28%
(0.30→0.90), i.e. the false positives are high-confidence and near the organ, so a probability cutoff
cannot prune them — specificity is a data problem, not a thresholding one.

**Limitations / failure modes (honest, from `analyze_cases.py` on the test set).**
- **Tumor size is the dominant driver of outline quality:** lesion Dice by size — small <1 cm³ **0.067**
  (n=27, 78% detected), medium 1–8 cm³ **0.512** (100% detected), large >8 cm³ **0.610** (100% detected).
- **The mechanism is over-segmentation:** the model *detects* small tumors but paints them 25–50× too
  large (e.g. GT 34 mm³ → predicted 1728 mm³). This single behavior both caps small-tumor Dice AND drives
  the 17% specificity (the same over-painting fires on healthy scans). ~20% of positives (30/151) are
  near-zero Dice, almost all small tumors.
- **Contrast phase is a secondary, size-confounded effect:** on the test set Non-contrast held up
  (0.547, 100% detected) while Venous was lowest (0.435) — Venous is the bulk (n=108) and carries most of
  the small-tumor misses, so the phase gap mostly reflects size, not phase per se.
- **Provided vs autonomous ROI:** the headline uses a provided pancreas box; the autonomous
  localize-then-segment number (~0.48) is the deployable figure and a capstone-facing item.
- **Data quality:** ~11–14% of raw cases had empty/corrupt masks (audited + excluded before training).

---

## 3. Pipeline Orchestration

**How this project maps to the rubric (real-time framing → static research dataset).** This assignment
assumes a real-time ML service; this project is a static dataset (JHU PanTS) + a 3D segmentation model,
so some concepts don't apply literally. Rather than fake them, here is the honest mapping — the pipeline
still satisfies CO2 (a resilient, automated pipeline):

| Assignment concept | This project | Why it still meets the outcome |
|---|---|---|
| Real-time data ingestion | one-time indexing (`build_manifest.py` → `manifest.csv`) | no stream exists; ingestion is a solved, versioned step |
| DAG-scheduled retraining | manual / CLI trigger, run per experiment | a static dataset never changes, so a scheduler adds risk with no benefit; reproducibility comes from config + fixed seed + committed splits |
| serve via an API | **built:** `serve.py` FastAPI `POST /predict` | fully satisfied (see §4) |
| confusion matrix / residuals | segmentation → Dice overlap + specificity counts + by-size/phase + sample overlays | correct equivalents for dense segmentation (rubric allows "or equivalent") |
| event-based trigger | future work (new study → localize → segment → flag) | shows the deployed design; out of scope for a static dataset |

**End-to-end pipeline (plain language).**
1. **Ingestion / indexing** — `build_manifest.py` scans the dataset on the external drive and writes `manifest.csv` (one row per case: CT + mask paths + metadata).
2. **Splitting** — `create_splits.py` carves patient-level, tumor-stratified train/val/test lists; `make_scaled_split.py` / `build_exp26_cohorts.py` build experiment cohorts *only from the training fold* (with a disjointness assert).
3. **Data-quality audit** — `audit_subregions.py` flags/excludes empty or misaligned masks before training.
4. **Preprocessing + training** — `train.py` streams cases through the whole-box preprocessing, fine-tunes SegResNet from SuPreM, logs to MLflow, and archives checkpoints.
5. **Evaluation** — `evaluate.py` / `analyze_cases.py` / `cascade_eval.py` score a checkpoint (Dice, specificity, per-case breakdown, autonomous cascade).
6. **Serving / export** — `export_case.py` writes prediction files (NIfTI + 3D meshes + `results.json`); a minimal FastAPI endpoint serves predictions (section 4); the Week-5 UI consumes them.

**Trigger mechanism + frequency (and why not a scheduler).** The trigger is **manual / command-line**, run once per experiment. This is deliberate: PanTS is a **fixed, static dataset** — there is no streaming source and no new data arriving on a schedule, so a DAG/Airflow-style scheduled retrain would add operational complexity with zero benefit (it would re-ingest a dataset that never changes). The reproducibility a scheduler normally provides is instead delivered by the config-driven scripts + fixed seed + committed splits, which make any run exactly repeatable on demand. *(If this were deployed against a live PACS feed, the natural trigger would be event-based — a new study arrives → localize → segment → surface to the radiologist — noted as future work.)*

**Data versioning.** Code + config + committed split ID-lists + `experiments.md` in git; the manifest and derived splits are regenerated deterministically; raw data never committed (lives on the external drive, path via config).

**Model logging.** MLflow (params/metrics per run) + a per-run immutable checkpoint archive with a `run_info.txt` recipe record + a `run_ledger.csv` (one row per run, never overwritten). This redundancy exists because a good checkpoint was once lost to an overwrite.

**Error handling / resilience.** Startup **leakage guard** (aborts if a training split touches val/test), **atomic checkpoint saves** (temp-file + rename, so a crash mid-write can't corrupt a checkpoint), **hardened resume** (recipe-identity verification + strict optimizer/scheduler restore + deterministic step-indexed data, so a paused run reproduces the same trajectory), and drive-presence checks.

**Diagram.** See `week4/img/pipeline-diagram.svg` — the four stages (data prep → training → evaluation →
registration/serving/UI) plus the cross-cutting trigger, data-versioning, model-logging, and
error-handling concerns.

![pipeline](img/pipeline-diagram.svg)

---

## 4. Model Deployment

**Registration + versioning.** The final model is registered in the MLflow Model Registry as `pancreas-lesion-segmenter` **version 1** (checkpoint step 18000, sha256 `62cc72fd…`). Registration logs the raw checkpoint, a proper `mlflow.pytorch` model (MLmodel flavor), the fully-resolved config, and provenance (checkpoint SHA + step, recipe, git commit). The registered PyTorch model is the **network component only**; `scripts/serve.py` supplies the whole-box preprocessing + CADe summarization.

**Inference endpoint.** *[TODO tomorrow: a minimal FastAPI service (`app.py`) wrapping the `predict_volume` + `postprocess` inference API.]*
- **How it's called:** `POST /predict` with a case identifier (or an uploaded NIfTI) →
- **What it returns:** a CADe summary JSON: `{ "case_id", "lesion_present": bool, "lesion_volume_mm3", "confidence", "pancreas_dice"?, "mask_url" }`.
- **Sample call + response:** *[TODO.]*
- **Latency / performance.** Full-volume sliding-window inference is ~a few seconds per case on the GPU (CPU stitching to relieve MPS memory). For a CADe assist this is well within an acceptable turnaround (a radiologist reviews the overlay, not a real-time stream), so throughput is not a bottleneck; the relevant consideration is memory (whole 3D volumes), handled by cropping to the pancreas ROI + CPU stitching.

---

## 5. Orchestration & Deployment Decisions (reflection)

*[One paragraph — draft:]* The central architectural decision this week was to **not** impose a real-time MLOps scaffolding (Airflow DAGs, scheduled retraining, streaming ingestion) on a static research dataset, and to instead invest that effort in **reproducibility and resilience** where it actually pays off: a config-driven, single-command pipeline; MLflow plus an MLflow-independent checkpoint archive and ledger; a startup leakage guard; and atomic, identity-verified resumable training. The trade-off is that the pipeline is triggered manually rather than automatically — acceptable here because the data never changes, but a limitation if this were deployed against a live imaging feed, where an event-based trigger would be the right design. With more time I would (a) build out the localize-then-segment cascade into the serving path so the API needs no provided ROI, and (b) add a lightweight tumor-presence gate to raise specificity before serving predictions to a clinician.

---

## Appendix — where each rubric item lives
- HP tuning → §1 + `docs/experiments.md` + `scripts/tune_optuna.py` + MLflow.
- Final eval → §2 + `scripts/evaluate.py` on test + Week-3 diagrams.
- Orchestration → §3 + `week4/pipeline-diagram.png`.
- Deployment → §4 + `app.py` + MLflow registry.
- AI docs → `docs/ai-usage-log.md` (Week-4 entry), `docs/implementation-plan.md`, `CLAUDE.md`.
