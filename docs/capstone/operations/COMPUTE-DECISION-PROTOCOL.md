# Compute benchmark and decision protocol

**Status:** Approved Plan 10 design, 2026-09-18; D-210 remains open pending evidence  
**Decisions:** P10-20 through P10-23  
**Last reviewed:** 2026-09-18

## Purpose

Decide whether the approved capstone can finish reliably on Quinton's Apple M5 Pro workstation and,
only if measured evidence says no, define a bounded case for rented CUDA compute. The decision is
about critical-path feasibility and correctness, not chasing maximum hardware speed.

## Default

Local MPS remains the default because it:

- keeps source data and restricted local artifacts under the existing workstation boundary;
- avoids upload, provider, cost, teardown, and cloud-persistence work;
- matches the environment Quinton will use for development and demonstration;
- has already run meaningful 3D MONAI experiments during the preceding project;
- supports overnight/background experimentation when resource locks and storage are safe.

Historical timing is useful context but not a capstone benchmark because the data roots, autonomous
cascade, environment, cohort scale, storage device, and pipeline may change.

## Questions the benchmark must answer

1. Is source I/O or preprocessing the bottleneck before MPS compute?
2. Does the prepared cache reduce total wall time enough to justify its storage cost?
3. Can the localizer and segmenter fit and run reliably at the approved tensor policies?
4. How long does one baseline horizon, one controlled comparison, and a full development evaluation
   take—not just one training step?
5. How much work is lost and repeated after interruption/resume?
6. Can retrieval/index/UI work proceed while training without unsafe writer/MPS contention?
7. Does the complete planned queue fit G4/G5/G8 dates with 25% contingency?
8. Would remote transfer/environment validation/teardown save critical-path time after their overhead?

## Benchmark artifact

Every result is an immutable benchmark record, not a copied terminal time. Required fields:

- benchmark ID/version/status and hypothesis/question;
- code commit/clean state and environment ID;
- source snapshot/cohort/sample IDs and case characteristics;
- root aliases, physical failure domains, filesystem, cache state, and bytes;
- stage/config/model/tensor/batch/worker/device/precision settings;
- warm-up count and timed window;
- repeat count, raw timing samples, median/range;
- throughput, wall time, peak memory if measurable, disk bytes/rate, and CPU/GPU observations;
- fallback warnings, MPS/CPU operations, OOM/disconnect/retry events;
- projected full workload, run count, available windows, and 25% contingency;
- decision implication and limitations.

## Benchmark suite

### B1 — external storage

Use a fixed representative file set on the proposed source/artifact volume:

- sequential large-file read;
- case-wise NIfTI open/header/payload read;
- representative write/hash/publish/read-back;
- cold versus warm state labeled honestly;
- compression/decompression CPU cost separated when possible.

Purpose: determine whether storage/cable/filesystem or computation dominates.

### B2 — preparation/cache

Use a frozen train-role sample covering size/spacing/positive status diversity:

- uncached full preparation;
- prepared-cache write and validation;
- cached reload;
- bytes per study and projected full-cohort size;
- parity of cached/uncached tensors under Plan 09 tolerance.

Purpose: decide what should be cached, not merely whether cache is faster.

### B3 — training

For localizer and segmenter separately where their workloads differ:

- run a warm-up sufficient to exclude first-iteration compilation/allocation artifacts;
- time a fixed representative iteration window long enough to smooth loader variation;
- record validation/checkpoint overhead separately;
- test chosen and safe alternative batch/worker/precision settings one variable at a time;
- verify model outputs/gradients/lineage, not performance quality.

Projection includes planned iterations/epochs, validation frequency, checkpointing, and expected
restarts. It does not multiply the fastest isolated step by epochs while ignoring the rest.

### B4 — autonomous inference/evaluation

Use a fixed development sample containing:

- lesion-positive and lesion-negative studies;
- small/difficult lesions and varied scan geometry where available;
- localizer success/failure paths;
- full source-volume preprocessing, localization, ROI extraction, segmenter inference, restoration,
  post-processing, measurement, prediction publication, and evaluation.

Record per-stage and total case time, memory, output bytes, and failure rate. Extrapolate by actual
evaluation cohort count.

### B5 — retrieval

- corpus ingest/normalization throughput;
- embedding throughput and memory;
- index build/write/reopen time and bytes;
- fixed query latency distribution;
- response-generation path separately, if approved.

Purpose: determine whether embedding/index work competes materially with imaging or remains a safe
parallel CPU/storage task.

### B6 — interruption/resume

Inject a controlled interruption at a checkpointable stage:

- measure work retained, validation/recovery time, and repeated work;
- prove keeper/current artifact protection;
- verify resource locks and state after termination;
- project realistic failure overhead.

## Schedule projection

The projection inventories required and likely work:

- baseline localizer smoke/diagnostic/training/evaluation;
- baseline segmenter/cascade work;
- continuous exploratory queue with strict priority and bounded budget;
- one required controlled comparison and confirmatory rerun if planned;
- operating-policy evaluation;
- full development and frozen publisher-test execution;
- retrieval build/evaluation;
- integration/regression/release reruns;
- known unavailable nights/days and exclusive MPS constraints.

For every workload:

```text
projected_wall_time = measured_component_time
                    × planned_scale
                    + validation/checkpoint/publication overhead
                    + expected recovery overhead
```

Then apply at least 25% schedule contingency to critical-path compute. Week 9 cannot be counted as
capacity for a new experiment; it is available only for defect-driven stabilization reruns. Week 10
cannot be counted for result-changing work.

## D-210 decision states

| State | Meaning |
|---|---|
| `local_default_pending_benchmark` | Current planning state; no remote action authorized |
| `local_selected` | Required work fits with contingency and no correctness/memory blocker |
| `remote_proposal_required` | One trigger is met; provider/cost/data plan must be reviewed |
| `remote_approved` | Quinton separately approved exact provider/hardware/spend/upload scope |
| `scope_reduced_local` | Remote path rejected/unavailable; required claim/horizon narrowed honestly |
| `remote_completed` | Outputs verified locally and remote teardown evidence recorded |

## Trigger for a remote proposal

At least one must be demonstrated:

- a required operation is unsupported/incorrect on MPS after a bounded diagnosis and CPU fallback is
  not schedule-feasible;
- approved baseline tensor/model/inference cannot fit local memory under a scientifically acceptable
  configuration;
- repeated MPS instability persists after environment, data, worker, precision, and resource-lock
  controls;
- the complete measured local critical path misses G4/G5/G8 with 25% contingency despite prioritizing
  required over optional work.

Faster CUDA alone is not a trigger. A large exploratory queue is not a trigger unless the required
critical path itself is infeasible.

## Required remote proposal

Before any purchase or upload, document:

- exact trigger and immutable local benchmark/projection IDs;
- workload and scientific reason it cannot simply be reduced/deferred;
- candidate provider, region, GPU, CPU, memory, disk, image/environment, and availability risk;
- hourly/storage/egress prices observed at the time and a total Quinton-approved spending ceiling;
- setup, queue, upload, download, validation, and teardown time;
- source license/privacy/de-identification and provider storage/retention boundary;
- exact minimized upload/download manifest and encryption/access controls;
- matched smoke and output-comparability policy;
- checkpoint/resume and spot/preemption decision;
- local artifact destination and capacity;
- deletion/teardown evidence and fallback if provider or budget fails.

Prices/providers are deliberately not selected during Plan 10 design because they are time-sensitive
and no trigger or spending authority exists.

## Matched remote smoke

Before a long remote job:

1. install/verify the separate locked remote environment;
2. use a synthetic or smallest permitted fixed sample;
3. run preprocessing and one forward/training/inference path;
4. compare shape, geometry, finiteness, deterministic controls, and numerical tolerance—not bitwise
   MPS/CUDA equality;
5. publish a remote environment/smoke record locally;
6. verify checkpoint upload/download/hash/load;
7. proceed only if the platform difference is understood.

If the final comparison relies on hardware-sensitive training, both experimental arms should run on
the same selected platform under matched conditions unless the hardware factor is itself explicit.

## Remote data and security boundary

- Verify the exact source terms before upload; “public” is not equivalent to unrestricted cloud use.
- Upload only the approved cohort/material needed for the workload.
- Never upload review notes, secrets, unrelated source snapshots, or the entire local artifact root.
- Use private access, encrypted transport/storage where supported, and no public links.
- Keep secrets out of images, scripts, shell history, manifests, and logs.
- Disable unnecessary provider logging/snapshots and record what the provider retains.
- Download terminal manifests, logs, checkpoints, metrics, and checksums to the verified local root.
- Validate and back up selected keepers before deleting remote resources.
- Record instance/volume/object deletion; do not claim impossible guarantees beyond provider evidence.
- Remote storage never becomes the only authoritative copy.

## Decision outcomes

### If local is selected

- freeze local environment and storage settings used for the projection;
- schedule exclusive MPS windows and safe parallel CPU/retrieval work;
- checkpoint at the measured recovery interval;
- monitor actual versus projected duration and reopen D-210 only on a defined trigger.

### If remote is approved

- execute only the authorized workload/spend/upload set;
- keep the local workflow and contracts authoritative;
- report platform differences and matched controls;
- stop at ceiling/trigger rather than silently spending more;
- complete download/verification/backup/teardown before calling the run complete.

### If remote is not approved or feasible

Prioritize required evidence:

1. valid autonomous baseline;
2. one controlled comparison at an honest horizon/cohort;
3. frozen evaluation and integrated workflow;
4. exploratory breadth only after those fit.

Reduce iterations, cohort, comparisons, or optional scope transparently with amended preregistration
before results, never by dropping difficult cases or weakening the evaluation denominator.

## Acceptance gate

- [ ] Storage and preparation benchmarks use the verified 4 TB roots.
- [ ] Localizer, segmenter, full cascade, evaluation, retrieval, publication, and recovery timings are
  recorded or explicitly not on the critical path.
- [ ] Full required-work projection includes overhead, exclusive resources, and 25% contingency.
- [ ] D-210 records `local_selected`, `remote_proposal_required`, or `scope_reduced_local` with evidence.
- [ ] No remote action occurs without a later explicit provider/spend/data approval.
- [ ] Actual run durations are compared with projections and material deviations update the risk plan.
