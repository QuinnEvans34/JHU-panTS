# Pancreas localization and ROI policy

**Status:** Approved Plan 05 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P05-01, P05-02, P05-04 through P05-06  
**Governing plan:** [`../implementation/05-autonomous-imaging.md`](../implementation/05-autonomous-imaging.md)

## Purpose

The localizer does not need to draw the final pancreas perfectly. It must reliably place the pancreas
and nearby suspected lesions inside a manageable Stage 2 field of view without using lesion evidence
at inference. This document separates four questions that a single Dice score would hide:

1. Did the localizer find the correct anatomical region?
2. Which predicted components become the ROI?
3. Does the physical margin retain the target?
4. Does the final Stage 2 mapping preserve everything the selected ROI contained?

## Baseline candidate

The proposed D-204 answer is a newly trained dedicated binary pancreas localizer using the existing
MONAI/SegResNet family and full-volume sliding-window inference. It is a baseline because it is small,
compatible with the validated pipeline structure, trainable on the workstation, and directly
optimizes the organ needed by the cascade. Architecture is configurable; “SegResNet” is not a promise
that Plan 06 cannot revisit.

### Input and target

- Input: canonical full CT intensities only.
- Output: background and pancreas logits/probabilities.
- Training target: a resolved pancreas annotation permitted as `training_target`.
- Excluded from target/input: lesion masks, lesion-union masks, report findings, provided boxes,
  evaluation labels, and source-derived tumor status.
- PanTS is the baseline source. A PANORAMA pancreas annotation is eligible only after its Plan 03 QC
  and allowed-use rules pass and only in a separately declared source-aware run.

The localizer target remains unchanged if a lesion mask is deleted, altered, or moved. This becomes a
fixture-based invariance test.

## Candidate-to-ROI sequence

The frozen ROI policy applies these conceptual steps:

1. Validate the localizer probability grid and map it to the declared localizer space.
2. Apply a development-selected probability/decision rule.
3. Enumerate connected candidate components and physical properties.
4. Apply one frozen component-selection strategy.
5. Create an axis-aligned box around the selected union in the canonical/world-aligned space.
6. Expand by a frozen margin in millimeters and clip to the available scan field.
7. Run plausibility and boundary checks.
8. Map the entire selected box into the Stage 2 tensor with the frozen normalization policy.
9. Record effective target containment, resolution, padding and crop cost for evaluation only.

No hidden rescue step may inspect a reference annotation after Step 2.

## Component strategies to compare

| Candidate | Description | Primary risk |
|---|---|---|
| Largest component | Keep only the largest predicted pancreas component | A disconnected but real tail/body fragment is discarded |
| Plausible-near-component union | Keep the primary component plus physically plausible components within a frozen distance/box-inflation rule | A nearby false positive enlarges the crop |
| Probability envelope | Define a region from a calibrated high-recall probability support/quantile | Low-probability noise can approach a whole-scan box |

The recommended starting policy is plausible-near-component union because it can preserve fragmented
anatomy without accepting every distant false positive. It is not locked until the development
comparison. Every component and accept/reject reason remains in the localization record.

Component size, distance and bounding rules use physical units. A voxel-count threshold is not
portable across spacing.

## Margin and box behavior

- Margin is expressed in millimeters and converted per axis using the current grid transform.
- Requested and realized margins are both recorded because scan boundaries may clip the request.
- Contact with any source boundary creates a warning and a per-face clearance record.
- A box cannot be enlarged from a lesion reference during training evaluation or inference.
- The box may include tissue outside the pancreas; high recall is more important than a tight organ
  outline, provided Stage 2 resolution and runtime remain acceptable.
- Box dimensions, physical volume, scan-volume fraction and component-union volume are recorded before
  normalization.

## Stage 2 normalization

### Proposed baseline: aspect-preserving letterbox

1. Compute one uniform scale factor from the selected box and Stage 2 target shape.
2. Resample every spatial axis by that same factor.
3. Symmetrically pad the remaining dimensions to the fixed tensor shape.
4. Record any odd-voxel padding asymmetry deterministically.

This guarantees that the selected ROI is not center-cropped and avoids anatomy-dependent per-axis
distortion. The effective millimeter spacing may differ by study, so its distribution is a selection
and subgroup variable.

### Fallbacks

- **Larger fixed cube at fixed spacing:** preferred if the workstation handles it and letterbox
  downsampling is too coarse.
- **Fixed-spacing variable ROI with Stage 2 sliding windows:** preserves resolution but may lose the
  whole-organ-in-one-view advantage and increase runtime.
- **Independent per-axis resize:** not a baseline fallback because it distorts anatomy differently by
  axis.
- **Center crop after pad/resize:** prohibited because it can silently remove selected anatomy.

## Development selection design

The localization-policy cohort is frozen and train-disjoint. Candidate settings are selected before
the autonomous baseline and never from publisher-test output.

### Metrics

| Metric | Why it matters |
|---|---|
| Empty/failed localization rate | Direct cascade failure |
| Mean and per-case pancreas containment | Whether Stage 2 receives the organ |
| Lesion containment on eligible positive references | Diagnostic of whether nearby tumor remains visible; evaluation only |
| Fraction of studies above frozen containment levels | Means can hide a severe tail |
| Minimum/per-face clearance | Identifies direction and magnitude of clipping |
| Effective post-normalization containment | Detects loss caused after an apparently good box |
| ROI physical dimensions/volume and scan fraction | Measures background inflation |
| Effective Stage 2 spacing and scale | Measures resolution sacrificed to fit |
| Boundary contact and ambiguous-component rate | Predicts unsafe/uncertain cases |
| Full localizer and Stage 2 runtime/peak memory | Keeps the policy feasible |

Reference containment is calculated by the evaluation join. It never enters the localization
prediction artifact or decision at runtime.

### Selection rule

1. Freeze candidate thresholds, component rules, margins, tensor sizes and warning/failure limits.
2. Reject any setting that violates the frozen empty/failure or effective-containment bar.
3. Identify settings within the frozen tolerance of the best safe containment result.
4. Among them, choose the smallest/faster crop with acceptable effective resolution.
5. Freeze the complete ROI policy ID before the Week 5 autonomous baseline.

If no candidate passes, do not weaken the bar after viewing the same results. Register a new localizer
or mapping candidate and a new selection round.

## Training ROI simulation

Stage 2 training uses pancreas-only reference boxes because they provide stable training supervision.
To reduce ideal-box versus predicted-box mismatch:

- apply the same physical margin and letterbox code used at inference;
- add bounded translation, scale and per-face perturbations whose range is frozen from localizer
  development errors;
- never inspect lesion extent when accepting or expanding a jittered box;
- record when training lesion voxels fall outside the jittered box rather than secretly repairing it;
  and
- keep the unjittered provided-region reference available as a separately labeled evaluation mode.

If autonomous performance falls despite good containment, predicted-ROI training or out-of-fold
localizer crops becomes a Plan 06 candidate rather than an unrecorded baseline change.

## Plausibility and warning inputs

The policy records but does not invent hard limits until the development audit measures them:

- zero/near-zero predicted pancreas support;
- implausibly small or large physical component volume;
- excessive number of components or distant competing components;
- selected box occupying an excessive scan fraction;
- contact with one or more scan faces;
- extreme scale/downsampling needed to fit Stage 2;
- nonfinite or invalid probability output; and
- localizer runtime or memory outside the resource envelope.

Stable thresholds live in the ROI-policy artifact. Changing one invalidates the cascade bundle and
predictions.

## Tests

- lesion-label invariance of localizer target and training box;
- deterministic component enumeration and tie-breaking;
- nearby versus distant component fixtures;
- millimeter margin on anisotropic spacing;
- boundary clipping with realized-margin record;
- no loss of ROI voxels through letterbox mapping;
- uniform rather than per-axis scale;
- deterministic odd padding;
- effective containment measured after mapping;
- empty, fragmented, widespread and low-probability outputs;
- candidate selection reproducibility from frozen input table; and
- publisher-test identity rejection in policy selection.

## Evidence required to freeze the policy

- candidate grid and preregistered selection rule;
- development cohort ID/membership hash and reference-quality counts;
- per-study candidate table;
- aggregate containment/crop/scale/failure/runtime report;
- selected ROI-policy record and derivation hash;
- rejected candidates and reasons; and
- representative overlays for success, boundary, fragmentation and failure cases.
