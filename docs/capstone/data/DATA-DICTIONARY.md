# Plan 02 data dictionary

**Status:** Approved for schema implementation  
**Version:** 1.0  
**Governing identity rules:** [`../contracts/identity-and-versioning.md`](../contracts/identity-and-versioning.md)

This dictionary specifies semantic meaning. The approved JSON schemas under `../contracts/` supply
exact types, patterns, and required-field validation.

## Shared conventions

- IDs are canonical, source-scoped strings; filesystem-safe tokens are presentation details.
- Times are UTC RFC 3339 values and never determine scientific identity.
- Hashes are lowercase, full 64-character SHA-256 values.
- Source files use `root_alias` plus relative POSIX URI. `..`, absolute, drive-letter, and `file:`
  paths are forbidden.
- Missing is `null` plus, where scientifically material, a missingness/status reason. Empty strings
  are not missing-value sentinels.
- Controlled vocabularies use lowercase snake case.

## Source snapshot

| Field | Required | Meaning |
|---|:---:|---|
| `schema_version` | Yes | Record contract version |
| `source_snapshot_id` | Yes | Immutable snapshot identity |
| `source_key` | Yes | `pants` or `panorama` for Plan 02 |
| `source_version` | Yes | Publisher release/archive/commit identifiers, explicitly unknown where absent |
| `retrieved_at` | Yes | When the local snapshot was acquired/verified |
| `license` | Yes | Name, URI/evidence, restrictions, and citation requirements |
| `root_alias` | Yes | Configured logical source root, never a host path |
| `inventory_uri` / `inventory_sha256` | Yes | Sorted source-file inventory and integrity |
| `inventory_assurance` | Yes | Publisher checksum, full local hash, selected local hash, or metadata-only |
| `status` | Yes | `complete`, `partial`, or `quarantined` |
| `derivation_sha256` | Yes | Full canonical snapshot derivation hash |

## Subject record

| Field | Required | Meaning |
|---|:---:|---|
| `subject_id` | Yes | `<source>:subject:<source_subject_id>` |
| `source_snapshot_id` / `source` | Yes | Source lineage |
| `source_subject_id` | Yes | Exact publisher identifier; not assumed equal across sources |
| `identity_method` | Yes | `source_subject_id` or `study_as_subject_fallback` |
| `identity_assurance` | Yes | `source_asserted`, `direct_metadata`, or `unverified_unique` |
| `status` | Yes | `reconciled`, `excluded`, or `quarantined` |
| `issue_ids` | Yes | Possibly empty list of related issues |

Age and sex are not identity keys. If retained for subgroup description, they remain optional source
metadata with missingness preserved.

## Study record

| Field | Required | Meaning |
|---|:---:|---|
| `study_id` | Yes | `<source>:study:<source_study_id>` |
| `subject_id` | Yes | One source-scoped grouping parent |
| `source_snapshot_id` / `source` | Yes | Source lineage |
| `source_study_id` | Yes | Exact publisher examination identifier |
| `source_partition` | Yes | Publisher location/category such as `train`, `test`, or `unspecified` |
| `modality` | Yes | `CT` for initial imaging sources |
| `image` | Yes | Root alias, relative URI, media type, bytes, and available hash assurance |
| `geometry` | Yes when reconciled | Shape, spacing in millimetres, affine/orientation evidence |
| `acquisition` | Yes | Nullable date/year, phase, scanner/manufacturer/site fields as available |
| `target_statuses` | Yes | One or more target-aware status records: target name, `positive`/`negative`/`unknown`, evidence method, and source reference |
| `status` | Yes | `discovered`, `reconciled`, `eligible`, `excluded`, or `quarantined` |
| `issue_ids` | Yes | Possibly empty list of exclusions/validation issues |

`source_partition` is never interpreted as a protected train/validation/test role. Target status is
also not transferable by name alone: PANORAMA `non-PDAC` supports `pdac=negative`, not automatically
`pancreatic_lesion=negative`. Each study has at most one status record for a given target; the
application-level validator rejects duplicate or contradictory target entries.

## Annotation record

| Field | Required | Meaning |
|---|:---:|---|
| `annotation_id` | Yes | Immutable logical structure/version identity |
| `study_id` | Yes | Annotated study |
| `structure` | Yes | Canonical semantic structure, initially `pancreas` or `lesion` |
| `source_structure` | Yes | Source name/value before remapping |
| `file` | Yes | Root alias, URI, integrity, and geometry reference |
| `annotation_version` | Yes | Source label release/commit or derived version |
| `method` | Yes | `human_manual`, `human_validated`, `machine_generated`, `derived`, or `unknown` |
| `validation_status` | Yes | `source_asserted`, `project_verified`, `unverified`, or `rejected` |
| `allowed_uses` | Yes | Explicit set from `training_target`, `crop_reference`, `evaluation_reference`, `display_reference` |
| `label_encoding` | Yes | Source voxel value(s), canonical target, and mapping version |
| `status` / `issue_ids` | Yes | Eligibility and linked validation issues |

Method and allowed use are structure-specific. A multi-label PANORAMA file therefore creates at
least separate pancreas and lesion annotation records.

## Data issue record

| Field | Required | Meaning |
|---|:---:|---|
| `issue_id` | Yes | Immutable issue identity |
| `rule_code` | Yes | Stable validation/exclusion rule |
| `entity_type` / `entity_id` | Yes | Affected snapshot, subject, study, annotation, or cohort |
| `severity` | Yes | `information`, `warning`, or `blocking` |
| `disposition` | Yes | `retain`, `exclude`, `quarantine`, or `resolved_by_new_artifact` |
| `message` | Yes | Human-readable explanation |
| `evidence` | Yes | Structured source fields/files/hashes supporting the decision |
| `created_at` | Yes | Audit time, not scientific identity |
| `supersedes_issue_id` | No | Links a later adjudication without modifying the earlier issue |

## Manifest control record

| Field | Required | Meaning |
|---|:---:|---|
| `manifest_id` / `derivation_sha256` | Yes | Immutable manifest identity |
| `source_snapshot_ids` | Yes | Ordered immutable inputs |
| `record_schema_versions` | Yes | Subject/study/annotation/issue contract versions |
| `records` | Yes | URI, count, bytes, and content hash for each JSONL collection |
| `build` | Yes | Run/config/code identity and adapter versions |
| `reconciliation` | Yes | Counts by state plus named unresolved discrepancies |
| `status` | Yes | `complete` or `quarantined` |

## Cohort control record

| Field | Required | Meaning |
|---|:---:|---|
| `cohort_id` / `derivation_sha256` | Yes | Logical version and full derivation identity |
| `cohort_family_id` | Yes | Split/protection namespace such as `capstone-pants-v1` |
| `purpose` | Yes | `source_pool`, `training`, `validation`, `testing`, `development`, `smoke`, or `analysis` |
| `protected_role` | Yes | `train`, `validation`, `test`, or `none` |
| `parent_cohort_ids` | Yes | Direct parent set; empty only for source pools |
| `ancestor_cohort_ids` | Yes | Complete ancestry used for guard checks |
| `manifest_ids` | Yes | Manifest inputs |
| `definition` | Yes | Filters, grouping, stratification, seed, targets, and shortage policy |
| `members_uri` / `membership_sha256` | Yes when frozen | Sorted canonical membership collection |
| `profile_uri` / `profile_sha256` | Yes when frozen | Counts/strata report |
| `study_count` / `subject_count` | Yes | Exact achieved counts |
| `state` | Yes | `draft`, `validated`, `frozen`, or `superseded` |
| `frozen_at` | Required when frozen | Publication time, not membership identity |

## Cohort member record

| Field | Required | Meaning |
|---|:---:|---|
| `cohort_id` | Yes | Owning cohort |
| `study_id` / `subject_id` / `source` | Yes | Membership and grouping identity |
| `protected_role` | Yes | Must equal the cohort role |
| `target` / `target_status` | Yes | Cohort-specific prediction target and `positive`/`negative`/`unknown` status |
| `annotation_ids` | Yes | Exact annotations allowed for the cohort purpose |
| `inclusion_reason` | Yes | Source pool, sampled stratum, fixed migration membership, or adjudication |
| `source_order_key` | Yes | Deterministic tie-breaking value; never filesystem enumeration order |

Membership identity is the sorted canonical member record collection. A separate CSV may be emitted
for human inspection but is never authoritative.
