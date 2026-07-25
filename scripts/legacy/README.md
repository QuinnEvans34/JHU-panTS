# scripts/legacy/

One-off and superseded scripts, moved here to keep the main `scripts/` folder focused on the
current pipeline. Nothing in `src/` or the active scripts imports these, so moving them is safe.
They still run (their `src` import path was adjusted for the deeper folder), but they are not part
of the day-to-day workflow.

| Script | What it was for | Why it's here |
|---|---|---|
| `peek_case.py` | Save slice PNGs of one case (quick data peek). | Ad-hoc exploration, Week 1. |
| `find_lesions.py` | List tumor-positive cases in the dataset. | Ad-hoc exploration. |
| `view3d.py` | Quick 3D peek of a mask. | Ad-hoc exploration. |
| `make_clarity_splits.py` | Build the clarity-curriculum experiment splits. | EXP-13 finished. |
| `make_contrast_splits.py` | Build the contrast-phase (nc/pv) experiment splits. | EXP-14 finished. |
| `audit_masks.py` | 3-class pancreas-mask quality audit (empty/tiny/oversized). | Superseded by `scripts/audit_subregions.py` (the head/body/tail-aware audit). |
| `inspect_checkpoint.py` | Print a checkpoint's tensor shapes. | Used once to match our SegResNet to the SuPreM weights; kept for reference. |
| `log_run_to_mlflow.py` | Re-log a run to MLflow if it trained in a no-MLflow env. | Housekeeping utility. |

The current pipeline is: `build_manifest` → `create_splits` / `make_scaled_split` / `build_exp26_cohorts`
→ `audit_subregions` → `make_init_checkpoint` → **`train.py`** → `evaluate.py` / `analyze_cases.py` /
`cascade_eval.py` / `paired_bootstrap.py` → `export_case.py`.
