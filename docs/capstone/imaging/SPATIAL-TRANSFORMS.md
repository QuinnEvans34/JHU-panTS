# Autonomous spatial-transform contract

**Status:** Approved Plan 05 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P05-06 and P05-07  
**Governing plan:** [`../implementation/05-autonomous-imaging.md`](../implementation/05-autonomous-imaging.md)

## Purpose

A correct-looking mask can still be scientifically wrong if it is shifted, flipped, scaled, cropped,
or assigned the wrong affine. The autonomous cascade crosses more spatial representations than the
preceding provided-region path. This contract makes every transition explicit and independently
testable.

## Authoritative geometry

The source CT consists of array values, a shape/header, and an affine mapping voxel indices to
physical world coordinates. PROWL records which NIfTI affine was selected and its qform/sform codes.
The selected source affine and source grid are authoritative for final output.

Scientific identity includes the CT content hash and geometry record. Two arrays with identical
values but different valid affines are different imaging inputs.

## Named spaces

| Space | Meaning | Minimum recorded geometry |
|---|---|---|
| `source_voxel` | Original CT array index space | Shape, dtype, affine, qform/sform, orientation, units |
| `source_world` | RAS+ physical millimeter coordinates | Source voxel-to-world affine |
| `canonical_full` | Reoriented full CT before localizer spacing | Shape, affine, orientation transform |
| `localizer_grid` | Resampled full-volume model grid | Shape, affine, target/realized spacing, align convention |
| `roi_world` | Selected physical region after component policy and margin | Bounds, requested/realized margin, boundary contact |
| `segmenter_tensor` | Fixed Stage 2 input after crop, uniform scale and pad | Shape, affine/equivalent mapping, uniform scale, pad, effective spacing |
| `source_probability` | Continuous model output restored to original CT grid | Exact source shape/affine and interpolation provenance |
| `source_mask` | Discrete raw/derived masks on original CT grid | Exact source shape/affine, integer label contract |

Every box field names its coordinate space and endpoint convention. Unlabeled six-integer boxes are
not accepted.

## Forward chain

1. Validate the source image is 3D, finite, readable, and has a valid invertible affine and physical
   units.
2. Reorient to the configured canonical orientation while preserving the mapping to source world.
3. Resample the complete image to the localizer grid with the configured image interpolation and
   intensity transform.
4. Run full-volume localization and create the frozen-policy ROI in localizer/world coordinates.
5. Clip only to the available source/world field; record requested versus realized extent.
6. Extract the selected region from the canonical/localizer representation.
7. Apply one uniform aspect-preserving scale, then deterministic symmetric padding to Stage 2 shape.
8. Run the segmenter and preserve continuous class probabilities in `segmenter_tensor` space.

The forward record stores every operation in order. Library-owned transform metadata may accompany
it but cannot replace the portable PROWL record.

## Inverse chain

1. Remove exactly the recorded Stage 2 padding.
2. Invert the uniform scale to the exact pre-letterbox ROI sampling grid.
3. Place continuous probabilities into the full canonical/localizer field at the recorded ROI.
4. Map probabilities through inverse resampling and orientation to the exact source grid.
5. Validate finite values and probability behavior; apply the frozen source-grid decision rule.
6. Create integer raw masks with the exact source shape and source affine/header policy.
7. Calculate physical components and measurements from source-world geometry.

Outside-ROI probability behavior is explicit. The baseline uses background probability 1 and
pancreas/lesion probability 0 outside the Stage 2 region; it does not leave uninitialized values.

## Interpolation and decision order

| Data | Forward interpolation | Inverse interpolation | Rule |
|---|---|---|---|
| CT image | Linear/trilinear | Not normally inverted | Record intensity window/scale separately |
| Probability/logit field | N/A from model | Linear/trilinear | Restore continuously, then normalize/validate as configured |
| Discrete annotation fixture | Nearest | Nearest for fixture/reference mapping | Never create fractional class labels |
| Final raw mask | Created on source grid | N/A | Argmax/threshold only after probability restoration |

The implementation must define corner/center alignment, padding origin, and rounding. A one-voxel
offset is a test failure, not visual noise.

## Required transform-record fields

- transform ID, schema and component version;
- source study/CT hash and cascade-bundle ID;
- each named space's shape and affine/equivalent voxel-to-world mapping;
- source selected-affine provenance and qform/sform codes;
- ordered orientation and resampling operations;
- localizer spacing and full-volume coverage facts;
- selected component IDs, ROI bounds and endpoint convention;
- margin in millimeters plus realized per-face margin;
- crop slices/rounding in the parent grid;
- uniform Stage 2 scale factor, pre/post shapes and per-face padding;
- effective Stage 2 voxel spacing;
- forward/inverse interpolation and alignment settings;
- software/component versions; and
- validation status, landmark error, round-trip overlap and warnings.

## Physical measurements

- Voxel volume derives from the absolute determinant of the source affine's spatial 3×3 matrix rather
  than assuming a diagonal affine.
- Centroids and bounds are expressed in source voxel coordinates and RAS+ world millimeters.
- Distances use world coordinates; anisotropic voxel counts are not treated as millimeters.
- Any maximum-diameter approximation names its method and tolerance.
- Measurements are derived from source-space masks, not the normalized Stage 2 tensor.
- If shear/obliquity exceeds the supported measurement policy, the prediction may still be viewable
  but measurement publication warns or fails as frozen.

## Golden fixtures

1. Identity affine and no resampling.
2. Nonzero origin with odd crop dimensions.
3. Axis flip/reorder requiring canonical orientation.
4. Anisotropic voxel sizes.
5. Oblique or sheared valid affine within support policy.
6. ROI touching each low/high source face.
7. ROI larger than nominal field but preserved by letterbox.
8. Small ROI with asymmetric one-voxel padding.
9. Landmark points at corners, center, pancreas and lesion.
10. Binary sphere/cuboid with known world volume and diameter.
11. Two disconnected lesions.
12. Invalid singular/nonfinite affine.

## Required assertions

- Source and restored shape are identical.
- Source and restored affine/header policy match exactly or within a named serialization tolerance.
- Forward then inverse landmark error is within the frozen sub-voxel/world-millimeter tolerance.
- No selected ROI content is lost during normalization.
- Discrete labels remain in their allowed value set.
- Physical volume agrees with the analytic fixture tolerance.
- A source-space overlay passes manual visual review on representative real PanTS studies before
  baseline publication.
- Static case-package and FastAPI consumers receive identical geometry references.

## Failure behavior

- Missing/ambiguous physical units, singular affine, impossible shape, nonfinite values, or an
  unsupported dimensionality fails preflight.
- Failed inverse validation prevents publication of source-space masks.
- A transform mismatch cannot be repaired by copying the source affine onto an unrelated array.
- Correcting a transform creates new transform and prediction identities; old outputs remain
  quarantined/invalidated rather than overwritten.

## Implementation note

MONAI transform tracing is useful, but it is version-sensitive application state. PROWL serializes the
minimal operations above in plain records and validates with NiBabel/world-coordinate fixtures. This
allows a future transform implementation to change without changing the scientific meaning.
