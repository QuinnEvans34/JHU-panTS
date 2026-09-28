# PanTS annotation provenance and decoding review

Status: source evidence reviewed; candidate decoder tested, **not activated**.
No annotation eligibility, cohort changes, label rewrite, model run or clinical finding.

## Publisher evidence and limits

The pinned repository revision is 243bef3075d2ab556eae374846e3ddfbc9f4c309.
Its [data README](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/data/README.md)
identifies separate structure files and a class map (pancreas 17, pancreatic lesion 28).
These class IDs must not be confused with the foreground value in a separate binary mask.
The pinned README was fetched read-only; no publisher source files were copied into this repo.

The [versioned paper, section 3.3](https://arxiv.org/html/2507.01291v1#S3.SS3)
describes manual tumor annotation and review, versus AI-initialized, radiologist-verified
and corrected non-tumor structures. This supports a source-level distinction between
human_manual lesions and human_validated pancreas—not human_manual for every structure.
It is a publisher protocol statement, not a per-file audit of this acquisition. That paper
version also uses different split terminology from our pinned release; it does not override
the protected 7,200/1,800/901 memberships or the publisher 9,000/901 boundary.

Recommended future records, once release applicability is reconciled:

| Structure | Proposed source method | Assurance boundary |
|---|---|---|
| Pancreatic lesion | human_manual | source_asserted, not independently verified by PROWL |
| Pancreas | human_validated | AI-assisted origin retained in provenance; source_asserted |

Do not populate these as unconditional per-file facts yet. Link exact source/version and
artifact hashes in provenance; document exceptions/unknowns explicitly. Publisher-level
claims do not close empty-mask, scaling, geometry, duplicate, or clinical-label questions.
Allowed uses remain empty for unresolved annotations. No automatic evaluation-reference
permission follows from training-target suitability. License discrepancy is not resolved here.

## Candidate decoding contract

Module: src/data/binary_label_policy.py; tests: tests/test_binary_label_policy.py.
Policy ID: pants-semantic-binary-atol1e-6-candidate-v1.

- Input is a nonempty 3D numeric array AFTER NIfTI slope/intercept scaling, not stored bytes.
- Reject NaN/Inf and every voxel outside absolute distance 1e-6 of either 0 or 1.
- Relative tolerance is zero. Validate all voxels before output; no clipping, generic >0,
  pre-validation rounding, or silent coercion of intermediate values.
- Return a NEW uint8 0/1 array plus policy/tolerance/changed-voxel/count evidence.
- Do not infer diagnosis, original author, physical units, validity or allowed use.
- Empty foreground is representable but not automatically an eligible negative target.
- Caller must explicitly name the candidate policy. No dataset/trainer imports it.

The proposed tolerance covers the measured 5.91389835e-8 foreground excess in cases
26/31 while remaining far below an intermediate class/probability value. This is a
project policy proposal, not a publisher instruction or a universal precision guarantee.
Approval/review is needed before any production integration or canonical label publication.

26 synthetic tests pass: exact/scaled endpoints, boundary rejection, nonfinite/intermediate
values, raw stored -128/127 rejection, type/shape checks, input preservation and explicit
policy selection. Full native suite **450 passed**, two upstream torch warnings.
The decoder works on an already loaded array and allocates several arrays; it is not a
streaming loader or a resource-qualified full-volume training adapter.

### Existing-code clarification

src/data/transforms.py ComposeLabeld currently uses >0, not equality to 1. It would retain
the measured near-one foreground; we have not found an equality bug in that composer.
Its permissive positivity and missing-mask behavior still require capstone qualification.
This candidate is not installed as a drop-in change to the historical pipeline.

### Annotation schema issue still open

The current annotation contract only admits nonnegative integer source_values. Our measured
int8 stored values and fractional scaled semantic values cannot be honestly represented as
original source foreground 1. Do not hide that mismatch by writing source_values=[1] for
the original file. Before publication, review a compatible encoding/provenance extension
or an explicit derived-label artifact contract tying normalized labels to original hashes
and the decoding policy. No schema was changed in this pass.

## Case 78: stronger lead, not a concluded defect

Read-only recheck of pinned metadata row 79, after verifying approved training membership:

- ID: PanTS_00000078.
- study type: **ct hip right**.
- CT phase: Non-contrast.
- shape: 225 x 197 x 115; metadata spacing: 1.5 x 1.5 x 1.5.
- Metadata SHA-256: 4bcbf14a31b1ca9441af051a104702e7a832391f47d3af5f493048ec813283e3.

Prior audited pancreas, liver and lesion masks were empty on matching grids. The study-type
field makes limited anatomical coverage a plausible explanation. Metadata is not visual
proof, and emptiness alone cannot distinguish missing annotation from out-of-view anatomy.
No source report, new mask, or voxel payload was read during this metadata follow-up.

Next bounded investigation: use only the previously hashed CT for a local orthogonal
contact sheet with source orientation/shape and slice indices; preserve source hash and
display parameters. Inspect coverage, not disease. If coverage remains uncertain, keep
the annotation unresolved and seek qualified review—do not invent a pancreas contour.
No external upload, patient-identifying display, full dataset scan or publisher contact.

Potential later outcomes require explicit evidence:

1. Out-of-scope anatomy confirmed: exclude from the intended pancreas-present localizer
   cohort by documented purpose, while preserving its protected base membership.
2. Expected anatomy visible but annotation missing: retain annotation-quality issue and
   withhold target use pending correction/qualified review.
3. Uncertain: retain unresolved status; do not force a negative target or final exclusion.

## Next decisions

Review the candidate decoding tolerance and encoding-contract representation before activation.
Then perform the case-78 coverage check, reconcile release-specific provenance and publish NEW
annotation/manifest artifacts only when their evidence supports the claimed method and uses.
Case 266 (and earlier case 2) unknown physical units remain separate unresolved findings.
