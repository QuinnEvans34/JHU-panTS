# Workflow state, publication, and recovery contract

**Status:** Approved Plan 04 design baseline; not implemented  
**Version:** 0.1 approved design  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/04-workflow-orchestration.md`](../implementation/04-workflow-orchestration.md)

## Authority order

When records disagree, use this order:

1. schema-valid published artifact plus matching content/derivation hashes and completion evidence;
2. terminal PROWL workflow record and append-only stage-attempt events;
3. atomic current `run.json` summary reconstructed from those events;
4. Prefect local state/UI, when installed;
5. MLflow display state and console logs.

Prefect and MLflow supply useful observation. Neither can turn incomplete or invalid bytes into a
valid scientific artifact.

## Run and stage states

The existing run-manifest v1.0 values remain the compact summary vocabulary.

### Run states

| State | Meaning | Permitted next state |
|---|---|---|
| `planned` | Graph/config resolved; no stage mutation has begun | `running`, `cancelled` |
| `running` | At least one stage attempt may execute or await a declared resource | `completed`, `failed`, `cancelled` |
| `completed` | Every required stage is `completed` or independently verified `reused` | Terminal |
| `failed` | A required path reached an unrecovered failure | Terminal; recovery creates a new linked run |
| `cancelled` | Operator requested stop and no further stages may launch | Terminal; recovery creates a new linked run |

### Stage summary states

| State | Meaning |
|---|---|
| `pending` | Required but no attempt has started |
| `running` | Current attempt holds its declared locks and has a start event |
| `completed` | This run executed and published a validated artifact |
| `reused` | A pre-existing published artifact independently passed current validation |
| `failed` | Latest attempt failed and the run will not retry it further |
| `skipped` | Stage is outside the selected conditional path; never used to hide a required failure |

A retry does not erase a failed attempt. `run.json` shows the latest summary; the event stream retains
the full history.

## Append-only event contract

Plan 04 will add `workflow-event.schema.json`. Every event contains at least:

- `schema_version`, globally unique `event_id`, `run_id`, `stage_id`, and integer `attempt`;
- `event_type`: `run_planned`, `run_started`, `stage_started`, `stage_reused`, `stage_retry_scheduled`,
  `stage_completed`, `stage_failed`, `stage_cancel_requested`, `stage_cancelled`, `run_completed`,
  `run_failed`, `run_cancelled`, `lock_acquired`, `lock_released`, or `partial_quarantined`;
- UTC timestamp and monotonic sequence within the run;
- DAG and stage-registry versions/hashes;
- host/process identity and orchestrator adapter/version;
- stage derivation hash and relevant configuration hash where applicable;
- exact input/output artifact references where applicable;
- retry classification, error type/message/details reference, and selected recovery action;
- log URI and Prefect flow/task IDs when present.

Events are written to an attempt-local append-only log with flush/durability behavior defined by Plan
10. `run.json` is an atomic projection and may be rebuilt from valid events.

## Idempotency and reuse algorithm

For every stage:

1. Resolve exact registered inputs and verify their schema, completion, content hash, and allowed use.
2. Resolve the complete workflow configuration and extract the stage's declared relevant subset.
3. Compute the derivation hash from artifact type/schema, ordered input identities and hashes,
   relevant configuration, code identity, and component version.
4. Resolve the one expected canonical output identity; do not scan for similarly named files.
5. If a published output exists, revalidate schema, completion, content hash, derivation hash, and
   domain postconditions.
6. If every check passes, append `stage_reused` and continue without execution.
7. If an existing candidate conflicts, quarantine/record it and fail closed; never overwrite it.
8. Otherwise create an attempt directory beneath the destination artifact filesystem and append
   `stage_started` after required locks are acquired.
9. Execute the component only inside its declared attempt/output boundary.
10. Validate expected files, schemas, hashes, counts, scientific invariants, and capacity.
11. Publish atomically at the destination and write completion evidence last.
12. Append `stage_completed`, release locks, and update `run.json` atomically.

The same derivation hash does not permit reuse when bytes or domain validation disagree. A content
hash alone does not permit reuse when derivation/configuration identity differs.

## Attempt and publication layout

```text
outputs/prowl/workflows/<run-token>/
├── run.json
├── resolved-config.yaml
├── events/workflow-events.jsonl
├── logs/<stage-id>/attempt-<n>.log
├── attempts/<stage-id>/attempt-<n>/...
├── quarantine/<stage-id>/attempt-<n>/...
└── COMPLETE.json | FAILED.json | CANCELLED.json
```

Scientific output is prepared on the same filesystem as its canonical destination. If an external
drive is the destination, the attempt directory also lives on that drive. Cross-device moves are
treated as copies: copy into a destination-local attempt, validate, then publish locally. The runner
must not represent a laptop-to-drive move as atomic.

## Error classes and retry policy

| Class | Examples | Automatic behavior |
|---|---|---|
| `non_retryable_input` | Missing required artifact, wrong schema/hash, forbidden cohort role, unknown label value, geometry failure | Fail path immediately; correct input through a new artifact/run |
| `non_retryable_scientific` | Metric invariant failure, leakage check, invalid autonomous input, privacy boundary violation | Fail immediately and preserve evidence |
| `transient_io` | Temporary network read, drive read temporarily unavailable after verified mount, recoverable file-lock contention | Bounded retry with backoff after root/lock revalidation |
| `bounded_process` | Worker exits before publication without a deterministic data error | At most configured attempts; quarantine each partial |
| `checkpoint_resume` | Training/inference interrupted after a validated checkpoint | No blind restart; schedule an explicit checkpoint-linked attempt |
| `operator_cancel` | SIGINT or requested stop | Cooperative safe-boundary stop; no automatic retry |

Every stage declares its allowed class and maximum attempts. Unrecognized errors default to
non-retryable until reviewed. Expensive stages default to zero automatic from-scratch retries.

## Training and long-running work

- Training owns an exclusive accelerator lock and a model-attempt directory.
- A checkpoint is a partial recovery artifact, not a completed model version.
- Checkpoint metadata must name cohort, preprocessing, model/training configuration, code,
  environment, step/epoch, optimizer/scheduler state, and checksum.
- Resume revalidates that identity before launching. Mismatch creates a new experiment decision or a
  clean run, never an override.
- `best` and `last` may be convenience filenames inside one immutable attempt; their controlling
  model/checkpoint IDs remain explicit.
- SIGINT requests the component's safe checkpoint boundary. SIGKILL/power loss leaves no completion
  marker and recovery uses only the last independently valid checkpoint.
- MLflow run identity is recorded but does not replace the model or workflow artifact manifest.

## Locks and stale owners

Each lock record contains lock type/key, run/stage/attempt, host, process, acquired time, heartbeat,
and lease policy. Required locks include:

- one accelerator lock per actual device;
- one writer lock per destination artifact family and derivation ID;
- one root-intensive I/O lock where concurrent reading/writing threatens stability;
- one local-service port lock where applicable.

A stale lock is not removed merely because it is old. Recovery verifies host/process liveness or an
expired lease, records the evidence, appends a release/recovery event, and only then reacquires it.

## Resume algorithm

1. Load the terminal/interrupted run, registry version, resolved configuration, and events.
2. Create a new recovery run when the earlier run is terminal; set `resume_of` to its run ID.
3. Re-resolve root aliases and verify root identity, capacity, permissions, code/environment policy,
   and current locks.
4. Recompute stage derivations and validate every completed/reused output independently.
5. Reuse the longest valid dependency closure, not merely the longest list of green task states.
6. Quarantine invalid partials/conflicts and stop if upstream identity changed unexpectedly.
7. Resume the earliest incomplete stage; use a checkpoint only after its stage-specific validator.
8. Preserve both run histories and link the recovery decision/evidence.

If the user intentionally changes configuration, inputs, code, or environment, this is a new run that
may reuse unaffected ancestors by derivation identity; it is not presented as continuation of the
same computation.

## Framework-loss test

After a successful smoke workflow:

1. preserve PROWL artifacts/events;
2. stop or point away from the local Prefect server/database;
3. run `inspect` and validate the prior outputs from PROWL records;
4. request the same workflow through direct local execution or a fresh local Prefect state;
5. verify complete stages are independently classified `reused`.

Failure means the framework has become an undeclared source of truth and cannot be selected for G3.

## Cleanup boundary

Partial and quarantined attempts are never deleted automatically during a run. The operator receives
a generated cleanup candidate list with reason, size, age, parent run, and confirmation that no
published artifact references it. Plan 10 owns retention and recoverable deletion behavior.
