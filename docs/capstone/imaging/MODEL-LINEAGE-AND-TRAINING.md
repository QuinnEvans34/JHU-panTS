# Autonomous model lineage and training boundary

**Status:** Approved Plan 05 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P05-01 through P05-04, P05-09, P05-10, and P05-13  
**Governing plan:** [`../implementation/05-autonomous-imaging.md`](../implementation/05-autonomous-imaging.md)

## Purpose

The capstone may reuse code structure, experiment lessons, and permitted third-party pretraining. It
may not reuse a model trained during the preceding project. This contract makes that distinction
machine-auditable and separates the two capstone model roles.

## Model roles

| Role | Proposed baseline | Target/output | Training field of view | Inference field of view |
|---|---|---|---|---|
| Localizer | Dedicated compact SegResNet-family model | Background/pancreas only | Full-volume patches from registered PanTS train-role studies | Entire canonical CT through sliding windows |
| Segmenter | SegResNet-family three-class model | Background/pancreas/suspected lesion | Pancreas-only training ROI plus frozen jitter | Frozen predicted ROI through Stage 2 normalization |

The architectures share a family for engineering simplicity; their task heads, model records,
checkpoints, selection metrics and purposes remain separate.

## What “new model” means

Each capstone model must have:

- a capstone-created run ID after the approved project start;
- a registered train-role cohort and membership hash;
- a capstone resolved configuration and code/environment identity;
- an explicit initialization record;
- capstone training events/checkpoints;
- a named checkpoint-selection metric and immutable selected checkpoint; and
- a model-version ID derived from the selected weights and complete lineage.

A new filename or copied checkpoint does not make a model new. An old course checkpoint used for
warm start, teacher weights, pseudo-label generation, feature extraction, or model averaging is still
model reuse and is prohibited unless the approved scope is formally changed.

## Initialization classes

| Class | Baseline use | Required evidence |
|---|---|---|
| Fresh random initialization | Permitted fallback/control | Seed, initialization method, architecture and environment |
| Licensed third-party general abdominal CT pretraining | Permitted candidate | Source/version/citation/license, original URL/repository, checksum, architecture mapping and load audit |
| Prior-project trained checkpoint | Prohibited | Hash inventory/denylist proves it was not selected |
| Third-party task checkpoint trained directly on protected PanTS evaluation members | Prohibited unless a later contamination review proves separation | Training-data provenance and overlap review |
| Unknown or unverifiable checkpoint | Prohibited | None; train scratch instead |

SuPreM is the proposed third-party initialization candidate because the project already understands
its architecture relationship and the approved appendix names it as prior experience. It must still
be repinned and audited for the capstone. Its use is initialization, not a claim that the final model
is third-party or reused from the earlier course run.

## Checkpoint load audit

Before training, record:

- file hash and byte count;
- source/citation/license and retrieval record;
- expected architecture signature;
- source and destination tensor names/shapes;
- loaded, missing, unexpected and shape-mismatched tensors;
- the allowlisted task-head replacement;
- initialized values/seed for the new head; and
- a binary pass/fail decision.

Unexpected missing/mismatched backbone tensors fail the load. Printing a warning and continuing is
not sufficient. If the architecture changes too far for a defensible mapping, use scratch or a newly
reviewed source.

## Prior-project model inventory

Before any capstone training run, create a hash inventory of known historical checkpoints and model
exports. Training and registration compare the initialization and teacher/input model hashes against
that inventory. Paths and names are supporting evidence only; the hash check is authoritative.

Historical models remain available for:

- reading their configurations and failure analysis;
- reproducing a historical presentation if clearly labeled;
- regression fixtures that do not produce a capstone result; and
- comparison narrative using already recorded metrics.

They cannot enter capstone model computation.

## Baseline cohort boundary

### Localizer

- Registered PanTS train-role studies with a validated resolved pancreas annotation permitted for
  training.
- Studies with absent/unknown/invalid pancreas targets are ineligible rather than background.
- Training samples may include pancreas-positive and background regions within each eligible CT.
- Validation uses a frozen train-disjoint localization-development cohort.

### Segmenter

- Registered PanTS train-role studies with the target-aware label evidence required by the loss.
- Lesion-positive and verified lesion-negative membership/sampling are explicit; unknown is not
  negative.
- Exact case/patch sampling belongs to the resolved baseline configuration rather than a legacy text
  split.
- Validation uses frozen train-disjoint development cohorts with positive and negative cases needed
  by Plan 06.

PANORAMA is not part of the PanTS baseline by implication. After G2 it becomes eligible under exact
annotation uses and can be selected as a controlled Plan 06 data intervention. The expert-manual
lesion arm and optional automatic arm never merge silently.

## Localizer training contract

- Binary pancreas target is built independently from lesion data.
- Full-volume inference behavior is represented during validation; patch Dice alone cannot select the
  final model.
- Checkpoint selection emphasizes development containment/failure behavior under the frozen
  localization evaluation, not lesion Dice.
- The selected model is frozen before final ROI-policy selection and Stage 2 baseline generation.
- Any later retrained localizer creates a new model and cascade bundle.

## Segmenter training contract

- Three-class target uses the approved source remap and lesion-over-pancreas precedence.
- ROI source is the pancreas-only training annotation, never the union of pancreas and lesion.
- The same aspect-preserving normalization is shared with inference.
- Translation/scale/per-face jitter is bounded, versioned and frozen from localization-development
  evidence before baseline training.
- If a jittered ROI excludes lesion voxels, the event is recorded. The code cannot inspect lesion
  extent and secretly expand the ROI.
- Checkpoint selection uses a declared Plan 06-compatible validation metric and fixed cohort.
- Provided-region and autonomous evaluation use the same selected segmenter; only ROI source changes,
  under different prediction identities.

## Cascade bundle identity

The selected localizer and segmenter remain independently registered. The deployment/evaluation unit
is an immutable cascade bundle derived from:

- both model-version IDs and checkpoint content hashes;
- full-volume preprocessing and localizer sliding-window recipe;
- localizer decision/component/margin/plausibility policy;
- Stage 2 normalization/tensor/interpolation recipe;
- source-space restoration and base discretization;
- post-processing boundary/version reference; and
- code/environment component versions.

The bundle is not a new combined weight file. It is a manifest that makes the pair and their
interaction reproducible.

## Checkpoint selection and training chronology

1. Validate cohorts, environment, initialization and cache identity.
2. Run overfit/smoke gates on train-role fixtures.
3. Preregister maximum steps/time/cost, validation cadence, selection metric and tie-break.
4. Train without consulting publisher-test evidence.
5. Preserve periodic/latest recovery checkpoints separately from selected keeper checkpoints.
6. Select one checkpoint using the frozen rule; never reset the best metric on resume.
7. Register model identity and lock the selected bytes.
8. Run development baseline only after the cascade bundle is frozen.

`best` and `last` may be display labels but are never sufficient model identity. Model records state
the selection metric and value so a localizer cannot accidentally be chosen by lesion Dice or
training-patch mean.

## Required tests

- historical checkpoint denylist positive/negative cases;
- initialization source absent, hash mismatch, unexpected tensor and allowed-head mismatch cases;
- lesion-label change leaves localizer target identical;
- unknown lesion status never becomes segmenter negative;
- training cohort rejects evaluation-role ancestry and legacy list paths;
- training ROI bounds remain identical when lesion mask changes;
- shared train/inference Stage 2 normalization parity;
- resume retains selection history and cannot overwrite a keeper;
- model registration rejects missing cohort/config/code/environment evidence;
- cascade bundle changes when either model or any relevant inference policy changes; and
- publisher-test identifier cannot enter training, checkpoint selection or ROI-policy selection.

## Evidence package

- historical checkpoint hash inventory;
- third-party initialization manifest and load report;
- localizer and segmenter training preregistrations;
- resolved configs and cohort identities;
- run manifests, logs, checkpoint ledger and recovery evidence;
- selected checkpoint/model manifests;
- cascade-bundle manifest; and
- statement separating prior provided-region results from new capstone model results.
