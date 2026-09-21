# Review workflow and state model

**Status:** Approved Plan 08 design baseline  
**Decisions:** P08-04 through P08-07 and P08-11 through P08-16  
**Last reviewed:** 2026-09-09

## Workflow invariant

The reviewer always knows:

- which study/package/prediction is active;
- whether the displayed contour is prediction, reference, or discrepancy;
- whether evidence is sufficient, limited, refused, failed, or unavailable;
- whether the review is only a draft, is being submitted, or was durably recorded;
- whether any displayed prior review targets an older prediction.

## Operational state flow

```text
case list
  -> package loading
  -> valid unmarked CT
  -> analysis queued/running (only when needed)
  -> published autonomous prediction
  -> inspect + optional evidence
  -> review draft
  -> confirmation
  -> appending
  -> persisted receipt
```

Any package, viewer, evidence, or writer failure has an explicit state and retry/fallback. Evidence
failure never disables review. Review failure never erases the draft.

## Validation/demo branch

```text
valid prediction
  -> prediction-first inspection
  -> explicit reference reveal
  -> reference / overlap / discrepancy inspection
  -> review decision still targets prediction, not reference
```

Reference reveal cannot occur in `operational_review`. A package with no reference remains complete.

## State ownership

### Artifact state

Immutable values from case package, evidence response, and review events. React components cannot
change them.

### Workflow state

Loading, queued, running, failure, retry, request identity, and adapter capability. A terminal case
package replaces transient analysis state only when its target identity matches.

### Presentation state

2D/3D mode, plane, crosshair/slice, evidence mode, anatomy focus, source focus, opacity, and drawer
state. These changes never alter artifact or review identity.

### Draft state

Action, reasons, note, target IDs, and expected latest revision. A case/prediction change marks an
incompatible draft stale before clearing it; a persisted receipt clears only the submitted draft.

## Race rules

- Every async request carries a local request ID and expected artifact identity.
- Case change aborts supported requests and ignores every late unmatched response.
- Evidence responses render only for their exact question/structured-finding/index identity.
- Analysis completion loads only the published package returned for the requested study/run.
- Duplicate review retry uses an idempotency key; a timeout must inspect before re-appending.
- A write conflict returns the actual latest revision and requires explicit refresh/reconfirm.

## Review semantics

### Accept

The proposed contours and measurements are usable as presented for this research annotation-assist
task. It does not mean pathology confirmed, diagnosis accepted, or reference annotation matched.

### Edit required

The proposal is useful but needs correction. The initial UI records reason/note only; correction may
occur in another tool. A future corrected-mask reference does not modify the prediction.

### Reject

The proposed annotation is unusable, misleading, or cannot be safely assessed. Failed localization
may be rejected without fabricating a mask.

## Revision history

- Revision 1 has no predecessor.
- Revision N+1 names the exact event for revision N.
- Current state is derived from the valid chain, never written as a mutable truth row.
- Branching or a missing predecessor fails validation and requires repair/adjudication.
- Earlier events remain visible with time, action, reasons, and target prediction.

## Reset meanings

- **Reset view:** presentation only; retains package, evidence, and draft.
- **Discard draft:** explicit confirmation; retains artifacts and persisted history.
- **Switch study:** changes active identity and protects/clears incompatible transient state.
- **Reload:** reconstructs from repositories and writer history; never trusts old browser status.
