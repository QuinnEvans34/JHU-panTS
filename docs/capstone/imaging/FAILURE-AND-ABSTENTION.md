# Autonomous failure, warning, and abstention contract

**Status:** Approved Plan 05 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P05-08, P05-11, and P05-13  
**Governing plan:** [`../implementation/05-autonomous-imaging.md`](../implementation/05-autonomous-imaging.md)

## Purpose

An autonomous system must represent cases it cannot process safely. A skipped study, blank mask, or
ground-truth fallback can make metrics look better while hiding the exact failure autonomy introduces.
This contract guarantees one visible terminal record per requested study and separates scientific
failure from orchestration/resource failure.

## Terminal prediction statuses

| Status | Meaning | Output expectation |
|---|---|---|
| `completed` | All required stages and validations passed without a governed warning | Source-space raw masks/probabilities, transform and lineage |
| `completed_with_warnings` | Valid source-space prediction exists, but one or more frozen caution conditions occurred | Same files plus warning records |
| `failed` | No safe consumable prediction could be published | Failure record, completed upstream references, logs/details; mask files not required |

An abstention is represented as a failed prediction with an abstention-class failure code, not as a
fake all-background mask. A no-lesion prediction is a valid completed prediction whose lesion output
is empty under the frozen base decision rule.

## Failure stages and initial codes

### Input/preflight

| Code | Condition | Behavior |
|---|---|---|
| `INPUT_UNREADABLE` | CT cannot be opened or decoded | Fail before model compute |
| `INPUT_HASH_MISMATCH` | Bytes differ from registered reference | Fail closed and quarantine conflicting input reference |
| `INPUT_DIMENSION_UNSUPPORTED` | Not one supported 3D volume | Fail before preprocessing |
| `INPUT_NONFINITE` | Nonfinite voxel or geometry values | Fail before model compute |
| `AFFINE_INVALID` | Missing, singular, nonfinite or ambiguous unsupported affine | Fail before model compute |
| `PHYSICAL_GEOMETRY_UNSUPPORTED` | Spacing, units, field of view or obliquity outside frozen policy | Fail or caution exactly as policy states |

### Localization/ROI

| Code | Condition | Behavior |
|---|---|---|
| `LOCALIZATION_EMPTY` | No candidate support under frozen rule | Abstain; do not start Stage 2 |
| `LOCALIZATION_AMBIGUOUS` | Competing/distant components cannot be resolved safely | Abstain or caution under frozen policy |
| `LOCALIZATION_IMPLAUSIBLE` | Physical volume/extent/scan fraction outside frozen range | Abstain; preserve diagnostics |
| `ROI_BOUNDARY_CONTACT` | Requested margin reaches source field boundary | Warning if mapping remains valid; otherwise fail |
| `ROI_EFFECTIVE_RESOLUTION_LOW` | Letterbox downsampling exceeds frozen limit | Warning or fail before Stage 2 as frozen |
| `ROI_MAPPING_INVALID` | Crop/scale/pad transform cannot be inverted or validated | Fail before Stage 2 publication |

### Segmenter/restoration/publication

| Code | Condition | Behavior |
|---|---|---|
| `SEGMENTER_INFERENCE_FAILED` | Model/runtime failure after a valid ROI | Fail; retain localization artifact |
| `PREDICTION_NONFINITE` | Logits/probabilities invalid | Fail; no mask publication |
| `RESTORE_FAILED` | Inverse transform or source placement fails | Fail; no source-space mask publication |
| `SOURCE_ALIGNMENT_FAILED` | Restored shape/affine/grid validation fails | Fail; quarantine partial output |
| `OUTPUT_SCHEMA_FAILED` | Files exist but manifest/record invalid | Fail and quarantine |
| `OUTPUT_INTEGRITY_FAILED` | Content hash/size/completion verification fails | Fail and quarantine |

### Resource/orchestration

| Code | Condition | Ownership |
|---|---|---|
| `ROOT_UNAVAILABLE` | Required configured root missing/wrong | Plan 04/10 retry classification |
| `CAPACITY_INSUFFICIENT` | Forecast plus reserve unavailable | Plan 04/10, fail before compute |
| `ACCELERATOR_UNAVAILABLE` | Selected device cannot execute | Plan 04/10 fallback/decision |
| `RUN_CANCELLED` | Operator requests stop | Plan 04 terminal run/recovery behavior |

Resource errors do not become anatomical abstentions. Their prediction/run records remain visibly
different so product limitations are not confused with an unplugged drive.

## Warning record

Each warning has a stable code, severity, stage, safe human-readable message, structured measurements,
policy version and details/log reference. It does not include absolute private paths or a diagnostic
claim.

Warnings never change model probabilities. A warning may affect whether the result is eligible for
release/demonstration under a separately versioned selection policy.

## Prohibited recovery behavior

- Look up a ground-truth box, annotation, known lesion location or demo mask.
- Replace the failed localizer with a prior-project checkpoint.
- Segment an arbitrary center crop and call it autonomous.
- Fall back to the entire volume unless a separately preregistered image-only fallback bundle exists.
- Publish an all-background mask as though the model confidently found no lesion.
- Omit the case from the prediction-set index or metric denominator without a Plan 06 rule.
- Delete the failed attempt after a successful retry.

## Prediction-set accounting

For requested count `N`:

```text
N = completed + completed_with_warnings + failed
```

Study IDs are unique and ordered deterministically. Retries create attempt evidence but only one
terminal prediction identity for one bundle/config request. A recovery using changed configuration
creates a new prediction and prediction-set version.

Reports include status and code counts overall and by source, annotation-quality/evaluable-reference
status, acquisition subgroup and relevant geometry group. Small groups retain counts and uncertainty.

## Evaluation handoff

Plan 06 must freeze how each terminal state enters each metric before the baseline:

- a positive case that fails autonomy cannot be credited as detected;
- a negative failed/abstained case cannot be silently credited as a true negative;
- selective performance among completed cases is secondary and paired with coverage/abstention rate;
- pipeline failure rate remains separate from anatomical model failure; and
- provided-region rescue may diagnose the source of error but never replace the autonomous outcome.

This contract does not force one statistical convention for every metric. It prevents disappearance
and makes the convention auditable.

## User-facing behavior

The later review interface may show:

- `completed`: proposed contours and ordinary non-diagnostic caveat;
- `completed_with_warnings`: contours plus a clear request for closer review and the warning reason;
- `failed/abstained`: no proposed contour, an explanation that automated processing could not produce
  a valid result, and the recorded failure ID.

It must not show “no tumor” or similar diagnostic language for any state.

## Tests

- each failure code creates the correct terminal record and prevents forbidden downstream work;
- empty localization produces no Stage 2 call and no masks;
- no-lesion completed prediction is distinguishable from failure;
- warning policy is deterministic at exact boundary values;
- failed case remains in prediction-set count/index;
- retry preserves the first failed attempt;
- changed recovery configuration creates new prediction identity;
- resource failure is not labeled anatomical abstention;
- failure messages reveal no absolute paths or tracebacks; and
- autonomous failure cannot invoke a reference/provided-region code path.

## Governance

Thresholds separating warnings from failures are development-measured values stored in the ROI or
input policy. Changing a threshold invalidates the cascade bundle/predictions. New codes may be added
compatibly, but changing the meaning or severity of an existing code requires a versioned contract
change and regression review.
