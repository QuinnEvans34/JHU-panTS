# Autonomous imaging input and output contract

**Status:** Approved Plan 05 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/05-autonomous-imaging.md`](../implementation/05-autonomous-imaging.md)

## Purpose

This contract makes autonomy structural. The prediction path accepts an image-only record whose type
cannot contain annotations or a provided region. Evaluation reads a different reference record only
after prediction publication. Ignoring an annotation argument is insufficient because the code could
still discover it from a dataset record, sibling directory, or shared transform.

## Image-only inference study

The planned `inference-study` record contains:

| Field | Requirement |
|---|---|
| `schema_version` | Version of this input boundary |
| `study_id` / `subject_id` | Canonical Plan 01/02 identities |
| `source` / `source_snapshot_id` | Pinned source and snapshot identity |
| `ct` | Relative/root-alias file reference, bytes, media type, content hash, shape, dtype |
| `source_geometry` | Source shape, selected affine and its source, qform/sform codes, voxel sizes, orientation, units |
| `allowed_metadata` | Non-label fields retained for provenance/subgroup reporting, such as acquisition fields when licensed and non-identifying |
| `manifest_id` | Unified manifest version that resolved this input |

The baseline model consumes CT voxel values only. Allowed acquisition metadata is recorded for
lineage and subgroup evaluation; it does not become a model input unless Plan 06 preregisters that
change.

### Forbidden fields and discovery

The autonomous record cannot contain:

- annotation IDs, collections, roles, paths, filenames, or label availability;
- pancreas/lesion arrays, boxes, centroids, volumes, statuses, or reference findings;
- a report-derived tumor status, radiology conclusion, or lesion location;
- a provided crop, pre-cropped CT, demo cube, or reference reveal state; or
- an evaluation metric or selection label.

Autonomous code receives the file reference from this record. It does not glob a source study
directory, infer a label sibling path, load a historical `results.json`, or call a dataset builder that
returns image and label together.

## Model records and cascade bundle

The localizer and segmenter each have a model record containing:

- model version and immutable checkpoint file reference/hash;
- architecture and task/output classes;
- training cohort and annotation-use contract;
- resolved training/preprocessing configuration;
- initialization source and tensor-load audit;
- code/environment/run identity; and
- checkpoint selection metric, value, step, and evaluation cohort.

The `cascade_bundle` contains:

| Field | Meaning |
|---|---|
| `cascade_bundle_id` | Derivation-based identity for the complete two-stage inference system |
| `localizer_model_version_id` | Exact binary pancreas localizer |
| `segmenter_model_version_id` | Exact three-class pancreas/lesion segmenter |
| `localizer_preprocessing_id` | Full-volume orientation, spacing, intensity and sliding-window recipe |
| `roi_policy_id` | Threshold, components, physical margin, plausibility and failure policy |
| `segmenter_preprocessing_id` | Letterbox/tensor/intensity recipe and source-restoration rules |
| `inference_config_sha256` | Complete resolved inference configuration hash |
| `component_hashes` | Full checkpoint/config/policy hashes used to derive the bundle |

Changing either checkpoint, threshold, component rule, margin, normalization, tensor size, intensity
window, probability interpolation, or discretization rule creates a new cascade bundle and new
predictions.

## Localization prediction

For each study, localization produces a versioned intermediate record with:

- study, prepared-volume, localizer model, and localizer configuration identities;
- terminal status: `localized`, `localized_with_warnings`, or `failed`;
- probability and raw mask file references when produced;
- threshold and component-policy version;
- all component summaries and the selected component IDs;
- selected bounding region in localizer voxels and world-space millimeters;
- requested and clipped physical margin;
- boundary contact, region extent/volume, image-fraction, and plausibility indicators;
- confidence/quality proxy plus its method name; and
- warning/failure codes, runtime, window count, and resource evidence.

This localizer record is not the final pancreas contour and never contains Dice or reference
containment. Those are evaluation records.

## Spatial transform record

Every prediction references one immutable transform record. At minimum it contains:

- source shape, dtype, selected affine, orientation and units;
- canonical/localizer shapes and affines;
- crop bounds in localizer indices and world coordinates;
- physical margin and boundary clipping;
- Stage 2 input shape, uniform scale, per-axis padding and effective spacing;
- forward and inverse matrices/operations in applied order;
- image/probability/mask interpolation modes and alignment conventions;
- rounding rules and library/component versions; and
- landmark/round-trip validation summary.

Detailed requirements appear in [`SPATIAL-TRANSFORMS.md`](SPATIAL-TRANSFORMS.md).

## Autonomous prediction record

Each requested study produces one prediction record with:

| Field | Meaning |
|---|---|
| `prediction_id` | Derivation from study, CT hash, cascade bundle and inference configuration |
| `prediction_mode` | Always `autonomous` for this path |
| `status` | `completed`, `completed_with_warnings`, or `failed` |
| `study_id` / input reference | Exact image-only input identity |
| `cascade_bundle_id` | Complete localizer/segmenter system identity |
| `localization_prediction_id` | Exact Stage 1 output and ROI decision |
| `spatial_transform_id` | Exact forward/inverse transform |
| `raw_files` | Source-space pancreas/lesion masks and preserved probability maps |
| `derived_measurement_id` | Optional separately versioned measurements/post-processing |
| `warnings` / `failure` | Stable codes, stage, severity, safe explanation and details reference |
| `timing` | Preflight, localizer, ROI, segmenter, restore, validation and total durations |
| `lineage` | Source, manifest, models, config, code, environment and workflow run |

For completed predictions, source-space pancreas and lesion masks are required. The baseline
prediction set also preserves the source-space lesion probability map and localizer diagnostic
probability. For failed predictions, model files may be absent, but failure evidence and completed
upstream artifact references remain required.

## Raw and derived outputs

### Raw prediction

“Raw” means the class probabilities restored to source space and discretized with the frozen base
rule before lesion component deletion or operating-point post-processing. It is immutable.

Required validation includes:

- exact source shape and affine agreement under the spatial contract;
- finite probabilities within the defined numerical range;
- valid mask labels and integer dtype;
- pancreas/lesion files reference the same source grid;
- file sizes/hashes and completion marker; and
- no reference/evaluation identity in prediction lineage.

### Derived processing and measurements

A derived record names the raw prediction and a separate processing/measurement configuration. It
may contain:

- lesion-component ID, voxel count, physical volume, centroid and bounds;
- component probability summaries;
- maximum three-dimensional span under a named method;
- pancreas and total lesion volume;
- candidate worklist features; and
- warnings about tiny, boundary-touching, fragmented, or implausible output.

Every lesion component remains visible in the canonical component table before a later threshold or
filter is applied. A cleaned mask cannot overwrite or masquerade as the raw mask.

## Prediction-set completeness

A prediction set is controlled by a requested cohort or explicit study list and contains:

- prediction-set ID and derivation hash;
- requested cohort/list identity and membership hash;
- cascade bundle and inference config;
- one terminal record for every requested study;
- counts by status, warning, failure, source and resume state;
- deterministic ordered member index; and
- checksums/completion evidence.

Publication fails if a requested study is missing, duplicated, or silently excluded. A failed study
is a complete prediction-set member with a failed prediction, not a missing row.

## Evaluation join

Plan 06 receives a published prediction set and separately resolves protected reference annotations.
The join validates exact study identity and cohort role. It may calculate localization containment,
segmentation metrics, detection outcomes and subgroup results. It does not alter prediction records,
files, warnings or failure codes.

A matching provided-region reference run:

- uses `prediction_mode=provided_region_reference`;
- names the pancreas reference annotation used for its ROI;
- never uses lesion extent to form the ROI;
- creates distinct transform, bundle/inference, prediction and prediction-set identities; and
- remains visibly separate in every report and case package.

## Case-package compatibility

The current case-package schema exposes one model version. Plan 05 will revise it compatibly so the
UI can display a cascade-bundle ID and both component model versions while continuing to accept the
same scientific package through static files or FastAPI. The package does not need localizer
probability files for ordinary review, but it retains their lineage and relevant warnings.

## Validation fixtures

- valid image-only study;
- autonomous input containing a forbidden annotation/ROI field;
- valid completed, warned and failed predictions;
- cascade bundle with one component hash changed but old bundle ID retained;
- prediction with a source-grid shape or affine mismatch;
- missing study and duplicate study in a prediction set;
- failed study incorrectly omitted from status counts;
- autonomous record containing a provided-region annotation ID; and
- provided-region record whose ROI was built from a lesion union.
