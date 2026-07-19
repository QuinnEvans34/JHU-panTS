# Week 4 adversarial code and design audit

Date: 2026-07-19

Scope: data, preprocessing, cache, training, transfer loading, inference, cascade geometry, metrics, splits, experiment claims, and deployment design. This was a read-only code audit apart from writing this report. The working-tree edits already present in `CLAUDE.md`, `docs/experiments.md`, `scripts/audit_masks.py`, and `scripts/cascade_eval.py` were not changed.

## Executive conclusion

The 0-voxel pancreas masks are **not caused by MONAI orientation or resampling**. Raw nibabel inspection confirms genuine source-label defects. However, the current loader is also incomplete: it loads only the flaky combined `pancreas.nii.gz`, so it fails to recover valid head/body/tail labels and accepts corrupt-huge combined masks. The planned union-plus-volume-guard fix is directionally correct but is not implemented, and changing only `source_masks.pancreas` in YAML would have no effect because the training/evaluation record builder does not consume that config.

The most consequential finding is separate: **all scaled datasets were sampled from the full ImageTr pool rather than the canonical training fold.** `scaled300`, `scaled600`, and `scaledmax` overlap validation by 54, 109, and 266 cases respectively. Thirty of the first 40 tumor-positive cases in the current headline evaluation occur in `scaledmax` training. Therefore the provided-ROI ~0.528, autonomous ~0.483, 90% detection sensitivity, and localizer containment results are not held-out validation evidence and must be withdrawn or explicitly labeled contaminated until retrained and rescored on disjoint folds.

## Headline-changing findings

1. **Validation leakage changes every scaled-model headline.** The current EXP-17/17c/20/22 numbers cannot support generalization claims.
2. **The reported 94.6% containment is pre-resize-box containment, not containment in the 128³ tensor actually seen by Stage 2.** With 27.5% oversized boxes, the effective containment can be materially lower.
3. **The 9.5% zero/degenerate-mask observation is a mixture of real dataset gaps and a loader robustness hole.** Raw sources show 101 both-empty healthy validation cases, 9 recoverable subregion-only cases, and 7 oversized combined cases; the current pipeline treats all through the combined mask alone.
4. **The “pancreas-only localizer never sees lesion labels” statement is false.** It is trained as the same three-class pancreas/lesion model and only the pancreas output channel is used to make the box.

## Critical findings

### C1 — Real bug: scaled training splits leak validation cases

**Evidence:** `scripts/make_scaled_split.py:31-39` filters `m[m["split"] == "train"]`. In the manifest, this value is assigned from ImageTr/ImageTe source location (`scripts/build_manifest.py:54-60`), before the canonical train/val split is created. The actual fold membership lives in `outputs/splits/train.txt` and `val.txt` (`scripts/create_splits.py:74-83`).

Read-only set intersections on the current files found:

| split | size | overlap with `val.txt` |
|---|---:|---:|
| `scaled300` | 300 | 54 |
| `scaled600` | 600 | 109 |
| `scaledmax` | 1,412 | 266 |

For the deterministic first-40/first-40 evaluation cohort used by `evaluate.py` and `cascade_eval.py` (`scripts/evaluate.py:137-141`; `scripts/cascade_eval.py:363-368`), **30/40 positive and 5/40 negative cases are members of `scaledmax` training**. The in-loop positive validation used to select `best.pt` is similarly contaminated (`scripts/train.py:137-146`, `scripts/train.py:311-327`).

**Impact:** EXP-17 and EXP-17c data-scaling gains, the ~0.528 provided-ROI result, ~0.483 autonomous result, 90% detection sensitivity, and EXP-22 containment are not held-out validation measurements. The localizer and segmenter both trained on leaked validation cases. The statement in `CLAUDE.md` that there is no train/val leakage is false for scaled experiments.

**Concrete fix:** build every derived split by sampling only IDs from canonical `train.txt`, assert zero intersection with `val.txt` and `test.txt`, and preserve patient-group disjointness. Rebuild `scaled300`, `scaled600`, `scaledmax`, and clean variants; delete or isolate their old disk caches; retrain both models; then rerun every headline evaluation. Add a mandatory split-disjointness assertion in training and evaluation startup, not just split creation.

### C2 — Real bug: headline containment measures the pre-resize box, not Stage 2's visible cube

**Evidence:** `cascade_eval.py:224-230` computes pancreas/tumor coverage against `box`, then crops and applies `ResizeWithPadOrCrop`. When any box dimension exceeds 128, that transform center-crops it (`cascade_eval.py:213-215`). The audit reports 220/800 oversized boxes, yet the 94.6%/98.9% figures are calculated before this information loss (`cascade_eval.py:297-337`). The script itself prints “would center-crop” at `cascade_eval.py:398-404`, but the headline containment does not incorporate it.

**Impact:** “pancreas 94.6% / tumor 98.9% fully contained” overstates what the segmenter actually sees. The overstatement can affect 27.5% of audited cases. It also makes the claim that the remaining 5.4% clips and oversized boxes share one measured root cause stronger than the code supports: the first is localizer-box containment, while the second is downstream cube truncation.

**Concrete fix:** calculate effective post-transform containment by applying the identical crop/pad offsets to GT masks, or report two explicitly named metrics: `localizer_box_containment` and `stage2_input_containment`. Gate deployment on the latter. For resize-to-fit, record the crop-to-cube affine/scale and score in the correct physical geometry.

## High findings

### H1 — Real bug: the robust pancreas-source fix cannot be implemented by YAML alone

**Evidence:** config lists only `pancreas.nii.gz` at `configs/level45.yaml:31-33`. More importantly, no runtime code reads `source_masks`: `build_records` hardcodes only `pancreas_path` and `lesion_path` (`src/data/dataset.py:39-50`), and `ComposeLabeld` accepts one pancreas key (`src/data/transforms.py:41-77`). `cascade_eval.preprocess_transform` likewise loads only `image`, `pancreas`, and `lesion` (`scripts/cascade_eval.py:73-85`).

Raw `outputs/mask_audit.csv` confirms 117 flagged validation cases: 101 both-source-empty, 9 subregion-recoverable, and 7 oversized combined. This independently rules out orientation/resampling as the primary zero-mask cause because `audit_masks.py:26-33` counts raw NIfTI nonzeros before MONAI. But the current shared pipeline still mishandles the recoverable and corrupt-huge cases.

**Concrete fix:** make record construction config-driven and pass separate combined/head/body/tail masks into a single deterministic label-composition transform. On a common image grid, discard the combined mask when its physical volume exceeds the registered threshold, union the remaining plausible pancreas sources, then paint lesion last. Validate source shape/affine compatibility before voxelwise union. Use this one implementation in train, evaluate, cascade, analyze, sanity, and export paths.

### H2 — Real bug: current `val_clean` discards recoverable cases and does not solve training contamination

**Evidence:** `audit_masks.py:63-76` marks subregion-recoverable cases as `bad`, and `audit_masks.py:98-102` excludes every flagged ID. Thus `val_clean.txt` has 1,683 cases and removes the 9 recoverable cases as well as the 101 empty and 7 oversized cases. No `scaledmax_clean.txt` currently exists. The audit was run only on validation; intersections show `scaledmax` already contains 10 of the validation cases known to be truly empty, but train-pool source quality has not been exhaustively audited.

**Concrete fix:** first implement the robust union/guard, then define “clean” from the resolved mask, not from combined-mask status. Audit the canonical training fold and validation fold independently. Exclude only cases whose resolved pancreas is still empty/implausible. Rebuild derived splits from canonical `train.txt`.

### H3 — Framing/reporting issue: the dedicated localizer is not pancreas-only

**Evidence:** EXP-22 invokes the ordinary `train.py` with the ordinary three-class records and DiceFocal loss. `build_model` has three output channels (`configs/level45.yaml:75`; `src/models/segresnet.py:22-31`); `ComposeLabeld` paints lesion as class 2 (`src/data/transforms.py:66-71`); the loss consumes that full label (`scripts/train.py:276-283`). Only inference selects channel 1 (`scripts/cascade_eval.py:195-201`).

**Impact:** the statements that the localizer “never sees a lesion label” and is “pancreas-only by construction” are false. This is not an inference-time oracle leak—the model receives only CT at inference—but lesion supervision can shape shared features and the pancreas output. The autonomous arm remains predicted-ROI, but the claimed clean separation between stages is overstated.

**Concrete fix:** either relabel EXP-22 as a three-class full-scan model used as a pancreas localizer, or train a true two-class/background-pancreas localizer with lesion voxels folded into pancreas (or an explicit pancreas-union target). Then compare containment.

### H4 — Real bug: `--resume` is still unsafe for best-model tracking

**Evidence:** `load_checkpoint` returns one generic `best` field (`src/training/trainer.py:40-68`). Resume assigns it to `best`, but leaves `best_val=-1` (`scripts/train.py:179-187`). The next validation therefore becomes a new best even when worse than the pre-resume best and overwrites shared and new-run `best.pt` (`scripts/train.py:322-327`). Periodic/last checkpoints save `best`, not `best_val` (`scripts/train.py:329-333`). The unique timestamp directory prevents an older archive from being deleted, but it does not make the resumed run's selected keeper correct.

Optimizer/scheduler restore failures are caught and training continues (`src/training/trainer.py:55-67`), which is useful recovery behavior but not a scientifically equivalent resume. A changed `total_iters` also reconstructs a different scheduler function before state restoration.

**Concrete fix:** checkpoint separate `best_train`, `best_val`, selection metric name, resolved config, total schedule length, freeze state, and run identity. Restore them before saving. Refuse incompatible optimizer/scheduler/config resumes unless an explicit weights-only flag is provided. Resume into the same archive or record a parent checkpoint relationship.

### H5 — Real bug/design risk: PersistentDataset caches can silently serve stale preprocessing

**Evidence:** `_cache_tag` includes only split, first spacing element, first patch element, whole-box flag, two crop values, ROI source, and train/val (`src/data/dataset.py:17-29`). It omits HU window, orientation, anisotropic spacing/patch components, whole-box transform mode, mask-source policy/guard threshold, and other deterministic preprocessing. `PersistentDataset` is created without `hash_transform` (`src/data/dataset.py:79-85`). In installed MONAI 1.6.0, the default is `hash_transform=None`, and MONAI explicitly warns that changed transforms are not encoded in cache filenames.

**Impact:** the planned union-mask fix or resize-to-fit transform can reuse old cached tensors under the same tag, silently nullifying the experiment or mixing recipes.

**Concrete fix:** hash a canonical serialization of the complete deterministic preprocessing and source-mask policy, pass a transform hash, version the cache schema, and print the resolved cache fingerprint. For the immediate fix, use a new cache root or purge only the explicitly resolved old recipe directories before retraining.

### H6 — Design risk: resize-to-fit invalidates fixed physical-volume calculations unless geometry is tracked

**Evidence:** the proposed EXP-23 will rescale each variable-size box to 128³. Current cascade specificity converts cube voxels to mm³ using fixed `1.5³` (`scripts/cascade_eval.py:162-166`, `scripts/cascade_eval.py:414-425`). After per-case resize, cube voxels have case-specific, potentially anisotropic physical sizes. The same issue would affect any millimetre margin or exported geometry applied after resizing.

**Concrete fix:** retain per-axis source-box extent and derive effective cube spacing for each case, or inverse-map predictions to the resampled/full-volume grid before volume thresholds, Dice, export, and physical-distance postprocessing. Dice is invariant to a common resampling of prediction and GT, but the 50 mm³ CADe threshold is not.

## Moderate findings

### M1 — Framing/reporting issue: the harness check does not reproduce the training preprocessing

Training whole-box crops in native space and then resamples (`src/data/transforms.py:125-139`); the cascade resamples the full scan and then crops (`scripts/cascade_eval.py:73-85`, `scripts/cascade_eval.py:218-230`). It also uses its own margin default. A ~0.03 gap is plausible, but observing a nearby aggregate does not prove per-case equivalence. Within-harness `gt-panc` versus `pred` comparisons are more defensible than treating the harness absolute as a reproduced EXP-17c score.

**Concrete fix:** factor one shared deterministic crop/mapping implementation used by training and cascade, or quantify paired per-case differences and limits of agreement. Keep the native-oracle and cascade-harness numbers distinctly labeled.

### M2 — Design risk: largest-component localization can choose a confident false blob

`cascade_eval.py:195-204` keeps only the largest predicted pancreas component. A large spurious component can replace the true pancreas; a fragmented true pancreas can lose its tail. Falling back to the whole volume happens only when prediction is completely empty (`cascade_eval.py:210-215`), not when it is anatomically implausible.

**Concrete fix:** measure component count, size, location, probability mass, elongation, and boundary contact; retain/merge plausible components; and trigger an uncertainty fail-safe when geometry is implausible. The fail-safe should expand/retry or abstain, not silently submit a crop.

### M3 — Framing/reporting issue: the GT-quality gate is heuristic and partly circular

The gate uses fixed post-resample voxel and z-span cutoffs (`cascade_eval.py:287-303`) derived after inspecting failures. It labels every excluded case a “LABEL problem, not localizer miss” (`cascade_eval.py:320-326`) without independent image review. It also computes tumor containment before applying the pancreas-quality gate (`cascade_eval.py:305-312`), so the printed tumor cohort is not formally the same valid-GT cohort.

**Concrete fix:** preregister physical-volume and extent criteria from an external/anatomical reference, report gated and ungated numbers side by side, manually adjudicate a sample blinded to model output, and apply/report consistent cohort definitions. Call exclusions “implausible reference masks,” not proven label defects, unless source audit/adjudication confirms them.

### M4 — Real bug: config advertises multiple controls that code ignores

Unwired or ignored keys include `model.deep_supervision`, `transfer.reinit_head`, `transfer.encoder_lr_scale`, `training.amp`, `training.grad_accum_steps`, `preprocessing.scale_range`, `inference.postprocess.pancreas_largest_cc`, and most of `validation` (`configs/level45.yaml:51,82,86-88,123-138,149`). Differential LR is specifically documented but `build_optimizer` creates one parameter group at one LR (`src/training/trainer.py:19-28`). `validation.best_metric` appears honored only coincidentally because the loop hardcodes lesion Dice (`scripts/train.py:322-327`).

**Concrete fix:** either wire each key with a test or mark it clearly inert/remove it. Log the fully resolved behavior, not aspirational YAML.

### M5 — Design risk: checkpoints do not contain the resolved preprocessing contract

`save_checkpoint` stores model/optimizer/scheduler/step/best and optional extra (`src/training/trainer.py:40-49`), but `train.py` passes no resolved config. `run_info.txt` records only a subset and omits ROI source, cache/source-mask policy, HU window, augmentation, and inference settings (`scripts/train.py:250-264`). Evaluation relies on manually repeated CLI flags (`scripts/evaluate.py:79-114`).

**Concrete fix:** embed the resolved config and a recipe hash in every checkpoint; have evaluation load it by default and require an explicit override acknowledgement for mismatches.

### M6 — Framing/reporting issue: “four nulls prove data is the lever” is too strong

Transfer versus scratch (EXP-09) is supported on the original disjoint dev subset, subject to its acknowledged LR/freeze confound. The four recipe experiments are useful negative results at small n, but they do not exhaust loss, sampler, context, or resolution choices. More importantly, scaled-data confirmation is currently validation-contaminated due to C1.

**Concrete fix:** say “the tested recipe changes did not improve the selected development cohort; data scaling was the strongest observed lead.” Restore the stronger causal statement only after a leakage-free scaled rerun on a frozen cohort.

### M7 — Design risk: evaluation cohorts are deterministic prefixes, not representative samples

`evaluate.py:137-141`, `cascade_eval.py:363-368`, and the containment audit at `cascade_eval.py:281-285` take the first N manifest-order cases. This supports matched comparisons but can cluster sites, years, phases, and geometry.

**Concrete fix:** use a frozen, seeded, stratified evaluation list by tumor size, phase, site/vendor, and scan geometry; publish IDs or a cohort hash. Final confidence intervals should use the full disjoint validation cohort where feasible.

### M8 — Design risk: specificity and detection sensitivity need uncertainty and consistent operating points

Specificity@50 mm³ is implemented consistently in `evaluate.py:171-189` and `cascade_eval.py:406-425`. Dice correctly returns NaN for empty GT and uses `nanmean` (`scripts/evaluate.py:37-46,164-169`; `scripts/cascade_eval.py:63-70,392-397`). `analyze_cases.py` also returns NaN, and pandas means skip it (`scripts/analyze_cases.py:34-41,113-129`). Those parts are correct.

But 90% detection sensitivity at n=40 and specificity at n=40 have wide binomial uncertainty; the threshold is repeatedly swept on the same development cases. The rule of three is valid only for exactly zero observed failures and is correctly only printed in that branch (`cascade_eval.py:338-347`), but it is not a substitute for a confidence interval when failures occur.

**Concrete fix:** freeze one operating threshold after development, report exact binomial confidence intervals for sensitivity/specificity, bootstrap patient-level Dice, and reserve the official test set for one final locked evaluation.

### M9 — Design risk: current deployment plan lacks an abstention/OOD contract

The cascade has no runtime checks for missing/corrupt inputs, affine/orientation anomalies, partial field of view, unexpected physical extent, contrast phase, scanner/site shift, implausible pancreas output, oversized crop, or low confidence. It can silently fall back to the entire volume after an empty localization (`cascade_eval.py:210-215`), then center-crop it to 128³, which is not a safe recovery.

**Concrete fix:** add preflight image/affine/FOV validation, localizer plausibility and confidence checks, effective Stage-2 containment proxies, and explicit abstain/review-required outputs. Measure failure and abstention rates by site, vendor, phase, orientation, and scan extent.

## Minor findings

### m1 — Real bug: `audit_masks.py` computes a sum, not a voxel union

`audit_masks.py:62` sums head/body/tail physical volumes. If subregions overlap, this overcounts; it also does not verify matching affines/shapes. This is adequate for discovering nonempty fallback labels but not for validating the final union.

**Concrete fix:** load the masks on a verified common grid, compute a boolean voxel union, and report overlap/disagreement metrics.

### m2 — Real bug: archive naming is timestamp-based but not guaranteed immutable

`scripts/train.py:203,248-249` uses second-resolution timestamps and `exist_ok=True`. Two launches with the same run name in one second can share a directory. Resume intentionally creates a new directory, so “immutable” is procedural rather than enforced.

**Concrete fix:** use a UUID or MLflow run ID and create with `exist_ok=False`; fail on collisions.

### m3 — Framing issue: `run_info.txt` and ledger can mislabel resume/best values

The ledger column is named `best_val_lesion` (`scripts/train.py:335-343`) even for no-validation/localizer runs, while periodic checkpoints save a generic training `best`. The localizer archive contains a `best.pt` despite validation being disabled because train-patch mean Dice selected it (`scripts/train.py:305-309`). Documentation correctly recommends `last.pt`, but artifact names remain easy to misuse.

**Concrete fix:** record `selection_metric` and `selection_value`; name keepers by metric (`best_val_lesion.pt`, `best_val_pancreas.pt`, `best_train_mean.pt`).

### m4 — Design risk: physical dilation uses minimum spacing

`src/inference/postprocess.py:56-58` converts millimetres to an isotropic iteration count using `min(spacing)`. This over-dilates axes when spacing is anisotropic. Current 1.5 mm isotropic preprocessing avoids the issue, but resize-to-fit reintroduces variable effective spacing.

**Concrete fix:** use a spacing-aware ellipsoidal structuring element or a physical-distance transform.

## Claim-by-claim verdict

- **Provided-ROI lesion Dice ~0.528, autonomous ~0.483, detection sensitivity 90%:** the code can calculate these quantities, but the current numbers are **validation-contaminated**. The autonomous arm is also not from a lesion-naive localizer. Withdraw as held-out claims pending clean retraining/evaluation.
- **Containment 94.6% pancreas / 98.9% tumor:** supported only as **pre-resize localizer-box containment on a heuristically gated, contaminated cohort**. It is not Stage-2-visible containment and not an independent validation estimate.
- **Transfer >> scratch:** directionally supported by the earlier disjoint dev-subset comparison, with the documented LR/freeze confound. Do not generalize magnitude beyond that cohort.
- **Four recipe nulls, data is the lever:** useful project evidence, but “proved/the lever” is too strong; scaled confirmation is contaminated.
- **Both models logged and archived:** verified. SQLite contains FINISHED runs named `transfer_wholebox_scaledmax` and `localizer_fullscan_scaledmax`; both timestamped archive directories contain checkpoints. This establishes provenance, not validity.
- **No train/val overlap:** true for canonical `train.txt` versus `val.txt`, false for all scaled derived splits.
- **Zero masks are a MONAI bug:** rejected. Raw nibabel confirms source defects. The loader robustness hole remains real and recoverable cases are currently mishandled.

## Hyperparameters and experiments worth tuning after correctness fixes

Do not tune against the contaminated cohort. After rebuilding disjoint splits and fixing mask/caches:

1. **Localizer recall/box reliability:** train a true pancreas target; sweep probability threshold, component-merging policy, and margin against effective Stage-2 containment and crop scale—not pre-resize containment alone. This should move cascade failure rate more directly than lesion Dice.
2. **Stage-2 scale handling:** compare resize-to-fit, a larger 160³ cube, and aspect-preserving resize-plus-pad. Per-axis distortion from unconditional 128³ resize may hurt morphology; a maximum-spacing or letterbox policy is safer.
3. **Lesion over-segmentation:** sweep Tversky/Focal-Tversky false-positive weighting, focal gamma, and `lambda_dice:lambda_focal` on a frozen disjoint cohort. EXP-07 tested only background inclusion, not the wider loss family.
4. **Freeze and LR:** test no freeze versus 1-3 epochs; implement the advertised encoder LR scale before calling it tested. EXP-09 confounds initialization with LR/freeze.
5. **Operating point:** select lesion probability and 50 mm³ threshold on development data once, with exact sensitivity/specificity CIs; do not optimize on the final test set.

## Top three Week 4 fixes

1. **Rebuild all scaled splits from canonical `train.txt`, add startup leakage assertions, invalidate affected caches, retrain both models, and rerun the headlines.** Nothing is higher value.
2. **Implement one shared, config-driven pancreas resolver (combined + head/body/tail union, affine checks, >300 mL combined guard), then rebuild clean splits from resolved masks.** Do not merely edit YAML.
3. **Measure and fix effective Stage-2 containment, with correct geometry/volume accounting and an abstention fail-safe.** Compare resize-to-fit with larger/aspect-preserving cubes on the clean disjoint cohort.

## Correct and well done

- Lesion-over-pancreas precedence in `ComposeLabeld` is correct (`src/data/transforms.py:66-71`). A multi-source pancreas resolver should feed its resolved mask into this same paint-order rule.
- Image and GT are cropped through the same predicted box and resized identically in the current cascade (`scripts/cascade_eval.py:228-230`).
- Sliding-window stitching on CPU with windows on MPS is correctly and consistently implemented (`src/inference/sliding_window.py:15-26`; `scripts/cascade_eval.py:88-96`).
- Empty-GT Dice handling, `ignore_empty=True`, and separate pancreas/lesion reporting are correct in the reviewed metric paths.
- SuPreM prefix stripping, `net` unwrapping, and shape-matched loading are reasonable (`src/models/segresnet.py:34-57`), though a future hardening should assert that only the expected head tensors are missing/mismatched rather than merely print counts.
- The checkpoint archives and MLflow runs exist for both headline models; the provenance repair is useful even though resume selection still needs correction.
