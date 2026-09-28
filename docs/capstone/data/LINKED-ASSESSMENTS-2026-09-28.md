# Saved audit evidence linked to diagnostic assessments

September 28, 2026. Completed local evidence replay; **not eligibility or source promotion**.
Claude's Plan 07 lane remains independent and untouched.

## Result

New ignored package:
`outputs/prowl/annotation-assessments-6277e6f8-17e2-4f6f-b929-285c6e87af81/`

- Ten records: pancreas and pancreatic lesion for training cases 3, 26, 31, 78 and 266.
- Ten unresolved purpose assessments: two purposes for each of the five pancreas records.
- One linked provisional visual-review reference, for case 78, without automatic adjudication.
- All records retain empty allowed uses and eligibility not_granted.
- No complete stored-value inventory fabricated from minimum/maximum. Measured value counts
  retain their stored/scaled basis, exact scaling, original units and recorded unit interpretation.

`assessments.jsonl` SHA-256:
`5eecf72d45615e482ad59eb60a92011f977927bc7039e7f77160f59313026762`.
Completion receipt records 23 input hashes, including code, plus output identity. All input
hashes and output hash were independently rechecked after publication; Git ignores the package.

## Verified chain

The runner pins the prior follow-up receipt hash, then checks all 13 listed report/selection
artifacts, all 12 pairs and all 17 source-hash references. Five approved train identities are
checked against the hash-validated protected training list. Pair URIs, structures, source
hashes, repeated references, recorded grid compatibility, complete finite-voxel counts,
complete value counts, foreground summaries and inferred-unit identity links are checked.
The two supporting liver/lung reports are verified but do not become pancreas annotations.

Case 78's rendering evidence is pinned and matched to the paired CT URI/hash/byte count;
the bone contact-sheet hash is verified. The existing review document is hashed and linked,
not reparsed into an automatic clinical or anatomical verdict. Formal coverage remains
unresolved in machine-consumed assessments until an explicit reviewed disposition exists.
This preserves the earlier strong visual lead without claiming expert all-slice review.

## Important limitations

Hash linkage establishes consistency with the saved audit, not a new measurement of source
files or an independent validation of the original audit's correctness. No external-drive,
new scan, held-out image or network reads occurred. This adapter is scoped to the existing
voxel-audit-v1.1 format, not a general untrusted-input ingestion service.

The audit recorded complete semantic value counts but only a stored range, so the previous
encoding_evidence helper cannot be called with an invented complete stored-value list.
This package explicitly leaves complete_stored_value_set null. No inverse scaling or
canonical source value 1 was fabricated. Binary decoding remains unactivated.

The ten purpose assessments intentionally remain unresolved: foreground does not prove
anatomical coverage, and the provisional case-78 review is not a final eligibility decision.
Case 266's unknown units remain recorded. No schema migration, source license/provenance
qualification, cohort publication, target rewrite or experiment launch is implied.

## Implementation and tests

- `src/data/audit_assessment_link.py`: pure evidence verification and reference linking.
- `scripts/diagnostics/link_annotation_assessments.py`: fixed local replay, bounded input
  files, new UUID destination, exclusive output creation and completion receipt written last.
- `tests/test_audit_assessment_link.py`: 25 synthetic tests for integrity, altered/rehashed
  inconsistent evidence, cross-study/structure mistakes, value counts, coverage linkage,
  duplicate JSON keys, nonfinite JSON and non-promoting output behavior.

Native full suite: **505 passed**, two existing upstream torch.jit warnings. Workspace and
diff whitespace checks passed. No dependency changes, commits or edits to Claude's files.

## Next

Resolve production representation: versioned annotation encoding/provenance contract or
explicit derived-label artifact linking original hashes and the approved decoding policy.
The current integer-only v1 contract must not receive false source_values=[1]. Shared-contract
changes should be coordinated with Claude's active read-only contract assumptions. Then
resolve purpose-specific issue dispositions and integrate into NEW manifests; protected
cohort publication remains downstream of those checks.
