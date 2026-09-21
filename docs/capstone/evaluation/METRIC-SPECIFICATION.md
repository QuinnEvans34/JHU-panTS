# Metric specification

**Status:** Approved Plan 06 design baseline  
**Version:** 0.1 planning draft; executable metric version not yet assigned  
**Owner:** Quinton Evans  
**Decision:** P06-04 through P06-10  
**Governing plan:** [`../implementation/06-evaluation-and-model-experimentation.md`](../implementation/06-evaluation-and-model-experimentation.md)

## Purpose

This document defines the intended meaning of PROWL's metrics before implementation. Exact schema
field names, tolerances, and any external-compatibility mode are frozen with golden fixtures before a
formal baseline. No report may use the short words `Dice`, `sensitivity`, `specificity`, or `AUC`
without resolving them to a named metric version and reference population.

## Evaluation unit and coordinate space

- The atomic prediction/evaluation unit is one registered study.
- Subject is the resampling/grouping unit whenever a source can contain repeated studies per subject.
- Voxel overlap is computed only after a prediction and reference validate on the same source CT grid
  and affine.
- Physical volume and distance use the source affine/world geometry, not an assumed isotropic voxel.
- Evaluation joins references after autonomous prediction publication; reference content cannot alter
  prediction identity or processing.
- Aggregate rows are derived from immutable per-study/component rows.

## Reference eligibility

Each metric states its required reference evidence:

| Metric family | Eligible reference |
|---|---|
| Pancreas segmentation | Valid source-space pancreas `evaluation_reference` annotation |
| Lesion segmentation | Valid source-space lesion `evaluation_reference` with positive target evidence |
| Mask-evidence detection | Valid positive or negative lesion target evidence derived under the named mask convention |
| Metadata/report detection | Separately identified valid target evidence from that source; never pooled with mask evidence |
| Localization containment | Valid pancreas reference; lesion containment additionally requires positive lesion reference |
| Tumor-wise sensitivity | Positive lesion reference whose component topology passes the metric QC policy |

Unknown, missing, invalid, quarantined, or training-only annotations do not become negative.

## Prediction layers

Every metric names one layer:

- `raw_argmax` — source-space class mask from restored continuous class probabilities and the base
  discretization rule.
- `raw_probability` — source-space continuous class probability used for curves and policy analysis.
- `derived:<policy_version>` — a separately versioned threshold/denoising/anatomical policy.
- `provided_region_reference` — same selected segmenter with pancreas-only reference ROI; not
  autonomous.

Raw artifacts never change when a derived policy is added. A comparison cannot silently use raw on
one arm and derived on another.

## Completion and coverage

For a requested prediction set of size `N`:

```text
N = completed + completed_with_warnings + failed
coverage = (completed + completed_with_warnings) / N
failure_rate = failed / N
```

Also report counts/rates by terminal code, source, and the required error-analysis groups. A completed
prediction can still be unevaluable for a particular metric if its reference evidence is missing or
invalid; this affects the metric-eligible denominator but not autonomous coverage.

## Segmentation masks

For the three-class source-space label:

```text
background = label 0
pancreas_parenchyma = label 1
lesion = label 2
pancreas_region = label in {1, 2}
```

`pancreas_region` measures the full organ region including lesion voxels. `pancreas_parenchyma`
preserves continuity with the project's historical mutually exclusive class-1 metric. Both are
reported with explicit names; neither may be shortened to an ambiguous `pancreas_dice` field.

### Dice definition

For binary prediction `P` and reference `G`:

```text
Dice(P,G) = 2 * |P intersect G| / (|P| + |G|)
```

Per-study conventions:

| Reference/prediction state | Primary lesion-positive Dice | Separately named whole-cohort absence convention |
|---|---|---|
| GT positive, prediction positive | Standard Dice | Same value |
| GT positive, prediction empty | 0 | 0 |
| GT empty, prediction positive | Not eligible/NaN | 0 |
| GT empty, prediction empty | Not eligible/NaN | 1 |
| Prediction failed | No manufactured mask/NaN | No manufactured mask/NaN |

Primary reported segmentation metrics:

- `pancreas_parenchyma_dice_mean` over valid pancreas-reference studies;
- `pancreas_region_dice_mean` over valid pancreas-reference studies; and
- `lesion_dice_positive_mean` over valid lesion-positive-reference studies.

Each includes eligible `n`, mean, median, quartiles, bootstrap interval, and per-study values. The
whole-cohort empty-as-absence convention may be published only as a secondary explicitly named
metric; it cannot replace lesion-positive Dice.

### Optional surface metric

A normalized surface Dice or surface-distance metric is useful only after Plan 09 freezes:

- physical tolerance in millimeters and its rationale;
- surface extraction/connectivity;
- empty/failed behavior;
- anisotropic geometry handling; and
- tested library/version or independent fixture values.

It is secondary unless the approved plan is amended.

## Localization and effective containment

Localization is scored twice:

1. on the localizer's source/canonical output; and
2. after ROI selection, margin, scale/pad, and final Stage 2 mapping.

The second value is the effective quantity because it measures what the segmenter can actually see.

For target mask `T` and final visible ROI support `R` mapped to source space:

```text
containment(T,R) = |T intersect R| / |T|
```

Report:

- pancreas effective containment distribution;
- lesion effective containment distribution on lesion-positive references;
- fraction of studies at frozen containment bands;
- empty/ambiguous/implausible localization rates;
- ROI volume and source-volume fraction;
- effective spacing/downsampling by axis; and
- boundary-contact and low-resolution warnings.

A failed localizer has no containment mask fabricated for it; it remains a failure in coverage and
end-to-end detection accounting.

## Patient-level candidate and detection

A patient/study lesion candidate is derived from a frozen policy applied to source-space lesion
probability and, where selected, predicted pancreas/anatomical output. The policy records:

- continuous case score definition;
- voxel probability threshold(s);
- multi-lesion-preserving denoising;
- anatomical constraint;
- component connectivity;
- minimum component or total volume in mm3;
- how multiple components combine into a case decision; and
- warning/failure behavior.

No value is called probability of disease. It is a model-derived review score.

For reference positive/negative and a frozen candidate rule:

```text
sensitivity = TP / (TP + FN)
specificity = TN / (TN + FP)
F1 = 2TP / (2TP + FP + FN)
```

Always show TP, FN, TN, and FP counts beside rates.

### Conditional and end-to-end accounting

- `completed_case_sensitivity` and `completed_case_specificity` use the standard formulas over
  completed valid predictions only and appear beside coverage.
- `end_to_end_detection_sensitivity = detected eligible positives / all requested eligible positives`;
  a failed positive receives no detection credit.
- `end_to_end_negative_clearance_rate = correctly unflagged eligible negatives / all requested
  eligible negatives`; a failed negative receives no clearance credit.
- Negative-clearance rate is not labeled specificity because a technical abstention is neither an
  anatomical false positive nor a true negative.
- Coverage and failure-code counts appear beside both.

This prevents a system from gaining apparent specificity by abstaining on difficult negatives while
still allowing model behavior among processed cases to be diagnosed.

### Operating curve

Development evaluation emits the complete preregistered grid over relevant probability and physical
volume thresholds rather than one favorable point. Each row contains:

- probability/score and volume/component policy;
- TP/FN/TN/FP and coverage;
- sensitivity, specificity, F1, and Wilson intervals;
- lesion-positive Dice under that derived policy where meaningful;
- false-positive component count/volume per negative study; and
- policy version.

D-208 selects one interpretable review-ordering score and operating policy from development evidence
and reviewer need. That complete identity is frozen before publisher-test inference/evaluation.

### AUC

AUC is computed only from a continuous, precisely named case score and a precisely named binary
reference definition. The result states score construction, ties, positive/negative counts, and
interval method. AUC from maximum lesion probability, total predicted lesion volume, or a composite
are different metrics and never share one label.

## Lesion components and tumor-wise sensitivity

### Component construction

- Use the source-space lesion reference and the named raw/derived prediction layer.
- Use 26-connectivity in 3D unless an external compatibility mode states otherwise.
- Record component voxel count, physical volume, centroid/world bounds, and parent study.
- Do not apply largest-connected-component selection.
- Exclude only components removed by the explicitly named multi-lesion-safe policy.

### Matching

Construct all prediction/reference pairs satisfying the preregistered overlap criterion. Match
one-to-one by:

1. maximum number of valid matches;
2. maximum total overlap quality among maximum-cardinality solutions; and
3. stable component identity as the final tie-break.

Each reference lesion is matched at most once and each prediction component is matched at most once.
Unmatched references are misses; unmatched predictions are false-positive components; additional
predictions touching one already-matched lesion remain duplicates/unmatched rather than extra true
positives.

```text
tumor_wise_sensitivity = matched_reference_lesions / eligible_reference_lesions
false_positive_components_per_scan = unmatched_prediction_components / eligible_scans
```

The exact primary overlap criterion is frozen before baseline results. If published benchmark code
does not disclose its matching rule, PROWL labels its metric internal and publishes a sensitivity
analysis across agreed overlap/Dice/coverage thresholds rather than claiming exact compatibility.

## Uncertainty and aggregation

### Resampling unit

- Use subject-level resampling when multiple studies may share one subject.
- Use study-level resampling only for sources whose approved identity contract is
  `study_as_subject_fallback`; state that limitation.
- Sample paired control/treatment results together by subject/study identity.
- Preserve all repeated studies from a selected subject within one resampled cluster.

### Default interval families

- Sensitivity and specificity: Wilson 95% interval on the named denominator.
- Mean/median Dice, containment, volume, and runtime: percentile bootstrap 95% interval using the
  registered seed/draw count, unless Plan 09 validates a stronger declared method.
- Controlled paired difference: paired cluster-bootstrap 95% interval plus win/loss/tie counts and
  the full paired-difference distribution.

Every aggregate includes eligible `n`, excluded/unevaluable `n`, terminal failures, interval method,
seed, draws, and grouping unit. Small subgroups remain descriptive.

## Subgroup fields

Required when available and sufficiently populated:

- source dataset;
- annotation source/provenance/quality stratum;
- contrast phase;
- lesion physical volume band and lesion count;
- manufacturer/acquisition fields;
- spacing, slice thickness, and geometry-warning band;
- localizer/ROI warning/failure class; and
- subject/study identity assurance.

The report shows counts before performance. Sparse/unknown groups are visible rather than imputed.
No subgroup becomes a new model-selection target after publisher-test results.

## Autonomous versus provided-region decomposition

The selected segmenter, source CTs, references, discretization, and metric version remain fixed.
Only ROI source changes:

- `autonomous`: predicted localizer/ROI policy;
- `provided_region_reference`: pancreas-only evaluation reference ROI.

Report paired differences in effective containment, pancreas/lesion Dice, detection, failure, and
runtime. Provided-region output may explain localization loss but never replace an autonomous failure
or headline prediction.

## Required golden fixtures

- perfect pancreas/lesion and perfect-empty negative;
- positive reference with empty prediction;
- negative reference with false-positive component;
- class-1/lesion swap demonstrating parenchyma versus region Dice;
- two reference lesions with correct, missed, duplicate, merged, and extra predictions;
- anisotropic and rotated/flipped affine with known physical volume;
- ROI whose pre-normalization containment is high but final Stage 2 visibility is lower;
- completed, warned, failed-positive, and failed-negative prediction set;
- known confusion matrices and score ties;
- known paired control/treatment differences and bootstrap seed;
- subgroup with pooled improvement but one required-group regression; and
- raw mask plus derived policy proving raw bytes/metrics remain addressable.

## Metric-version invalidation

A new metric version is required when changing class mapping, reference target meaning, empty/failure
handling, component connectivity/matching, probability/volume processing, score construction,
aggregation/resampling, or required subgroup behavior. Corrected versions preserve old results and
state whether conclusions change.
