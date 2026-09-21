# Identity and versioning contract

**Status:** Architecture baseline  
**Version:** 1.0.0  
**Approved:** 2026-09-08

## Why identity and integrity are separate

PROWL needs to answer two different questions:

1. **What logical thing is this?** A PanTS study, a PANORAMA subject, a cohort, or a model run.
2. **Are these exact bytes/configuration the expected version?** A SHA-256 content or derivation hash.

A human-readable ID answers the first question. A hash answers the second. We keep both; neither is
used as a substitute for the other.

## Source keys

Initial dataset keys:

- `pants`
- `panorama`
- `pubmed`
- `pmc`

Keys are lowercase ASCII slugs matching `^[a-z][a-z0-9_-]{1,31}$`. Adding a source requires a
version/license record; renaming a key is a breaking identity migration.

## Entity identifiers

| Field | Syntax | Example | Rule |
|---|---|---|---|
| `subject_id` | `<source>:subject:<source_subject_id>` | `panorama:subject:000123` | Identifies a person within a source; never infer across sources without evidence. |
| `study_id` | `<source>:study:<source_study_id>` | `pants:study:PanTS_00009005` | Identifies one imaging examination. |
| `annotation_id` | `<source>:annotation:<source_annotation_id>` | `panorama:annotation:000123_01-lesion-v1` | Identifies one source annotation/version. |
| `cohort_id` | `cohort:<slug>:v<integer>` | `cohort:capstone-train:v1` | Human-selected logical version; membership hash proves exact contents. |
| `run_id` | `run:<uuid4>` | `run:10d1c56e-9e36-4a1e-9ca4-c9a4f26b787e` | Unique execution; human name is separate. |
| `model_version_id` | `model:<slug>:<derivation-prefix>` | `model:prowl-baseline:4b9d8d8f34b1` | Immutable selected weights plus recipe lineage. |
| `prediction_id` | `prediction:<derivation-prefix>` | `prediction:0e98c21d12ca` | Deterministic from study, model, and inference recipe. |
| `evaluation_id` | `evaluation:<derivation-prefix>` | `evaluation:6ae20a9c5164` | Deterministic from prediction set, cohort, and metric spec. |
| `corpus_id` | `corpus:<slug>:<derivation-prefix>` | `corpus:pancreas-evidence:be13a098c127` | Corpus contents plus normalization/chunking. |
| `index_id` | `index:<slug>:<derivation-prefix>` | `index:pancreas-evidence:6f1bb87b436a` | Corpus plus embedding/index recipe. |
| `case_package_id` | `case-package:<derivation-prefix>` | `case-package:19a6d149e71f` | Prediction plus optional reference/evidence presentation selection. |
| `review_event_id` | `review:<uuid4>` | `review:600d1f27-1f45-4ed0-bc11-03c543cf6e56` | Human event identity; never derived or reused. |

The displayed label may be friendly; contracts use the canonical ID. Source identifiers are
pseudonymous dataset IDs only. If a source ID contains disallowed path characters, preserve it in a
record field and generate a reversible safe token for the filesystem rather than silently changing
the canonical ID.

## Source snapshot identity

A source snapshot record contains:

- source key;
- release/version/commit where available;
- retrieval date;
- license/citation identifiers;
- deterministic sorted file inventory;
- published checksums or locally computed selected/full checksums;
- completeness/reconciliation status.

`source_snapshot_id` is `snapshot:<source>:<derivation-prefix>`, where the derivation includes the
canonical snapshot record and file inventory assurance level.

## Derivation key

A derivation key identifies what an output *should be* before the bytes are produced:

```text
SHA-256(canonical JSON {
  artifact_type,
  schema_version,
  ordered input artifact IDs and content hashes,
  relevant resolved configuration,
  code identity,
  algorithm/component version
})
```

Canonical JSON uses UTF-8, lexicographically sorted object keys, no insignificant whitespace, and
JSON-native numbers/booleans/null. Arrays remain ordered. Paths are normalized to artifact-relative
POSIX form before hashing.

The full 64-character hash is stored as `derivation_sha256`. A 12-character prefix may appear in a
human-readable ID/path, but comparisons always use the full hash.

## Content integrity

Every material file carries or appears in a manifest with:

- relative URI;
- byte count;
- media type;
- full SHA-256 hash;
- optional shape, dtype, affine/spacing, or row count relevant to the format.

`content_sha256` proves the output bytes. It is not the derivation key. Two implementations may
produce scientifically equivalent but byte-different outputs; that case needs an explicit
equivalence policy, never silent hash substitution.

## Schema versions

Use semantic versions:

- Major: incompatible field meaning/removal or consumer break.
- Minor: backward-compatible optional fields/capabilities.
- Patch: clarification or validation tightening that does not change valid meaning.

Stored artifacts never have their schema version edited in place. An adapter emits a new artifact.

## Code identity

Every run records:

- Git commit when available;
- whether the working tree was dirty;
- a hash of the relevant diff or source bundle when dirty;
- entry point and component version;
- environment/dependency identity.

A dirty run may be exploratory. It cannot masquerade as a clean reproducible release run.

## Configuration identity

Store the complete resolved configuration used by the component. The derivation hash includes only
the declared relevant subset, but the run manifest preserves the full resolved configuration and a
record of the selected subset. This keeps irrelevant display settings from invalidating a model while
preventing hidden preprocessing parameters from escaping the hash.

## Review revisions

Review events use unique event IDs and an integer `revision`. Revision 1 has no predecessor. A later
event includes `supersedes_review_event_id` and increments the revision for the same
`case_package_id` and `prediction_id`. Previous events remain unchanged.

## Invalidation rules

- Identity/source/label change invalidates manifests, affected cohorts, and descendants.
- Cohort membership change invalidates models trained from it, not unrelated source artifacts.
- Preprocessing change invalidates caches and downstream models/predictions.
- Inference/post-processing change invalidates prediction/measurement artifacts but may reuse model
  weights.
- Metric change invalidates evaluations but may reuse complete predictions.
- Corpus/chunk change invalidates indexes; embedding/index change does not invalidate the corpus.
- UI-only rendering change does not invalidate scientific predictions.
- Review events never invalidate upstream artifacts.

## Prohibited identity shortcuts

- Absolute local paths as identifiers.
- Filename alone as proof of contents.
- Current date/time as a scientific version.
- `latest`, `best`, or `final` as the only model/artifact identity.
- Assuming equal IDs across sources refer to the same person or study.
- Overwriting an artifact because a logical name is reused.
