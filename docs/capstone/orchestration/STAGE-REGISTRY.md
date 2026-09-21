# Workflow stage registry specification

**Status:** Approved Plan 04 design baseline; not implemented  
**Version:** 0.1 approved design  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/04-workflow-orchestration.md`](../implementation/04-workflow-orchestration.md)

## Purpose

This registry names every committed orchestration boundary before code wraps it. It prevents the
runner from discovering steps through filenames, importing arbitrary scripts, or deciding scientific
order at runtime. Component plans own scientific behavior; Plan 04 owns dependency, execution,
validation, state, and recovery behavior.

## Required declaration for every stage

| Field | Meaning |
|---|---|
| `stage_id` | Stable lowercase identifier; unique across the registry |
| `component_version` | Version of the wrapper/scientific interface, not the orchestration tool |
| `owner_plan` | Plan responsible for scientific meaning and domain validation |
| `depends_on` | Exact upstream stage IDs; must form an acyclic graph |
| `input_types` / `output_types` | Registered artifact types and controlling schemas |
| `config_selector` | Exact resolved-configuration subset included in derivation identity |
| `preflight` / `postvalidate` | Validators run before work and before publication |
| `retry_class` | `none`, `transient_io`, `bounded_process`, or `checkpoint_resume` |
| `resource_class` | `cpu_light`, `cpu_heavy`, `io_heavy`, `accelerator_exclusive`, or `service_local` |
| `locks` | Root, artifact-family, accelerator, port, or other named exclusive resources |
| `capacity_rule` | Forecast plus reserve required at the destination root before writing |
| `entry_point` | Stable Python callable or CLI adapter; never a shell-text blob |
| `timeout/cancel` | Deadline and declared cooperative cancellation boundary |
| `determinism` | Seed or explicit statement that output is content-deterministic |

All paths inside artifact references are relative URIs or root-alias references. Absolute paths may
be resolved locally at execution but are not registry identities.

## Imaging workflow

| Stage | Owner | Depends on | Inputs | Published output | Retry/resource |
|---|---|---|---|---|---|
| `preflight_roots` | 10 | — | Root registry, workflow capacity estimate | Root-preflight report | None / CPU light |
| `snapshot_sources` | 02, 03, 10 | `preflight_roots` | Publisher files/releases/licenses | Source snapshot and file inventory | Transient I/O / I/O heavy |
| `build_manifest` | 02, 03 | `snapshot_sources` | Pinned source snapshots, adapter config | Unified manifest package and issues | None / CPU light |
| `build_cohorts` | 02, 03 | `build_manifest` | Manifest, duplicate/adjudication records, cohort definition | Frozen cohort package | None / CPU light |
| `build_prepared_cache` | 05, 10 | `build_cohorts` | Frozen train-role cohort, annotations, preprocessing config | Prepared-cache version | Bounded process / I/O heavy |
| `train_model` | 05, 06, 10 | `build_prepared_cache` | Prepared cache, frozen cohort, model/training config | Model version and checkpoints | Checkpoint resume / accelerator exclusive |
| `infer_autonomous` | 05 | `train_model` | Model version, evaluation cohort, inference config, full CTs | Raw autonomous prediction set | Checkpoint/bounded resume / accelerator exclusive |
| `postprocess_measure` | 05, 06 | `infer_autonomous` | Raw predictions, spacing/affine, processing config | Processed predictions and measurements | Bounded process / CPU heavy |
| `evaluate_model` | 06 | `postprocess_measure` | Prediction set, protected references, metric specification | Evaluation artifact | Bounded process / CPU heavy |
| `export_review_cases` | 08 | `postprocess_measure` | Selected predictions/measurements and display config | Review-case payload artifacts | Bounded process / CPU/I/O heavy |

`infer_autonomous` receives no ground-truth annotation or provided ROI. `evaluate_model` is the first
stage permitted to resolve protected references for scoring. Orchestration validation must enforce
that separation rather than trusting the called function.

## Literature workflow

| Stage | Owner | Depends on | Inputs | Published output | Retry/resource |
|---|---|---|---|---|---|
| `preflight_literature` | 07, 10 | — | Rights policy, network/local roots, corpus request | Rights/access preflight report | None / CPU light |
| `snapshot_literature` | 07 | `preflight_literature` | Permitted metadata/text endpoints or files | Corpus-source snapshot | Transient I/O / I/O heavy |
| `build_corpus` | 07 | `snapshot_literature` | Source snapshot and inclusion rules | Corpus manifest and normalized documents | Bounded process / CPU light |
| `build_passages` | 07 | `build_corpus` | Corpus version and chunking config | Stable passage records | Bounded process / CPU heavy |
| `embed_passages` | 07, 10 | `build_passages` | Passage set and embedding config | Embedding artifact | Bounded process / CPU/accelerator as selected |
| `build_index` | 07 | `embed_passages` | Embeddings, metadata, index config | Versioned local vector index | Bounded process / CPU heavy |
| `evaluate_retrieval` | 07 | `build_index` | Frozen question set, index, retrieval config | Recall@k/MRR evaluation | None / CPU light |
| `evaluate_responses` | 07 | `evaluate_retrieval` | Retrieved passages, response/refusal config, labels | Groundedness/refusal evaluation | Bounded process / service local or CPU |
| `export_evidence_fixture` | 07, 08 | `evaluate_responses` | Selected queries/passages/responses | Evidence-response fixtures | None / CPU light |

The literature workflow accepts no patient image, source report, ground-truth imaging label, or
direct source identifier. Structured non-identifying findings enter only at query/evidence-response
time under Plan 07's contract.

## Integration and release workflows

| Stage | Owner | Depends on | Inputs | Published output | Retry/resource |
|---|---|---|---|---|---|
| `select_integration_versions` | 08, 12 | — | Exact prediction, measurement, evidence, UI build IDs | Selection manifest | None / CPU light |
| `assemble_case_packages` | 08 | `select_integration_versions` | Selected artifacts, case-package config | Case-package versions | Bounded process / I/O heavy |
| `validate_case_packages` | 01, 08, 09 | `assemble_case_packages` | Case packages and schema/domain validators | Validation report | None / CPU light |
| `smoke_review_transport` | 08, 09 | `validate_case_packages` | Valid packages, static/FastAPI adapters, UI fixture | Transport/UI smoke report | Bounded process / service local |
| `build_release_package` | 12 | `smoke_review_transport` | Exact permitted artifacts, docs, model card, test evidence | Immutable release package | None / I/O heavy |

Release selection never uses `latest`, filesystem modification time, or an MLflow display name as
identity. The selected IDs and hashes are explicit inputs.

## Named workflow profiles

| Workflow | Required stages | Purpose |
|---|---|---|
| `imaging_data_smoke` | roots → snapshots → manifest → cohorts → prepared cache | Prove multi-source data reaches preprocessing without training |
| `imaging_baseline` | Full imaging path through evaluation | Produce one new autonomous baseline and evaluation |
| `imaging_export` | Existing valid prediction set → processing/export | Build review artifacts without retraining |
| `retrieval_smoke` | Literature path through retrieval evaluation | Prove local corpus/index/retrieval behavior |
| `retrieval_full` | Full literature path through response evaluation/export | Produce validated evidence fixtures |
| `integration_smoke` | Select → assemble → validate → transport smoke | Exercise the review contract with fixed artifacts |
| `release_candidate` | Integration smoke → release package | Package exact locked artifacts after G8 |

Profiles select a subgraph and configuration; they do not redefine stages. A new stage or changed
dependency requires a registry version and graph-validation evidence.

## Resource and concurrency policy

- Default maximum stage concurrency is one.
- `accelerator_exclusive` stages acquire one host/device lock; they never overlap.
- Artifact-family writers acquire a lock keyed by destination root, artifact type, and derivation ID.
- CPU-light validation may overlap only with an accelerator stage when measured memory and I/O use is
  safe and neither reads the same external-drive files intensively.
- Two I/O-heavy stages do not run concurrently on the same external root by default.
- Local services reserve an explicit port and record it only as runtime evidence, not artifact
  identity.
- Notion/GitHub updates occur after scientific publication and hold no workflow resource lock.

## Registry validation tests

- Stage IDs are unique and match the naming pattern.
- Dependencies exist and the complete graph is acyclic.
- Every required input is produced upstream or declared as an external input.
- Every output type has an owning schema/validator and artifact-layout location.
- Relevant config selectors resolve and are non-overlapping only when intentional.
- Resource/retry classes are valid and every expensive stage has an exclusive-resource policy.
- Named workflow profiles resolve to connected valid subgraphs.
- Autonomous inference has no protected-reference input edge.
- Release selection contains no convenience-pointer input.
