# Test taxonomy and quality gates

**Status:** Approved design; implementation remains gated  
**Decisions:** P09-04 through P09-13 and P09-19 through P09-20  
**Last reviewed:** 2026-09-09

## Test layers

| Layer | Primary question | Typical fixture | Failure means |
|---|---|---|---|
| Static/config | Is configuration/schema/test collection valid? | Small control records | Stop before runtime |
| Unit | Does one pure rule produce the exact expected result? | Hand-authored arrays/records | Logic defect |
| Contract | Can valid records pass and invalid records fail consistently? | Positive/negative JSON | Boundary defect |
| Component | Does one service/adapter/UI component honor its contract? | Stubbed controlled dependency | Component defect |
| Integration | Do real components exchange the same meaning? | Synthetic/tiny files | Interface defect |
| Data quality | Are source facts, labels, identities, grids, and exclusions valid? | Synthetic plus local-real | Data/adapter issue |
| Failure injection | Does interruption/conflict/absence fail and recover safely? | Temporary artifact roots | Reliability defect |
| Browser | Does a user-visible workflow work in a real browser? | Canonical UI fixture server | UI integration defect |
| Local-real/MPS | Does actual data/hardware/library behavior satisfy the contract? | Pinned local manifest | Environment/scientific-path defect |
| End-to-end | Does source-to-review complete with exact lineage? | Release candidate fixture/run | System defect |
| Manual/stakeholder | Is display, wording, workflow, and alignment understandable/honest? | Named build/cases | UX/scientific review finding |

## Marker rules

Register every marker in strict configuration. A test may carry multiple markers; for example a
local NIfTI/MPS integration can be `integration`, `licensed_data`, `mps`, and `slow`.

External-resource markers are capability declarations. They are excluded from ordinary fast
selection and become hard preflight requirements when explicitly selected.

## Gate matrix

| Gate | Required suites | May remain open |
|---|---|---|
| G0-design | Approved plans, contracts, risk/test ownership, and scoped setup order | Executable setup evidence; bounded environment/fixture/test setup is permitted |
| G0-verification | Clean install, collection, historical baseline/classification, core contracts, fast commands | Product tests for unimplemented components, each traced; full G0 requires both checkpoints |
| Data/cohort implementation | Fast identity/contracts + source-local real validation | Model/retrieval/UI suites |
| Orchestration implementation | Stage/state/idempotency + failure injection | Expensive model run |
| Model run authorization | Data/cohort, geometry, input/lineage, checkpoint, resume, preflight | Final-quality metrics |
| Retrieval build authorization | Rights/corpus/query/index fixtures + tool spike | Generated response if G6 not ready |
| UI implementation | Contract/adapters/reducers + build | Stakeholder changes not yet selected |
| G6 retrieval | Corpus/index/retrieval/response/refusal held-out evidence | Optional generation polish |
| G7 workflow | UI component/browser/accessibility + persistence + stakeholder | Deferred stretch features |
| G8 release candidate | Full fast/integration/local-real/MPS/browser/E2E/manual matrix | Only explicitly accepted non-critical limitations |

## Change-to-test routing

- Schema/record change: all schema positive/negative, canonicalization, producers, consumers, and
  compatibility tests.
- Identity/hash/invalidation change: affected artifact lineage and stale-reuse tests.
- Preprocessing/spatial change: tiny geometry, cached/uncached, training/inference, source-space
  roundtrip, and real overlay tests.
- Model/loss/training change: construction, weights/gradients, smoke/overfit, resume, lineage, and
  Plan 06 evaluation—not a hardcoded accuracy unit test.
- Metric change: all independent golden cases plus affected report/UI derivation.
- Corpus/chunk/query/index change: rights/identity/rebuild, known relevance, and response citation.
- UI change: reducer/component/build, critical browser if workflow affected, manual viewer/zoom where
  visual behavior changes.
- Review writer change: append, lock/conflict, idempotency, partial/truncated file, receipt, reload,
  and revision chain.
- Orchestrator change: artifact authority and framework-loss/retry/resume tests.

## Formal run rules

- Record first run; a later rerun does not erase it.
- Fix code when the contract is correct; revise test and contract together when the contract changes.
- Never reduce an assertion, expand tolerance, or exclude a case only to obtain green.
- Release runs start from clean process state and declared cache state.
- Manual checklists name the exact build/artifacts and are not copied forward automatically.
- A defect may be accepted only if the affected requirement is non-critical or removed/deferred with
  explicit scope and user-facing limitation.
