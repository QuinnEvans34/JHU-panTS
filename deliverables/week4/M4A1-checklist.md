# M4A1 completion checklist — full-points tracker (30 pts)

Work off this for the rest of the day. Each rubric criterion: what it wants → our status → the artifact →
what's left. A ✅ = done, 🔲 = you still need to do it (mostly screenshots + one endpoint smoke test).
The key strategic section is **§0 (project-fit mapping)** — that's how we claim points on the parts of
the assignment written for a real-time MLOps project that our static-dataset deep-learning project does
not literally match.

---

## §0 · Project-fit mapping (READ FIRST — this protects ~7 pts of "orchestration + deployment")

The assignment is written for a **real-time ML service** (streaming ingestion → scheduled retraining →
API). Ours is a **static research dataset (JHU PanTS) + a 3D segmentation model**. Several assignment
concepts therefore don't apply literally. We do NOT fake them — we document the honest mapping and argue
we still meet the two learning outcomes (CO2 resilient pipeline, CO3 tracking/tuning/evaluation). Put this
table in the report (§3) so the grader sees a deliberate, justified choice, not an omission:

| Assignment concept (real-time framing) | Our project (static research dataset) | Why this still earns the outcome |
|---|---|---|
| Real-time data ingestion | One-time indexing: `build_manifest.py` scans the dataset → `manifest.csv` | Ingestion is a solved, versioned step; there is no stream to consume. |
| DAG-scheduled retraining | Manual / command-line trigger, run once per experiment | The dataset never changes, so a scheduler adds operational risk with zero benefit. Reproducibility is delivered by config + fixed seed + committed splits instead. |
| "Serve predictions via an API" | We DID build one: `serve.py` FastAPI `POST /predict` | Fully satisfied — this is not skipped. |
| Confusion matrix / residual plot | Segmentation → per-voxel overlap (Dice), specificity confusion counts, by-size/phase breakdown, sample overlays | The problem type is dense segmentation, so overlap + operating-point + sample predictions are the correct equivalents (the rubric explicitly allows "or equivalent visualization"). |
| Event-based trigger (future) | Noted as future work: new study arrives → localize → segment → surface | Shows we understand the deployed design; out of scope for a static dataset. |

**One-paragraph version for the report intro (already drafted there):** "This rubric assumes a real-time
MLOps pipeline; this project is a static research dataset and a 3D segmentation model, so real-time
ingestion and scheduled retraining do not literally apply. Rather than bolt on a scheduler that would
re-ingest a dataset that never changes, I documented the actual pipeline and justified the differences,
and invested that effort in reproducibility and resilience (config-driven runs, MLflow + an
MLflow-independent checkpoint archive, a startup leakage guard, atomic identity-verified resumable
training) — which is what CO2 (a resilient, automated pipeline) actually rewards."

---

## 1 · Hyperparameter Tuning — 8 pts
- ✅ **Strategy justified:** two methods — targeted single-variable ablation (7h/run makes blind grid infeasible) + **Optuna Bayesian (TPE)**. In report §1 + `docs/experiments.md`.
- ✅ **Ranges intentional:** lr 5e-5–5e-4, γ 1–4, λ_dice/λ_focal 0.5–2, wd 1e-6–1e-4 (report §1 table).
- ✅ **All runs in MLflow:** `pants-level45` (training) + `pants-level45-optuna` (15 trials).
- ✅ **Pre/post comparison:** the tuning progression (early ~0.17 → whole-box ~0.26 → data-scale ~0.41 → final test 0.474) + Optuna confirming lr near-optimal / γ mild lever. In report §1.
- ✅ **Final model registered:** `pancreas-lesion-segmenter` v1 (step 18000, sha `62cc72fd`).
- 🔲 **MLflow screenshots:** capture (a) the optuna experiment's tuning runs, (b) the registered model (Models tab) → save PNGs to `deliverables/week4/img/`. *This is the only missing item for this criterion.*

## 2 · Final Model Evaluation — 8 pts
- ✅ **Test-set metrics (held-out, one-time):** lesion Dice **0.474 [0.42–0.52]**, pancreas 0.827, detection **96%**, specificity **17%**. In report §2.
- ✅ **Business interpretation:** detection = the CADe headline; Dice = edit burden; specificity = false-alarm rate; ~0.53 SOTA reference. In report §2.
- ✅ **Honest limitations:** over-segmentation (small tumors 25–50× too large), size-driven Dice (0.067/0.512/0.610), size-confounded phase effect. In report §2.
- ✅ **Visualization:** by-size/by-phase bar chart (`deliverables/week4/img/test-by-size-phase.svg`) + Week-3 diagrams.
- 🔲 **Sample predictions with confidence (CV track):** export 2–3 test-case overlays with the CADe confidence — `python scripts/export_case.py --ckpt <FINAL_CKPT> --split test --case <id> --whole-box --crop-native 16 --roi 128` → drop the PNGs in `deliverables/week4/img/`. (Pick one small-miss + one good case for an honest contrast.)

## 3 · Pipeline Orchestration — 4 pts
- ✅ **Pipeline in plain language** + the **§0 fit-mapping table**. Report §3.
- ✅ **Trigger:** manual/CLI, justified (static dataset). Report §3.
- ✅ **Data versioning / model logging / error handling:** git + committed splits; MLflow + archive + ledger; leakage guard + atomic saves + strict resume + drive preflight. Report §3.
- ✅ **Diagram:** `deliverables/week4/img/pipeline-diagram.svg`.
- 🔲 (optional) If the grader needs a raster, export the SVG to PNG. SVG renders in GitHub/browsers, so likely fine as-is.

## 4 · Model Deployment — 3 pts
- ✅ **Registered + versioned:** `pancreas-lesion-segmenter` v1, provenance logged. Report §4.
- ✅ **Endpoint documented:** `serve.py` `GET /health` + `POST /predict {case_id}` → CADe summary. Report §4.
- ✅ **Latency noted:** ~a few sec/case, batch-review use-case. Report §4.
- 🔲 **Sample call + response:** smoke-test the endpoint and paste real output —
  `pip install fastapi uvicorn --break-system-packages`; `MODEL_CKPT=<FINAL_CKPT> uvicorn scripts.serve:app --port 8000 --workers 1`;
  then `curl -s localhost:8000/health` and `curl -s -X POST localhost:8000/predict -H 'content-type: application/json' -d '{"case_id":"<a test_pos id>"}'`. Paste both into report §4.
  *(Do this when the GPU is free — after the fullhealthy run, or briefly pause it.)*

## 5 · Orchestration & Deployment Decisions (reflection) — part of the report
- ✅ One-paragraph reflection drafted (report §5): chose reproducibility/resilience over real-time scaffolding on a static dataset; manual-trigger trade-off; with more time → cascade in the serving path + a specificity gate.

## 6 · AI Documentation Files — 7 pts
- ✅ **`ai-usage-log.md` Week-4 entry:** specific on the anatomy experiment, Optuna, and the deployment build + the plan→code→review loop + honest corrections + what's complete vs at-risk into Week 5.
- ✅ **`implementation-plan.md` Week-4 update.**
- ✅ **`CLAUDE.md`:** updated (EXP-26 + Week-4 M4A1 note).

---

## What YOU still need to do (the short list)
1. 🔲 **Two MLflow screenshots** → `deliverables/week4/img/` (optuna runs + registered model). [§1]
2. 🔲 **Endpoint smoke test** → paste `/health` + `/predict` output into report §4. [§4] *(GPU-free window)*
3. 🔲 **2–3 sample-prediction overlays** with confidence → `deliverables/week4/img/`. [§2] *(GPU-free window)*
4. 🔲 **Git:** create a `deliverables/week4/` branch, commit the `deliverables/week4/` folder + the updated root `docs/`, merge to main.
5. 🔲 (after fullhealthy finishes) fold the EXP-25 specificity result into experiments.md + optionally the report as a "Week-5 direction" note.

## What I (Claude) still owe
- The by-size/phase figure (this turn), the §0 mapping into the report, a final consistency read-through of the whole report, and folding in your smoke-test output + screenshots once you produce them.

## Point-risk summary
Nothing is at 0. The only unclaimed points are gated on **artifacts you produce** (2 screenshots, 1 curl, 2 overlays) — no new modeling. If those land, this is a full-marks submission: the tuning is genuinely rigorous (ablation + Bayesian), the evaluation is an honest held-out test with a CI and failure-mode analysis, the pipeline + deployment are real and documented with the fit-mapping, and the AI docs are specific and honest.
