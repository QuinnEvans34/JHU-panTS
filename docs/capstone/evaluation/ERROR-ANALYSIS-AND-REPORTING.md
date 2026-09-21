# Error analysis and reporting

**Status:** Approved Plan 06 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P06-09 through P06-11 and P06-15  
**Governing plan:** [`../implementation/06-evaluation-and-model-experimentation.md`](../implementation/06-evaluation-and-model-experimentation.md)

## Purpose

The autonomous baseline must do more than produce a score. This design decomposes where the system
fails, identifies which errors matter to the review workflow, and creates a defensible ranked input to
D-205. It also defines the machine-readable and human-readable reports so results do not diverge.

## Required analysis layers

### 1. Population and completeness

- requested and metric-eligible subjects/studies;
- target-positive, target-negative, and unknown counts by reference definition;
- completed, warned, failed, and unevaluable counts;
- source and annotation-provenance/quality counts;
- repeated-study/identity-assurance counts; and
- all exclusions with stable reason codes.

This layer appears before performance so a good mean cannot hide a narrow denominator.

### 2. Localization and ROI

- empty, ambiguous, implausible, boundary-contact, and low-effective-resolution cases;
- pancreas and lesion effective containment after final Stage 2 mapping;
- ROI volume/source-volume fraction and crop inflation;
- source geometry, spacing, orientation, and transform warnings; and
- autonomous versus pancreas-only provided-region difference.

Primary question: did Stage 2 receive a usable view of the target?

### 3. Segmentation morphology

For positive references classify errors without changing the prediction:

- complete miss;
- partial/under-outline;
- over-outline;
- boundary displacement;
- merge of multiple lesions;
- fragmentation/duplicate components;
- prediction outside pancreas context;
- pancreas/lesion class confusion; and
- plausible annotation disagreement or invalid reference.

Categories may co-occur. Automated flags nominate cases; final narrative classifications record their
rule and any manual adjudication.

### 4. Detection and false alarms

- false-negative positives by score, predicted volume, lesion size/count, phase, source, and ROI state;
- false-positive negatives by peak score, component count/volume, anatomical location, and phase;
- movement across probability/volume/anatomical/denoising policies; and
- sensitivity/specificity, false-positive components/scan, and coverage tradeoffs.

Primary question: can an operating-policy change improve reviewer burden without hiding misses, or is
new model/data evidence required?

### 5. Source and subgroup behavior

Required groups when populated:

- PanTS versus any eligible PANORAMA diagnostic/training influence;
- manual versus machine annotation and quality stratum;
- contrast phase;
- lesion volume/count bands fixed before outcome comparison;
- scanner/manufacturer/acquisition fields;
- geometry/effective-resolution bands; and
- warning/failure categories.

Show `n` and uncertainty. Unknown stays a visible group. A pooled gain with a material group regression
must be surfaced in model-selection guardrails.

### 6. Resource and workflow cost

- localizer, Stage 2, restoration, post-processing, and complete-study runtimes;
- memory/fallback and external-drive I/O behavior;
- prediction/probability storage;
- failure/retry frequency; and
- UI-relevant warnings or missing artifacts.

A small accuracy gain that makes the single-workstation workflow impractical is not automatically a
better capstone system.

## Deterministic review-case set

Create a registered development-only review set with fixed selection rules:

- lowest, median-nearest, and highest lesion Dice among valid positives;
- false negatives nearest/farthest from the selected operating boundary;
- highest-volume and highest-score false positives;
- localization empty/ambiguous/low-containment cases;
- largest autonomous versus provided-region disagreements;
- multiple-lesion merge/fragment examples;
- source/annotation/phase/size representatives; and
- at least one completed-with-warning case of each common code.

Break ties by study identity. Preserve the full selection table and reason. Images are for diagnosis
and communication; hand-picking attractive examples cannot define the set.

## Error-to-experiment decision matrix

For each major failure, record:

| Field | Meaning |
|---|---|
| Failure ID/category | Stable name tied to metric/per-case evidence |
| Frequency/severity | Count, rate, uncertainty, affected user task |
| Localization contribution | Whether the target was available to Stage 2 |
| Leading mechanism | Data, target, localization, resolution, model, loss, score/policy, source, compute |
| Alternative explanation | What else could produce the same pattern? |
| Cheapest discriminator | Diagnostic that separates mechanisms |
| Candidate intervention | Controlled change or coherent intervention block |
| Primary endpoint | Metric most directly altered by the mechanism |
| Guardrails | Critical performance/workflow qualities that must not regress |
| Feasibility | Code/data/compute/time and recovery margin |
| Decision value | What becomes known or unblocked |

Rank candidates using the Plan 06 criteria and retain rejected candidates/reasons. The highest score is
a recommendation to Quinton, not an automatic launch.

## Machine-readable outputs

### Per-study result

- subject/study/source and cohort/prediction/reference identities;
- terminal status/warnings/failure and metric eligibility;
- autonomous/provided-region and raw/derived policy identity;
- localization containment/ROI/effective-resolution measures;
- named pancreas/lesion metric values;
- case score, predicted component count/volumes, detection state;
- TP/FN/TN/FP contribution under each named reference/policy;
- subgroup/source/annotation fields;
- stage/runtime/storage values; and
- case-review selection reason if selected.

### Per-component result

- reference/predicted component IDs and parent study;
- voxel/physical volume, centroid/world bounds;
- overlap/Dice/coverage/IoU fields used by matching;
- matched/unmatched/duplicate/merged classification; and
- threshold/policy/matching-version identities.

### Aggregate result

- metric-spec, cohort, prediction set, reference, and run identities;
- eligible/excluded/failure counts;
- point estimates, intervals, resampling unit/seed/draws;
- curves and selected operating point;
- subgroup/source tables; and
- raw/derived/autonomous/provided-region comparison links.

Machine rows are immutable source for every report table and UI summary.

## Human-readable baseline report

Recommended order:

1. Question, system version, cohort, and non-diagnostic scope.
2. Population/completeness/failure accounting.
3. Autonomous headline metrics with uncertainty.
4. Localization and effective-containment evidence.
5. Autonomous versus provided-region decomposition.
6. Patient sensitivity/specificity curve and selected-development operating policy status.
7. Multi-lesion/tumor-wise results.
8. Source/subgroup distributions and limitations.
9. Deterministic case-review findings.
10. Runtime/storage/workflow evidence.
11. Ranked error mechanisms and D-205 experiment candidates.
12. Reproducibility identities and known limitations.

The Week 5 report may leave D-208 unselected while showing development curves. It cannot present a
temporary UI score as final.

## Controlled-comparison report

- preregistered question/mechanism/decision bar;
- control/treatment changed-factor audit;
- matched cohort and completeness evidence;
- primary paired effect and interval;
- critical guardrails;
- per-case win/loss/tie and distribution;
- required subgroups and resource differences;
- deviations/confounds;
- accepted/rejected/inconclusive/invalid/failed decision; and
- exact model/policy-selection consequence.

Write the decision from the frozen rule before writing an explanatory narrative.

## Final report behavior

- Distinguish development-validation from publisher-test everywhere.
- Distinguish the historical preceding-project provided-region result from all new capstone models.
- Present autonomous results first; provided-region is decomposition/reference.
- Use the same generated tables in paper/presentation where possible.
- State prior publisher-test exposure from the preceding project honestly.
- Report a poor final result and generalization gap without test-guided revision.
- State benchmark compatibility only for verified definitions.
- Keep all limitations, failure coverage, and subgroup counts visible.

## Required tests

- deterministic review-case selection and tie-breaking;
- aggregate tables reproduce exactly from per-study/component rows;
- a pooled improvement with planted subgroup harm remains visible;
- failures/exclusions reconcile to requested and eligible counts;
- autonomous/provided-region and raw/derived columns cannot merge;
- report tables reject ambiguous metric aliases;
- changed result version cannot silently update an existing report; and
- UI summary values match the selected machine-readable evaluation identity.
