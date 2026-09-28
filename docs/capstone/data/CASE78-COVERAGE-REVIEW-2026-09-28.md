# Case 78 coverage review

Date: September 28, 2026. Reviewer: Codex; research data-scope inspection, not a
radiologist's report, diagnosis, annotation correction or final eligibility adjudication.

## Finding

The inspected bone-window contact sheet shows pelvic/hip and proximal-thigh coverage,
including the most superior sampled axial plane. Its orthogonal views do not show upper
abdominal coverage. Together with the pinned metadata study type **ct hip right**, this
strongly supports an **out-of-pancreas-coverage** explanation for the empty pancreas mask.
It is not evidence that the CT is corrupt or that a missing pancreas contour needs drawing.

This is a selected-plane visual review: 10 axial, 5 coronal and 5 sagittal views span the
volume's indices. It is not a slice-by-slice expert read. A soft-window sheet was generated
but was not successfully displayed to the reviewer; the visual conclusion relies on the
bone-window sheet and corroborating source metadata. No disease assessment was made.

## Reproducible evidence

Ignored local folder:
`outputs/prowl/case78-coverage-c48e03d8-9d04-477e-8792-3a9c413128ed/`

- bone.png: inspected coverage sheet, scaled-value window [-400,1400].
- soft.png: generated alternative window [-160,240], not visually reviewed in this pass.
- evidence.json: original file hash/header, canonical affine/shape, orientation, all display
  indices/windows, image hashes and rendering code hash.
- Source: PanTSMini_ImageTr_00000001_00001000/PanTS_00000078/ct.nii.gz.
- SHA-256: d5f9849da0ac39919ce6ec0c199ea218deeb0b28b0dd981b01682322de90f57b.
- Shape 225 x 197 x 115, explicit 1.5 mm isotropic spacing.

The exact approved training membership and registered volume UUID/device were checked.
The CT hash matches the earlier audit and was remeasured after rendering. No source file
changed. Only this CT was read; no extra masks, other studies or held-out images were opened.

Rendering uses nibabel canonical RAS axis reorientation without resampling and float32
semantic CT values. Display uses nearest-neighbor resizing; labels specify orientation and
canonical indices. Full small volume was loaded (~20 MB float32 plus working copies), not
a general full-dataset memory policy. Outputs stay local/ignored, with no external upload.
Script: scripts/diagnostics/check_case78_coverage.py. Two synthetic orientation/window tests
added; full native suite **452 passed**, two upstream torch warnings.

## Recommended disposition, not activated

Do not use case 78 as a trusted pancreas-present localizer target. At the cohort-policy
review, classify it as an out-of-coverage candidate for exclusion from that purpose, while
preserving its base training membership and all original artifacts. A separate future
out-of-coverage robustness experiment would need explicit purpose/registration; this case
must not silently become a clinical negative or validation/test member.

No frozen cohort, annotation status or source record was edited. Later formal publication
should link this evidence to a reviewed issue/disposition. Unknown units in other cases and
the scaled-label encoding-contract question remain independent open items.
