# Five-study annotation v2 diagnostic manifest

September 28, 2026. Complete diagnostic publication; not source qualification or training.

## Result

New ignored package:
`outputs/prowl/manifest-v2-slice-685cfdbd-ae54-4508-be6f-5b9267197bd9/`

Manifest identity:
`manifest:pants-diagnostic-v2:bd69372c88eceb531a1f6ed65605d1e3412baa077ef686f9152671a73a828d7b`

- 5 subjects and 5 studies: PanTS 3, 26, 31, 78, 266; exact approved train membership checked.
- 10 original-source annotation records, v2: pancreas and pancreatic lesion for each study.
- 15 source-file references: five CTs and ten masks, from historical hash-verified audits.
- 20 blocking issues: five subject-identity holds, five study-qualification holds and ten
  annotation-use holds. These are unresolved decisions, NOT twenty corrupt files.
- All subjects/studies/annotations remain quarantined; zero eligible studies, no allowed uses.
- Snapshot is partial and no production root alias is activated.

## New implementation

`manifest-v2.schema.json` explicitly declares manifest version 2.0.0 and annotation collection
version 2.0.0; subject/study/issue collections remain version 1.0.0.
`src/data/manifest_records_v2.py` is an isolated assembler based on the v1 implementation,
with explicit annotation-v2 validation, versioned derivation identity and stronger issue/entity
links. It does not monkeypatch or mutate v1 behavior. This temporarily duplicates assembly
logic to preserve the existing interface during Claude's independent work; a future shared
internal engine requires parity tests and coordination, not silent divergence.

`src/data/annotation_v2_records.py` converts content-addressed linked evidence only to
quarantined original-source annotations. It preserves actual value counts/scaling and never
asserts a mapping, annotation method or provenance applicability that has not been resolved.
It verifies the linked record identity and exact audit reference before conversion.

`scripts/diagnostics/build_manifest_v2_slice.py` is a fixed local saved-evidence publisher,
not a general cohort/production publisher. It checks the prior pinned receipt and input
hashes, the exact five training IDs, ten distinct annotations, and audit/source equality.
No metadata spreadsheets, scans, external drives or network services are read.

## Package and verification

25 files have hashes in verification.json. Assembly inputs are persisted; rebuilding from
the persisted bytes reproduced every manifest collection and control record exactly.
All package hashes, referenced annotation audit files (size and SHA-256), and original
input hashes were independently rechecked after publication. The completion marker is
written last; a failed write would leave an incomplete directory, not a completed package.
This is exclusive new-directory diagnostic publication, not a crash-durable production writer.

The manifest_evidence alias refers to the package directory and its retained pair reports.
followup_source remains an unactivated historical diagnostic source alias. root-bindings.json
describes this scope; it is NOT a runtime root registry. Consumers must not train from it.
Linked case-78 coverage references remain in linked-assessments.jsonl with their hashes;
they do not become an approved anatomy-absent target or a clinical negative label.

The build diff_sha256 field records a scoped code/schema fingerprint, as in prior diagnostic
packages, not literal Git patch bytes. code-identity.json preserves its inputs. Issues/run
IDs are generated once and persisted: replay is identical from persisted inputs; rerunning
the publisher creates new issue IDs and a new diagnostic artifact, not a duplicate identity.

## Tests and compatibility

13 new synthetic tests: version separation, immutable input handling, exact repeatability,
collection hashes, annotation conversion, wrong/missing cross-record links, duplicate records,
publisher-test disguise rejection, evidence-sensitive identity and timestamp independence.
Full native suite: **545 passed**, two existing upstream torch.jit warnings. Workspace and
diff checks passed; the output package is ignored by Git.

V1 schema, assembler, old packages, original files, split membership and Claude's reserved
Plan 07 files remain unchanged. No model run, decoder activation, full dataset scan, commit
or push occurred.

## Next decision work

The representation gap is now solved for diagnostic original-source annotations. The next
blocker is evidence/authorization, not another serialization layer: reconcile release-specific
annotation provenance and source-use terms; review the proposed binary decoding policy;
then document purpose-specific coverage/geometry/identity dispositions before eligibility.
Case 266 units and case 78 coverage-purpose handling remain explicit. Source-level publisher
claims must not become per-file verification. Full G1 and frozen cohort publication remain
open; a five-study diagnostic is not an exception to those gates.
