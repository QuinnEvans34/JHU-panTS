# UI data adapters and review persistence

**Status:** Approved Plan 08 design baseline; schema implementation gated  
**Decisions:** P08-02, P08-03, P08-08, and P08-13 through P08-16  
**Last reviewed:** 2026-09-09

## Boundary

React components consume one validated internal view model. Repositories/adapters own transport,
schema validation, capability discovery, reference resolution, and error normalization.

## Planned interfaces

```text
CaseRepository
  listCases() -> CaseListEntry[]
  getCasePackage(casePackageId) -> CasePackage
  resolveFile(casePackageId, fileReference) -> URL/handle

AnalysisRepository
  requestAnalysis(studyId, idempotencyKey) -> AnalysisTask
  getAnalysisTask(taskId) -> AnalysisTask

EvidenceRepository
  requestEvidence(structuredFinding, questionIntent) -> EvidenceResponse
  getEvidenceResponse(evidenceResponseId) -> EvidenceResponse

ReviewRepository
  listReviewEvents(casePackageId, predictionId) -> ReviewEvent[]
  appendReview(reviewDraft, expectedLatestRevision, idempotencyKey) -> ReviewWriteReceipt
  inspectAppend(idempotencyKey) -> ReviewWriteReceipt | not_found
```

These are conceptual contracts, not permission to implement them before Plans 09/10.

## Static package adapter

- Reads a versioned case-list manifest and immutable case-package JSON.
- Resolves only validated relative file references beneath the package base.
- Can read precomputed evidence responses and a content-hashed review-history snapshot.
- Cannot claim it appended to the authoritative event ledger.
- May download/export a schema-valid review event with `exported—not recorded` status.
- Must expose capability flags so the UI presents `Record review` versus `Export review record`
  honestly.

## FastAPI adapter

- Returns the same case package and evidence response values as their file forms.
- Exposes transient analysis task status separately from terminal packages.
- Sends review drafts to the local append-only writer.
- Returns a durable receipt only after validation, append, flush/fsync policy, and read-back pass.
- Uses exact target identities and idempotency keys.
- Does not turn URLs, database rows, or response timestamps into scientific identity.

Proposed route meaning—not final endpoint spelling:

| Operation | Behavior |
|---|---|
| List packages | Lightweight entries; no reference asset preloading |
| Get package | Exact schema payload, immutable cache policy |
| Resolve file | Safe package-relative content with expected hash/size |
| Start/inspect analysis | Separate task record until package publication |
| Request evidence | Approved structured finding/question contract |
| Get review history | Exact package/prediction chain and snapshot identity |
| Append review | Server assigns event identity/time/revision and returns receipt |

## Internal view model

The view model contains presentation-ready but scientifically unchanged fields:

- study display identity and source;
- package/prediction/model IDs and timestamps;
- prediction status/localization/warnings;
- resolved layer descriptors for CT, raw prediction, optional derived displays, and optional reference;
- measurements with explicit units/source/availability;
- optional frozen reviewer-ordering descriptor;
- evidence-response references/states;
- lineage details for an expandable panel;
- adapter capabilities and validation warnings.

It may format units or labels. It cannot calculate scientific measurements, choose thresholds, alter
masks, or infer a healthy case from missing fields.

## Required contract revision

The next compatible case-package schema should separate:

```text
measurements:
  lesion_present
  lesion_count
  lesion_volume_mm3
  pancreas_volume_mm3
  maximum_lesion_diameter_mm
  component_measurements_uri

review_ordering: optional
  status: available | unavailable
  value: number or null
  display_label: string or null
  policy_id: exact frozen policy or null
  limitations: string[]
```

The field is called ordering/priority—not risk, malignancy, or diagnosis. D-208 defines its source and
meaning. A schema version is never edited in place.

## Review append protocol

1. UI validates action/reasons/note and exact target identities.
2. User confirms the action and target model/prediction.
3. UI sends a draft, expected latest revision, and idempotency key.
4. Writer reloads current history and revalidates action compatibility and revision chain.
5. Writer assigns UUID/time/revision, validates final event schema, and appends under the writer lock.
6. Writer verifies the appended bytes/event and returns a receipt.
7. UI reloads history and shows `Recorded` only when receipt and event agree.

Receipt minimum:

- review event ID;
- exact case-package and prediction IDs;
- revision and predecessor;
- event content SHA-256;
- append sequence or governed location identity;
- recorded timestamp;
- idempotency key/result state.

## Failure behavior

- Schema or target mismatch: reject before append.
- Stale expected revision: conflict; return latest identity, do not auto-rebase.
- Timeout/uncertain response: inspect using the same idempotency key before retry.
- Duplicate key with same content: return original receipt.
- Duplicate key with different content: hard conflict.
- Partial/corrupt trailing JSONL: quarantine/repair through Plan 10 procedure; do not ignore silently.
- Disk unavailable/full: fail without saved claim; retain UI draft.

The writer is the only process allowed to append review events. A future database must preserve the
same logical request/event/receipt contracts.
