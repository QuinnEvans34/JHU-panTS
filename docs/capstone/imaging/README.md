# PROWL autonomous imaging

**Status:** Approved Plan 05 design package; implementation dependencies remain  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/05-autonomous-imaging.md`](../implementation/05-autonomous-imaging.md)

This directory defines the image-only localize-then-segment workflow before implementation. The
documents distinguish reusable engineering experience from capstone model artifacts and keep
ground-truth reference information outside autonomous inference.

## Documents

| Document | Purpose | Status |
|---|---|---|
| [`AUTONOMOUS-IO.md`](AUTONOMOUS-IO.md) | Image-only input, localization, cascade-bundle, prediction, probability, and prediction-set boundaries | Proposed for Plan 05 approval |
| [`LOCALIZATION-AND-ROI.md`](LOCALIZATION-AND-ROI.md) | Pancreas-only localizer, ROI candidate selection, containment, crop cost, normalization, and freeze procedure | Proposed for Plan 05 approval |
| [`SPATIAL-TRANSFORMS.md`](SPATIAL-TRANSFORMS.md) | Source/world/canonical/localizer/segmenter spaces, inverse restoration, interpolation, and geometry tests | Proposed for Plan 05 approval |
| [`MODEL-LINEAGE-AND-TRAINING.md`](MODEL-LINEAGE-AND-TRAINING.md) | New-model boundary, pretraining allowlist, baseline data, training ROIs, checkpoint selection, and bundle identity | Proposed for Plan 05 approval |
| [`FAILURE-AND-ABSTENTION.md`](FAILURE-AND-ABSTENTION.md) | Input, localization, inference, restoration, publication, and resource failure behavior | Proposed for Plan 05 approval |

## Non-negotiable rules

1. Autonomous inference receives a CT and permitted non-label metadata; it does not receive or
   discover annotations, provided regions, report findings, or evaluation labels.
2. Both capstone model checkpoints are newly trained. Prior-project checkpoints are evidence only.
3. The localizer target is pancreas only. Lesion labels do not construct its target or its ROI.
4. Stage 2 autonomous inference uses the predicted ROI exactly as frozen; reference data cannot repair
   it.
5. ROI mapping preserves the selected region and records scale/padding. Center-crop overflow and
   independent per-axis stretching are not the baseline.
6. Source affine/world geometry is authoritative. Published masks align to the source CT.
7. Every requested study produces one terminal prediction record, including failures.
8. Raw probabilities/masks remain immutable; post-processing and measurements are derived versions.
9. Autonomous and provided-region predictions are separate modes and identities.
10. The publisher-test role does not select thresholds, margins, tensor size, checkpoints, or model
    experiments.

## Planned machine-readable contracts

- image-only inference-study schema;
- localization-prediction schema;
- spatial-transform schema;
- ROI-policy schema;
- localizer and segmenter model-manifest schemas;
- cascade-bundle schema;
- prediction and prediction-set schemas;
- component-measurement schema; and
- compatible case-package revision exposing the cascade lineage.

These are documentation contracts until Plan 05 becomes Ready and implementation begins. Plan 09
owns committed golden fixtures and executable schema tests.

## Evidence boundary

Reference annotations may be joined only after autonomous prediction publication. Evaluation may
measure pancreas/lesion containment and Dice, but those values never flow back into the prediction
record. A demonstration package may expose a separately labeled reference block with reveal controls;
it cannot make the autonomous prediction retroactively reference-assisted.

## Next review

Quinton approved P05-01 through P05-13 on 2026-09-09, locking the dedicated pancreas-only cascade as
the baseline answer to D-204. Numerical operating settings remain development-measured, versioned
values. Implementation and training still wait for the Plan 06 handoff and Plan 10 boundaries.
