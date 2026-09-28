# Annotation contract v2: original encoding and provenance

September 28, 2026. Schema and explicit validator implemented and tested. Not activated
in manifest publication or training; no real annotation was promoted in this step.

## Decision

Add `docs/capstone/contracts/annotation-record-v2.schema.json` with schema_version 2.0.0.
This is a major version because replacing source_values with measured encoding is a
breaking shape/meaning change. Keep v1 intact rather than widening an integer array and
silently changing how existing consumers interpret it.

The v2 original-source representation supports separate pancreas/lesion binary files,
including negative stored ranges, fractional semantic values and empty masks. It does
not yet define a derived-label artifact or a general multi-class mapping. Derived files
must not masquerade as original sources, and `method=derived` is intentionally absent.

## What is recorded

| Concern | Representation |
|---|---|
| Original source identity | Existing file reference and content SHA-256 |
| Measured audit | Separate audit file reference plus audited source hash |
| Observed values | Explicit stored or NIfTI-scaled basis, complete unique sorted value/count rows and total voxels |
| Stored representation | Minimum/maximum only; no invented complete raw value set |
| Scaling | Effective slope/intercept, not unresolved NIfTI sentinel values |
| Intended decoding | Null, proposed, or approved binary endpoint policy, hash, tolerance and canonical foreground |
| Mapping authorization | Referenced decision required for approved mapping |
| Annotation origin | Method plus unknown/publisher-protocol/per-file provenance scope and exact evidence references |
| Release applicability | Unresolved or confirmed, separate from general publisher claims |
| Allowed uses | Separate decision reference; no automatic training or evaluation permission |

Canonical background for the supported mapping is zero; foreground is explicitly one or
two. A mapping declaration does not materialize a normalized file or activate a decoder.
The existing candidate decoder remains unchanged and unactivated.

## Validator behavior and limits

`src/data/annotation_contract_v2.py::validate_annotation_v2` loads v1 definitions through
an explicit local referencing registry (no network lookup), then checks v2 shape plus
cross-field consistency. It rejects nonfinite JSON, unsafe reference paths, namespace/
snapshot mismatches, mismatched source hashes, duplicate/unsorted values, incomplete
counts, reversed ranges and scaling endpoint disagreement. Range comparison tolerance
is 1e-12 absolute/relative solely for numeric consistency, NOT label decoding or geometry.

An approved binary mapping must cover every observed semantic value under its recorded
absolute tolerance; relative tolerance is zero. A proposed mapping cannot claim approval
evidence. Quarantined/excluded annotations require issues and empty allowed uses. Claimed
methods/review statuses need applicable provenance; project_verified requires per-file
scope. Eligible records additionally require an approved mapping, nonempty allowed uses,
and a use-decision reference. Unknown/unverified/rejected origin cannot silently qualify.

JSON Schema alone checks shape, not every semantic rule; use the explicit validator.
The validator verifies references structurally but does NOT load the evidence or prove
that an approval is authentic, that its permissions match the record, or that G1 is met.
The later publisher must verify evidence hashes/contents, exact source/release/purpose
applicability, issue disposition, geometry, rights and protected membership. Validation
success alone must never authorize training. Those gates remain open.

## Compatibility and Claude boundary

No existing schema or assembler was edited. New v2 records are rejected by the v1 validator,
and v1 records are rejected by the explicit v2 validator. This prevents accidental mixing.
Claude's Plan 07 files and existing shared-contract assumptions remain untouched.

Unchanged current hashes:

- annotation v1: de2465e1d42492c29b797e9d3b76fcc4b7296b7871914f214d33a245d457c591
- manifest v1: c0fa91ca4aa3d0c69c597465b726190c476970ba22088e3c9ba9bde71df175dd
- manifest assembler: 090dabfc1fd7ea5879bed4d8fcc77e4b465bef210ee0652d2a6fb18daf10d5e7

## Tests and next step

27 new synthetic tests verify the measured scaled endpoints, empty/binary masks, identity,
count/range/scaling failures, mapping/provenance/allowed-use guards and version separation.
Full native suite: **532 passed**, two existing upstream torch.jit warnings. No scans or
external data accessed, dependencies changed, records rewritten, or experiments launched.

Next: implement explicit v2-aware manifest publication alongside the preserved v1 path,
with matching control-record version and annotation collection version. Convert linked
diagnostic evidence to NEW quarantined v2 records with unresolved provenance/mapping
left honest. Verify cross-record/source/issue references and reproducible package identity.
Do not insert v2 annotations into a control record declaring annotation version 1.0.0.
Source/provenance decisions and frozen training cohorts remain separate later gates.
