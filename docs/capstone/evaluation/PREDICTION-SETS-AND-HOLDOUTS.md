# Prediction sets and holdout policy

**Status:** Approved Plan 06 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P06-03, P06-06, and P06-14  
**Governing plan:** [`../implementation/06-evaluation-and-model-experimentation.md`](../implementation/06-evaluation-and-model-experimentation.md)

## Purpose

This contract prevents convenient subsets, missing failures, and repeated publisher-test reads from
changing the scientific question. Cohorts define who should be processed; prediction sets prove what
happened to every requested study; evaluation sets identify the exact reference join and metric
version.

## Identity chain

```text
registered cohort
  -> inference request
  -> exactly one terminal prediction per member
  -> immutable prediction set
  -> role-valid reference join
  -> evaluation result
```

Every arrow carries the parent IDs and content hashes. Ordering is deterministic but scientific
membership depends on IDs/hashes, not row position.

## Cohort roles

| Role | Source ancestry | Allowed use | Test-blind expectation |
|---|---|---|---|
| `train` | Frozen train-role parent | Parameter fitting | Not a generalization estimate |
| `train_smoke` | Registered train descendant | Wiring/overfit/timing | May be inspected freely |
| `train_development` | Registered train descendant | Exploration and diagnostics | May guide development |
| `development_validation` | Accepted validation role | Baseline, checkpoint/policy selection, controlled comparison | Explicitly development after first use |
| `publisher_test` | Accepted publisher-test role | One final frozen-system estimate | No selection evidence may precede freeze |

PANORAMA remains a training source unless a new untouched subject-grouped evaluation partition is
explicitly frozen before use. PanTS `study_as_subject_fallback` is stated in all uncertainty reports.

## Subsets

A subset is a new cohort artifact, not a list passed to a script. It includes:

- parent cohort ID/hash/role;
- deterministic selection method and seed where applicable;
- target-evidence rule;
- exact ordered membership and hash;
- intended use/run class;
- creator/date/code/config identity; and
- proof that no protected role changed.

Positive/negative, small-lesion, phase, source, warning, or review-case subsets inherit their parent
role. “First 20,” file-order slicing, hand-picked IDs, and arbitrary `*.txt` inputs are not eligible
for capstone claims.

## Prediction-set contract

A prediction set records:

- prediction-set ID/version and immutable creation identity;
- requested cohort ID/hash and ordered study IDs;
- model or cascade-bundle ID;
- inference/preprocessing/raw-discretization identity;
- prediction mode (`autonomous` or `provided_region_reference`);
- one terminal prediction reference per requested study;
- completed, warning, failed, and terminal-code counts;
- duplicate/missing/unexpected-member validation;
- per-member prediction/hash/status lookup;
- start/end/runtime/resource/environment identity; and
- completion marker/hash.

The identity changes if cohort membership, model/bundle, mode, preprocessing, ROI policy,
discretization, code behavior, or terminal member result changes.

## Completeness rules

For requested members `R` and terminal members `T`:

- set equality `R == T` is required;
- every study occurs exactly once in the terminal index;
- a retry remains attempt evidence but cannot create two terminal entries for one prediction request;
- failed members remain in the index;
- an unevaluable reference does not delete the prediction;
- unexpected predictions fail publication; and
- aggregate metrics cannot publish until completeness passes.

Changing configuration to recover a failed case creates a new prediction identity/set. It does not
replace the original failure in place.

## Reference join

The evaluation join adds:

- exact annotation/reference IDs and content hashes;
- target-evidence definition (`mask_evidence`, `report_evidence`, or another named source);
- metric eligibility and exclusion reason per study;
- source/annotation/subgroup fields used for reporting; and
- metric-spec version.

Inference does not receive this structure. The join occurs after prediction-set publication and
cannot mutate a prediction status, ROI, mask, probability, or score.

## Development-validation use

Development validation may support:

- model checkpoint selection under a frozen rule;
- Plan 05 localization/ROI policy selection;
- G4 autonomous baseline and provided-region decomposition;
- D-205 experiment selection and controlled comparison;
- D-208 case-score/operating-policy selection; and
- error analysis/subgroup diagnostics.

Because it is intentionally reused, reports call it `development-validation`, not untouched test.
The registry records every evaluation read so the extent of adaptation is visible.

## Publisher-test freeze

Before any capstone publisher-test inference/evaluation, create a release-selection manifest that
freezes:

- selected localizer, segmenter, and cascade-bundle IDs/hashes;
- preprocessing, localization, ROI, spatial, and raw-discretization policies;
- raw/derived post-processing policy;
- case score and probability/volume/component thresholds;
- required metric version and uncertainty settings;
- publisher-test cohort ID/hash;
- exact environment/code revision;
- expected output/storage/resources;
- signed/dated rationale based only on development evidence; and
- an audit proving no publisher-test result appears in the selection evidence.

The publisher-test labels may exist locally for final evaluation, but selectors/training/inference
interfaces receive only the role and permitted image inputs until the post-prediction evaluation
join.

## One-way final evaluation

1. Validate the release-selection manifest.
2. Produce the complete image-only publisher-test prediction set.
3. Lock prediction-set bytes and completeness evidence.
4. Join protected references under the frozen metric version.
5. Publish per-study and aggregate results.
6. Report generalization gap and limitations.
7. Do not change the model/policy because of the result.

If the result is poor, it remains the estimate. Future work may propose a new experiment, but that
cohort is no longer test-blind for the changed design.

## Correctness reruns

A publisher-test rerun is permissible only when a documented defect or operational failure means the
frozen system was not executed as specified—for example corrupted output, interrupted inference,
wrong model hash, or incorrect metric implementation.

Required evidence:

- defect/incident record and affected scope;
- proof that the corrective change restores the frozen intended behavior rather than optimizing it;
- preserved original predictions/results;
- unchanged model and operating-policy identities unless those were the defect;
- full affected-set rerun, not selective failed cases chosen by result; and
- report amendment explaining whether conclusions changed.

A low score, unfavorable subgroup, or threshold hindsight is not a correctness defect.

## Prior exposure disclosure

The preceding project already evaluated historical provided-region models on accepted PanTS test
members. Those models/results remain historical, and no capstone model may inherit their weights.
The capstone registry discloses this human/project-level prior exposure. Test-blindness therefore
means the new selected capstone model/policy is not optimized from new publisher-test reads; it does
not falsely claim that Quinton has never seen any historical aggregate from those cases.

## Required tests

- parent-role inheritance for every subset type;
- arbitrary path, first-N, duplicate, missing, and unexpected-member rejection;
- subject-group disjointness and repeated-study clustering;
- one terminal status per requested study;
- failed member retained through evaluation join;
- reference join cannot mutate prediction files/records;
- publisher-test ID rejected by training/tuning/policy selection;
- freeze manifest changes if any model/policy/metric identity changes;
- final execution blocked without a test-blind audit;
- corrective rerun requires incident ID and preserves original evidence; and
- autonomous and provided-region prediction sets cannot share prediction-mode identity.
