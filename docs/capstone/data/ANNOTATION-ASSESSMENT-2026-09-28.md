# Annotation encoding evidence and purpose assessment

September 28, 2026. Implemented pure helpers; synthetic verification only.
No source reads/writes, artifact publication, cohort changes, decoder activation or training.

## Why this step

The original v1 annotation record requires nonnegative integer source values. Measured
PanTS stored -128/127 values with NIfTI scaling cannot honestly be described as original
source values [1]. Separately, an empty pancreas mask is not proof of a cancer-negative
study or of annotation corruption. Quinton agreed to preserve case 78 and consider verified
anatomy-absent cases for a later controlled robustness experiment.

## Implemented boundary

`src/data/annotation_assessment.py` provides two pure functions:

- `encoding_evidence`: preserves caller-supplied source/audit SHA-256, complete observed
  stored values, effective slope/intercept and corresponding scaled values. Rejects invalid
  or nonfinite values, duplicate values and zero effective slope. Does not round, map,
  decode, or identify the observations as canonical labels.
- `assess_purpose`: builds a content-addressed pancreas assessment from supplied evidence,
  pancreas foreground count, explicit coverage state and purpose. Every result preserves
  the source and protected membership, grants no allowed uses and says not_granted.

| Coverage / pancreas mask | Pancreas-present localizer | Anatomy-absent robustness |
|---|---|---|
| Present / foreground | Candidate | Out of purpose |
| Absent / empty | Out of purpose | Candidate |
| Present / empty | Unresolved | Unresolved |
| Absent / foreground | Unresolved conflict | Unresolved conflict |
| Uncertain / either | Unresolved | Unresolved |

These are candidate assessments, not eligible annotation records or frozen cohort members.
The candidate label decoder remains unactivated. Existing v1 schemas and manifest assembly
are unchanged, preserving compatibility and Claude's read-only shared-contract assumptions.

## Evidence limitations

These functions validate supplied values and references, not the existence or credibility
of the evidence. A syntactically valid hash is not proof that an audit or coverage review
occurred. An integration adapter must resolve/hash the referenced artifacts, verify that
source/study/structure identities match, verify audit completion and complete value counts,
and retain the exact signed-off coverage disposition. Never pass a truncated audit sample
as the complete observed value set. Do not infer coverage from the mask count or study title.

Foreground count is exclusively a pancreas-mask measurement. This API cannot classify
lesion presence, malignancy or clinical negatives. Physical units, grid agreement, source
provenance, licensing and independent allowed-use approval remain separate gates.
No real case assessment was published by this step; case 78's visual finding remains in
CASE78-COVERAGE-REVIEW-2026-09-28.md rather than being silently promoted to adjudication.

## Verification

28 new synthetic tests cover measured scaled endpoints (0 and 1.0000000591389835), invalid
encoding, the purpose matrix, evidence requirements, retained membership, no permissions,
and deterministic/purpose-sensitive identities. Native full suite: **480 passed**, two
existing upstream torch.jit warnings. No dependencies changed.

## Next step

Build/test the evidence-linking adapter against the existing bounded audit receipts, with
hash and identity verification, then write NEW diagnostic assessment artifacts. Keep
unresolved cases unresolved. Decide the production encoding-contract version/derived-label
publication route before inserting annotations into manifests; this sidecar does not solve
that migration or authorize canonical label publication. Protected cohort publication and
first-run readiness follow, not a training launch now.
