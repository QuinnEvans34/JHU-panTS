# Spatial units investigation — September 28, 2026

Status: measured evidence and proposed reconciliation policy; no unit overrides enabled.

## Approval and implementation follow-up

Quinton explicitly approved the paired explicitly-mm CT inference policy in this task.
`infer_mask_mm` now returns a separate interpreted evidence record, retaining original
raw units, both measured SHA-256 values, study identity and policy version
`paired-explicit-mm-ct-v1`. It requires same-study pairing from a validated join,
matching shape/spacing/affine, a clean explicitly-mm CT, and consistent coded mask
transforms. It does not rewrite source files or automatically grant eligibility.
Previously published issue records must be preserved and linked to a later resolution
artifact by the manifest publisher; the inference function does not modify them.

Real-data validation: 00000001 pancreas now receives the inferred-mm interpretation
using the paired CT. 00000002 is refused because its CT also has unknown units.
The source hashes match those recorded in SOURCE-EVIDENCE-2026-09-28.md.
Seven new synthetic tests cover successful provenance/preservation and rejection of
unknown CT units, mismatched shape/affine/transforms, missing hash and different study.
**309 Python tests pass**, two upstream deprecation warnings.

The sections below preserve the investigation and original proposal chronology.

## Measurements

Training studies 00000001 and 00000002 were rechecked header-only. Within each study,
CT, pancreas and lesion shapes, numeric zooms and selected affine match.

- 00000001: shape 512×333×200; numeric zooms 0.625/0.625/0.800000011920929;
  qform and sform codes both 1. CT and lesion explicitly declare mm; pancreas does not.
- 00000002: shape 275×198×180; numeric zooms 1.5/1.5/1.5; qform code 0,
  sform code 2. None of the three files declares spatial units.
- The pinned acquisition metadata.xlsx lists spacing (0.625,0.625,0.8) and
  (1.5,1.5,1.5), respectively. Its column is named `spacing`, not `spacing_mm`.

Metadata was read through the XLSX XML archive using standard-library read-only
parsing because openpyxl is absent from the project environment. No dependency added.
This bounded inspection is not a general metadata adapter.

## Publisher documentation

Reviewed the publisher's [repository](https://github.com/MrGiovanni/PanTS) and
[data layout/class map](https://github.com/MrGiovanni/PanTS/blob/main/data/README.md).
These pages support source layout/structure interpretation but do not supply an
explicit rule for repairing unknown NIfTI units. Do not cite them as per-file proof
that an unknown header means millimetres. No publisher contact or external write occurred.

## Proposed policy, not activated

1. Explicit, valid header units remain authoritative after geometry checks.
2. Unknown-unit masks with matching shape, zooms and affine to the paired explicitly-mm
   CT may be candidates for a separately recorded inferred-mm interpretation. Require
   source identity, paired file hashes and transform-consistency checks. Never modify
   originals or describe the inferred unit as a publisher header declaration.
3. Where CT and masks all lack units, matching numerical metadata is useful corroboration
   but not sufficient unit evidence. Keep unresolved pending a documented source-level
   mm convention or other independent measurement. Do not infer from plausible numbers alone.
4. Mismatched grids/transforms or contradictory declared units remain blocking; do not
   fix them by copying the CT affine or silently resampling.

Study 00000001 fits the candidate pattern in item 2; study 00000002 stays unresolved
under item 3. Neither is newly declared eligible. This sample does not estimate how
common missing units are across PanTS.

## Code progress

The evidence adapter now retains raw native header values alongside interpreted geometry,
so unknown-unit measurements are not discarded. A schema-validated issue-record builder
creates append-only, hash-linked blocking findings without auto-resolving them. Issue IDs
are new per invocation; callers must persist/reuse existing issue artifacts rather than
regenerating issues when attempting a reproducible rebuild.

Next: agree the inference policy, qualify the metadata adapter, and produce a sampled
manifest with unresolved cases represented honestly. Frozen real cohorts remain gated.
