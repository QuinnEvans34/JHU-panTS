# M4A1 delivery plan — sections 1–5 (what we do, artifact by artifact)

Documentation-first plan for the Tuning/Orchestration/Deployment report. For each rubric section:
what the grader wants, exactly what we produce, the artifact, and whether it needs code (→ Codex
pass-off before we write it, then a Codex code review after). Process: **docs → Codex reviews the
code PLAN → write code → Codex reviews the CODE → integrate.**

Legend: ✍️ writing/doc · 🖥️ command on existing code · 🧩 NEW code (needs Codex pass-off) · 🎨 diagram/image

---

## Section 1 — Hyperparameter Tuning (8 pts)

**What the grader wants:** tuning strategy justified, intentional ranges, all runs in MLflow, pre- vs
post-tuning comparison, final model registered.

**What we do:**
1. ✍️ Write the tuning narrative in the report: **two strategies** — (a) targeted single-variable
   ablation (`experiments.md`), justified by the 7h/run cost; (b) **Bayesian optimization (Optuna TPE)**
   over the continuous training HPs (`scripts/tune_optuna.py`, already run + Codex-reviewed).
2. ✍️ Ranges table (lr 5e-5–5e-4, γ 1–4, λ_dice/λ_focal 0.5–2, wd 1e-6–1e-4) + the **findings**: LR is the
   dominant knob (LR ≳ 2e-4 collapses the lesion to 0.0; our 1e-4 default is confirmed near-optimal), a
   mild signal that higher γ (~3.5–3.9) helps at the proxy horizon, and the median-pruner behavior
   (11/15 pruned early to save compute).
3. **Pre/post comparison — matched conditions (honest):**
   - 🖥️ Cheap apples-to-apples: run the **default config as a 1,500-step proxy** and compare to Optuna's
     best proxy (0.254). Same horizon → fair "before vs after tuning."
   - 🖥️ (optional, weekend) one **full 24k run with the best config** (γ 3.85) vs the 0.415 baseline — the
     real test + a possible new registered model.
   - ✍️ State clearly that the 0.25 proxy values are undertrained rankings, NOT comparable to the 0.415
     full-run number.
4. 🧩 **Register the final model in the MLflow Model Registry** as `pancreas-lesion-segmenter` (a small
   `scripts/register_model.py` — see the code pass-off sheet).
5. 🖥️ Capture **MLflow screenshots** (the `pants-level45` tuning runs + the `pants-level45-optuna`
   experiment + the registered model) → `deliverables/week4/img/`.

**Artifacts:** report §1, `outputs/optuna/wholebox_hp_search_trials.csv`, MLflow screenshots, a registered model.

---

## Section 2 — Final Model Evaluation on the held-out TEST set (8 pts)

**What the grader wants:** test-set metrics with business interpretation, a visualization, honest
limitations; for CV, sample predictions with confidence.

**What we do:**
1. 🖥️ Run the registered model **once on the official `test` split (901 cases)** with `evaluate.py`
   (whole-box, provided-ROI): lesion + pancreas Dice on tumor-positive, specificity on tumor-free,
   threshold sweep. (Confirm `test.txt` exists + has GT labels first.)
2. 🖥️ Run `analyze_cases.py` on test for the **by-tumor-size and by-contrast-phase** breakdown.
3. ✍️ Write §2: numbers + **business interpretation** (detection sensitivity = the CADe headline; Dice =
   edit burden; specificity = false-alarm rate; ~0.53 SOTA reference), **visualization** (reuse the Week-3
   confusion-matrix / operating-point / Dice-by-size diagrams + a couple of `export_case.py` overlay PNGs
   as "sample predictions with confidence"), and **honest limitations** (over-segmentation 3–13×,
   small-tumor 0.11, non-contrast 0.25, provided-vs-autonomous ROI).

**Artifacts:** report §2, test-set metrics, diagrams (Week-3) + sample overlays.
**Code?** Mostly commands on existing scripts. Minor: confirm `evaluate.py`/`analyze_cases.py` run on
`test` and can score ALL positives (not just `--n-pos 12`) — flag any small change in the code pass-off.

---

## Section 3 — Pipeline Orchestration (4 pts)

**What the grader wants:** full pipeline in plain language + diagram; trigger; data versioning; model
logging; error handling.

**What we do:**
1. ✍️ The pipeline narrative is drafted in the report — finalize it (ingestion→manifest→splits→audit→
   train→eval→export/serve), the **manual/script trigger justified** (static dataset → no scheduler),
   data versioning (git + committed splits), model logging (MLflow + archive + ledger), error handling
   (leakage guard, atomic saves, hardened resume, drive checks).
2. 🎨 Generate the **pipeline diagram** as an image → `deliverables/week4/img/pipeline-diagram.png` (I'll produce it).

**Artifacts:** report §3 + the diagram image. **Code?** None.

---

## Section 4 — Model Deployment (3 pts)

**What the grader wants:** model registered/versioned in MLflow; inference endpoint documented with a
sample call + response; latency/performance noted.

**What we do:**
1. 🧩 A clean single-entry inference wrapper `src/inference/predict.py::predict_case(...)` (DRYs the logic
   duplicated across evaluate/export).
2. 🧩 A minimal **FastAPI service** (`scripts/serve.py`): loads the model once at startup; `GET /health`;
   `POST /predict {case_id}` → CADe summary JSON. (See the code pass-off sheet for the exact contract.)
3. 🧩 MLflow model registration (shared with §1's `register_model.py`).
4. ✍️ Write §4: registration/versioning, the endpoint contract, a **sample call + response**, and a
   **latency note** (~a few sec/case sliding-window; batch-review use-case, not real-time streaming).

**Artifacts:** report §4, `src/inference/predict.py`, `scripts/serve.py`, `scripts/register_model.py`,
sample call/response.
**Code?** YES — the main build. Goes through the Codex plan pass-off → code → Codex code review.

---

## Section 5 — Orchestration & Deployment Decisions (reflection)

**What the grader wants:** one paragraph on architectural decisions, trade-offs, what you'd do differently.

**What we do:** ✍️ finalize the drafted paragraph (chose reproducibility/resilience over real-time MLOps
scaffolding on a static dataset; manual trigger trade-off; with more time → cascade in the serving path +
a specificity gate). **Code?** None.

---

## Section 6 — AI Documentation Files (7 pts) [not 1–5 but required]
✍️ `docs/ai-usage-log.md` (Week-4 entry: Optuna + Codex reviews + the deployment build + honest
corrections), `docs/implementation-plan.md` (Week-4 status), `CLAUDE.md` (already current — verify).

---

## Execution order (points-per-effort)
1. ✍️ AI docs + report §1/§3/§5 finalize (fast, ~15 pts of surface). → I draft, you review.
2. 🎨 Pipeline diagram. → I produce.
3. 🖥️ Test-set eval + analyze_cases (§2). → you run, I write §2 from the output.
4. 🧩 Deployment build (§4) — **Codex passes off the plan (next file) → I code → Codex reviews.**
5. 🖥️/🧩 Tuning pre/post: default-proxy run (+ optional full best-config run) + `register_model.py`.

**The only code needing the Codex loop:** `predict_case` + `serve.py` + `register_model.py` (§4/§1), and a
possible tiny tweak to eval for "score all test positives" (§2). Those are specified in
`deliverables/week4/codex-passoff-code-plan.md`.
