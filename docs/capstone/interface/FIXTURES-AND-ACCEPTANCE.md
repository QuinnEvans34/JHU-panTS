# Interface fixtures and G7 acceptance evidence

**Status:** Approved Plan 08 design baseline; fixture creation gated  
**Decision:** P08-18  
**Last reviewed:** 2026-09-09

## Fixture policy

Committed interface tests use synthetic or licensed non-voxel control records and tiny generated
NIfTI/display assets. Local real-case fixtures remain off-Git when required and are identified through
content-hashed manifests. Every fixture states the behavior it proves; showcase quality is not a
selection criterion.

## Minimum scenario set

| Fixture ID | Scenario | Required proof |
|---|---|---|
| UI-F01 | Operational positive | Prediction/measurement/warning render with no reference dependency |
| UI-F02 | Operational negative | Absence is explicit evidence, not a missing-field fallback |
| UI-F03 | Multiple lesions | All lesion components remain inspectable and measured |
| UI-F04 | Localization low confidence | Warning persists across views; review can continue appropriately |
| UI-F05 | Localization/prediction failure | No blank-success contour; reject reason available |
| UI-F06 | Validation reference locked | Reference assets/metrics unavailable before reveal |
| UI-F07 | False-positive validation case | Prediction/reference/discrepancy remain visibly distinct |
| UI-F08 | Evidence sufficient | Every claim resolves to returned passage/source |
| UI-F09 | Evidence insufficient | Refusal/ranked passages; no generated answer |
| UI-F10 | Evidence unavailable | Review remains possible; failure is explicit |
| UI-F11 | Review append/reload | Durable receipt and reconstructed history match |
| UI-F12 | Review revision | New event supersedes old; both retained |
| UI-F13 | Stale prediction | Old review never appears as current for new prediction |
| UI-F14 | Invalid/unsupported package | Fail closed before scientific rendering |
| UI-F15 | Request race | Late result from prior case/question is discarded |
| UI-F16 | Static export only | UI says exported/not recorded, never saved |
| UI-F17 | Writer timeout/idempotent retry | Exactly one durable event |
| UI-F18 | Viewer/WebGL failure | Honest error plus non-canvas workflow context |

## Transport parity fixture

One canonical package and all referenced bytes are served through:

1. local static files; and
2. FastAPI.

The validator/view model must produce identical schema values, identities, warnings, measurements,
layer content hashes, evidence references, and capabilities except explicitly normalized transport
URLs. A difference in scientific content fails the adapter.

## Historical visual fixtures

The preceding project's strong positive, true negative, and large false-positive examples remain
useful for NiiVue and visual regression. They are adapted into new capstone packages or clearly marked
legacy; the old `results.json` is never relabeled as contract-valid without transformation and
validation evidence.

## Test ownership

| Layer | Primary proof | Owner plan |
|---|---|---|
| Reducer/state transitions | Exact pure state tests | 08/09 |
| Schema/view model | Valid/invalid golden records | 01/08/09 |
| Static/FastAPI parity | Adapter integration | 08/09/10 |
| Review append/history | Writer integration/failure injection | 08/09/10 |
| Evidence citation/refusal | Response/UI integration | 07/08/09 |
| NiiVue layers/alignment | Real-browser plus manual scientific check | 08/09 |
| Stakeholder task | Observed protocol | 11 |
| Release critical flow | End-to-end run package | 12 |

## G7 evidence package

The completion record contains:

- UI source/build identity and environment;
- exact fixture and schema hashes;
- component/browser test reports;
- static/FastAPI parity report;
- append/reload/revision/idempotency evidence;
- accessibility scan plus manual keyboard/zoom/viewer checklist;
- responsive screenshots;
- stakeholder protocol, findings, approved changes, and deferrals;
- user-visible claim review;
- known limitations and unresolved defects.

G7 fails if the demonstrated decision exists only in browser storage, the reference is required for
operational review, unsupported evidence reaches the UI, or a stale review is shown beside a new
prediction.
