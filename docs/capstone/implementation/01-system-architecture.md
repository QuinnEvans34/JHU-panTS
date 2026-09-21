# System architecture and contracts

**Status:** Ready  
**Owner:** Quinton Evans  
**Target week:** 1  
**Depends on:** Approved Proposal v3.8; Appendix v3.1  
**Last reviewed:** 2026-09-08

## Outcome

A component architecture and contract set will define how immutable imaging sources, source
adapters, protected cohorts, derived training inputs, autonomous inference, evaluation, literature
retrieval, the UI, and review events interact. Every boundary will specify identity, schema,
versioning, validation, and invalidation behavior before implementation.

## Why this belongs

The approved project joins three data sources and several subsystems. The earlier project already
experienced cohort leakage, train/evaluation mismatch, stale-cache hazards, and lost checkpoints.
Architecture here is the mechanism that makes those failure classes detectable.

## Scope

- System context, component, and data-flow views.
- Canonical identifiers and artifact classes.
- File-first storage boundary and criteria for later persistence services.
- Cross-component input/output contracts.
- Security/privacy, provenance, and non-diagnostic boundaries.

## Non-goals

- Selecting a database or workflow framework without measured requirements.
- Rewriting working training/UI code during architecture planning.
- Designing clinical deployment, PACS integration, or medical-device infrastructure.

## Current state

- `docs/capstone-architecture.md` contains strong artifact-contract ideas but mandates Postgres,
  which the approved appendix no longer requires.
- Existing code uses CSV manifests, text cohort files, YAML configuration, local MLflow, checkpoint
  folders, NIfTI predictions, JSON UI cases, and a FastAPI service.
- Identity and version conventions differ across these artifacts and are not governed by one schema.

## Proposed components

1. Source catalog and adapters: PanTS, PANORAMA, literature.
2. Identity/provenance and protected cohort builder.
3. Preprocessing/cache builder.
4. Workflow orchestrator and run manifest.
5. Autonomous localizer and segmenter.
6. Post-processing, measurement, scoring, and evaluation.
7. Literature corpus/index/retrieval/grounded-response pipeline.
8. Prediction/evidence/review API or file adapter.
9. React/NiiVue review interface.
10. Artifact registry, logs, tests, and release package.

## Core artifact classes

| Artifact | Minimum identity | Immutable? | Invalidated by |
|---|---|:---:|---|
| Source study | source + source subject/study ID + source version | Yes | Never; replace with new source version |
| Annotation | study ID + structure + annotator/provenance + label version | Yes | New label version creates new artifact |
| Unified manifest | schema version + source snapshot hash | Yes | Source/schema change |
| Frozen cohort | definition version + membership hash | Yes | New cohort version only |
| Preprocessed case | source hash + preprocessing hash | Yes | Source/preprocessing change |
| Model run | run ID + cohort hash + config hash + code revision | Yes | Never modified; new run |
| Prediction | study ID + model/run ID + inference config hash | Yes | New model/config |
| Evaluation | prediction-set hash + metric-spec version | Yes | Prediction or metric change |
| Corpus/index | corpus hash + embedding/index config hash | Yes | Corpus/model/index change |
| Evidence response | question + retrieved passage IDs + generation config | Yes | New request/version |
| Review event | review ID + prediction ID + reviewer/session + revision | Append-only | Correction adds revision |

## Invariants

- No derived artifact exists without source identity and configuration/version lineage.
- No inference component receives a ground-truth label or provided pancreas box in autonomous mode.
- No patient/imaging data enters the literature corpus.
- Review decisions do not overwrite predictions.
- No stage overwrites a completed artifact with different content.
- A database, if added, stores metadata and references; raw voxel arrays remain file/object artifacts.
- Every displayed measurement names its source prediction and units.

## Downstream decisions that do not block this contract

- Orchestrator selection is handled in Plan 04 after the stage/state requirements are frozen.
- Vector-index and evidence-response details are handled in Plan 07.
- A database may be reconsidered only if the measured trigger in D-211 occurs.
- Component-specific schemas may add backward-compatible minor versions while preserving these
  identities and boundaries.

## Planning sequence

1. Inventory current artifacts and consumers.
2. Draw current-state data flow without idealizing it.
3. Draw target context/component flow.
4. Define identifiers, schemas, version fields, hashes, and ownership.
5. Define invalidation and partial-failure behavior.
6. Map every contract to tests and risks.
7. Review with Quinton before selecting tools.

## Test matrix

| Level | Scenario | Expected result |
|---|---|---|
| Schema | Required identity/version field missing | Artifact rejected before downstream use |
| Lineage | Preprocessing changes | New artifact identity; stale cache not reused |
| Isolation | Autonomous inference receives only image/input metadata | No label/ground-truth path accessible |
| Separation | Literature pipeline input includes patient record | Validation rejects input |
| Immutability | Completed artifact path rerun with different hash | Fail or create new version; never overwrite |
| Review | Reviewer changes a prior choice | New revision retains prediction and earlier decision |

## Failure modes

- Contract too abstract to test: add concrete examples and schemas.
- Tool choice leaks into requirements: restate behavior independently from technology.
- Old code cannot produce the new contract: add a compatibility adapter before migration.
- Too many artifact types: consolidate only when identity/invalidation semantics are truly equal.

## Acceptance gate

- [x] Current and target architecture diagrams exist.
- [x] Every component has inputs, outputs, identities, and owner.
- [x] Artifact layout and run-manifest schemas are written with examples.
- [x] Invalidation, idempotency, and partial-failure rules are explicit.
- [x] Autonomous, privacy, clinical-claim, and retrieval separation boundaries are testable.
- [x] Plans 02–12 use the same subject/study, case-package, prediction, and review-event terminology.

## Artifacts

- [`../architecture/current-state.md`](../architecture/current-state.md)
- [`../architecture/system-context.md`](../architecture/system-context.md)
- [`../architecture/component-map.md`](../architecture/component-map.md)
- [`../architecture/data-flow.md`](../architecture/data-flow.md)
- [`../contracts/artifact-layout.md`](../contracts/artifact-layout.md)
- [`../contracts/identity-and-versioning.md`](../contracts/identity-and-versioning.md)
- [`../contracts/run-manifest.schema.json`](../contracts/run-manifest.schema.json)
- [`../contracts/case-package.schema.json`](../contracts/case-package.schema.json)
- [`../contracts/review-event.schema.json`](../contracts/review-event.schema.json)
- [`../contracts/VALIDATION.md`](../contracts/VALIDATION.md)

## Handoff

Plans 02, 04, 07, 08, 09, and 10 may now use this architecture baseline and become Ready after their
component-specific questions and tests are resolved.
