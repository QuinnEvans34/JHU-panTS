# Codex pass-off — CODE PLAN for M4A1 deployment + registration + test eval

Review this DESIGN before we write any code. It covers the only new code M4A1 needs:
(1) a single-entry inference wrapper, (2) a minimal FastAPI endpoint, (3) MLflow model registration,
(4) a small test-set cohort helper. Verdict requested: **APPROVE** the plan or list changes. After
approval we write the code, then send it back to you for a CODE review.

Context: static PanTS dataset; whole-box SegResNet+SuPreM segmenter (final model, provided-ROI Dice
~0.415); existing inference API = `src/inference/sliding_window.predict_volume`, `postprocess.postprocess`,
`collapse.*`. The logic (load case → preprocess → sliding-window → argmax → postprocess → summary) is
currently duplicated across `evaluate.py` / `export_case.py::infer_case` / `cascade_eval.py`.

---

## 1. `src/inference/predict.py` — one clean inference entry point (DRY)

```python
def predict_case(cfg, model, device, case_id, split="test", compute_dice=True) -> dict
```
- Build one preprocessed sample via `get_dataset(cfg, split, train=False, cache="none", ids=[case_id])`
  + a batch of size 1 (reusing the exact eval preprocessing, so it matches training).
- `probs = softmax(predict_volume(...))`; collapse to 3-class if `label_mode == anatomy5`.
- `pred = probs.argmax(0)`; `pred = postprocess(pred, spacing, lesion_min_mm3, ...)`.
- Compute the CADe summary from `pred` + `probs`:
  - `lesion_present`: `(pred==2).sum() * vox_mm3 >= min_lesion_mm3`
  - `lesion_volume_mm3`: `(pred==2).sum() * vox_mm3`
  - `peak_lesion_confidence`: `float(probs[2].max())`
  - `pancreas_dice`, `lesion_dice`: if the sample carries GT (`label`), else `None`
- Return `{case_id, lesion_present, lesion_volume_mm3, peak_lesion_confidence, pancreas_dice, lesion_dice}`
  (+ optionally the `pred` array for callers that want the mask).
- `evaluate.py` / `export_case.py` can later call this to remove their duplicated logic (not required now).

**Q1:** Is reusing `get_dataset(ids=[case_id])` the right way to preprocess a single case for serving
(vs a bespoke transform pipeline)? Any pitfall computing the summary this way?

## 2. `scripts/serve.py` — minimal FastAPI inference endpoint

- **Startup (once):** load `cfg` with the final-model recipe (whole-box, crop-native 16, 128³ @1.5mm,
  roi_source pancreas), `build_model` + `load_checkpoint` from `--ckpt` (env `MODEL_CKPT`), read the
  checkpoint's `extra` metadata for a `model_version` string. Keep the model global, `eval()` mode.
- **`GET /health`** → `{status:"ok", model:"pancreas-lesion-segmenter", version, device}`.
- **`POST /predict`** → body `{case_id: str, split?: "test"}` → `predict_case(...)` → returns the CADe
  summary JSON.
- Run: `uvicorn scripts.serve:app --port 8000`. Sample call (`curl -X POST .../predict -d '{"case_id":...}'`)
  + sample response go in the report.
- **Documented limitation (honest):** the endpoint takes a known `case_id` from the manifest, i.e. it
  serves the *provided-ROI* model; accepting a raw uploaded CT would require the localize-then-segment
  cascade to find the pancreas first — noted as future work. Latency: ~a few seconds/case (sliding-window,
  CPU stitch) — fine for a batch CADe review, not a real-time stream.

**Q2:** For a 3-pt rubric item, is a **case_id-based** `/predict` acceptable, or do you think we should
accept a **NIfTI file upload** (which needs the cascade for a raw CT with no provided ROI)? Any concern
with a single global model handling sequential requests (no concurrency/threading planned)?

## 3. `scripts/register_model.py` — MLflow Model Registry

Two options — please pick the right one for "model is registered and versioned in MLflow":
- **Option A (simple, proposed):** in an MLflow run, `log_artifact(checkpoint.pt)` + log the recipe
  params/metrics, then `mlflow.register_model(model_uri, "pancreas-lesion-segmenter")` → a versioned
  registry entry pointing at the checkpoint. Minimal, satisfies "registered + versioned," easy screenshot.
- **Option B (proper, more work):** an `mlflow.pyfunc.PythonModel` wrapper whose `predict()` calls
  `predict_case`, logged via `mlflow.pyfunc.log_model(..., code_paths=["src"])` and registered — a truly
  *servable* MLflow model (`mlflow models serve`), which ties registration to the endpoint elegantly but
  requires packaging `src/` + the checkpoint as artifacts and handling the external-drive data path.

**Q3:** Is **Option A sufficient** for the rubric, or is **Option B worth the extra effort** for a 3-pt
item + the "Exceeds" bar? Any packaging gotcha you'd flag for Option B (code_paths, data path, MPS)?

## 4. `scripts/make_test_cohorts.py` (tiny) — reproducible test eval

- Write `outputs/splits/test_pos.txt` (151 tumor-positive test ids) + `test_neg.txt` (750 negatives, or a
  fixed subset e.g. 151 for a balanced spec read) from the manifest, sorted for determinism.
- Then §2 eval is: `evaluate.py --ckpt <final> --split test --whole-box --crop-native 16 --roi 128
  --roi-source pancreas --pos-ids …/test_pos.txt --neg-ids …/test_neg.txt --per-case-csv … --sweep`
  and `analyze_cases.py` on the test positives.

**Q4:** Build the `test_pos/test_neg` id files + use `--pos-ids/--neg-ids` (clean, reproducible,
per-case CSV), or just pass `--n-pos 151 --n-neg 750`? Any concern scoring all 750 negatives (time ≈ ~1h)
vs a 151-negative balanced subset for the specificity read?

## 5. General
- No new training here — all inference/serving/registration on the existing final checkpoint.
- MPS: serving uses the same `predict_volume` (sliding-window, CPU stitch) that already works.

**Q5:** Anything else in this plan that's wrong, risky, or missing for the deployment/eval sections
(latency framing, error handling on the endpoint, model-version provenance)?

**Requested verdict:** APPROVE the plan, or list the specific changes; then we implement and send the code back for review.
