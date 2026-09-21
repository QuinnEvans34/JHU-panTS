# Continuous training strategy

**Status:** Approved Plan 06 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P06-01, P06-02, and P06-13  
**Governing plan:** [`../implementation/06-evaluation-and-model-experimentation.md`](../implementation/06-evaluation-and-model-experimentation.md)

## Purpose

Training is an overarching capstone workstream. The objective is not to keep the GPU busy for its own
sake; it is to use the full project window to reduce uncertainty, gather evidence, and discover
failures early while other work continues.

## Operating principle

```text
prepare question -> clear dependencies -> run smallest falsification gate
-> start bounded training -> archive result -> update knowledge -> choose next question
```

No calendar week grants permission by itself. A run may begin when its data role, input/target
contract, initialization, output identity, metric, compute budget, stop rule, and storage destination
are valid for that run class.

## Calendar behavior

| Period | Allowed model work | Required boundary |
|---|---|---|
| Week 1 planning | Read-only audits and only discovery spikes necessary to make a plan accurate | No long run before G0 documentation/readiness review |
| Weeks 1–2 after G0 | Train-role smoke, overfit, timing, localizer-target, spatial, and exploratory development runs | No untrusted cohort, PANORAMA mixing, or publisher-test use |
| Week 3 | PanTS work continues; PANORAMA arms only after G2 | Source/annotation strata remain explicit |
| Week 4 | Pipeline/DAG-integrated repeats and reproducibility runs | Expensive baseline waits for G3; small component runs may proceed when independent |
| Week 5 | Formal autonomous baseline plus continued diagnostics | G4 evidence required before required comparison selection |
| Week 6 | Required controlled comparison and operating-policy analysis; other useful runs may continue | Controlled claims use frozen matched design |
| Weeks 7–8 | Targeted improvements, integration regression, selected-model finalization | Stop model search early enough to freeze before final evaluation |
| Week 9 | Stabilization reruns only | Same selected design; verified defect or operational failure; no new hypothesis |
| Week 10 | No result-changing model work | Delivery, demonstration, documentation, and presentation only |

This schedule means model learning spans development without allowing a late experiment to destabilize
the approved release buffer.

## Experiment queue fields

Every queued item records:

- priority and short name;
- `CAP-EXP-NNN` entry in [`../../experiments.md`](../../experiments.md), with its pre-run game plan;
- motivating prior experiment/evidence IDs, retained settings, and proposed next change;
- run class;
- question and information gained if successful, null, or failed;
- dependency/gate state;
- exact planned cohort/model/config parent identities;
- changed factor or intervention block;
- expected setup, smoke, and full-run duration;
- CPU/MPS, memory, external-drive bandwidth, and storage requirements;
- prerequisite code/tests;
- output/retention class;
- maximum compute/cost and abort conditions;
- earliest start/deadline; and
- what becomes unblocked by the answer.

Queue order is a plan, not permission. The Plan 04 operator preflight remains authoritative at start.

## Priority score

Qualitatively rank each candidate on:

1. **Invalidation risk:** could the answer show that current results are wrong?
2. **Critical-path value:** does it unlock G1–G5 or final delivery?
3. **Information value:** does it distinguish between plausible mechanisms?
4. **User value:** does it address missed lesions, false alarms, review burden, or reproducibility?
5. **Time to answer:** can a short diagnostic settle it before a full run?
6. **Reuse:** will the artifact support multiple later decisions?
7. **Operational fit:** can it run safely while other work proceeds?

Correctness and invalidation risks outrank a potentially higher Dice score.

## Required run ladder

Unless a stage is purely evaluation-only, advance through:

1. **Static preflight:** schema, cohort role, paths/roots, hashes, initialization, config, storage.
2. **Synthetic/unit gate:** target/preprocessing/output behavior on deterministic fixtures.
3. **Tiny overfit or functional gate:** verify loss can move and outputs are structurally correct.
4. **Short smoke:** bounded real-data steps plus checkpoint/resume and full-volume inference.
5. **Timing forecast:** measured step/validation/inference rates and final storage estimate.
6. **Full planned horizon:** no intervention changes after start.
7. **Terminal validation:** checkpoint/result schema, hashes, counts, logs, completion marker.
8. **Registered evaluation:** exact prediction set and metric version.
9. **Evidence update:** append every attempt's result, decision, caveats, and next consequence to
   `docs/experiments.md`; link immutable registry/evidence records and then update Notion/GitHub links.

A failed rung stops later rungs until the reason is understood or a new run version is registered.

## Working in parallel

The workstation has one primary accelerator and external storage roots. Parallel work is therefore
about human/task overlap more than simultaneous heavy compute.

- One MPS training/inference owner at a time by default.
- Documentation, code review, retrieval design, or UI fixture work may proceed while a stable run is
  active.
- CPU-heavy preprocessing or external-drive scans run concurrently only after measured evidence says
  they do not destabilize training or saturate the drive.
- No two writers target one model, cache, prediction, evaluation, or registry destination.
- Health inspection is read-only and does not modify the run.
- A new run does not start until the preceding terminal output is validated and archived.

Plan 04 owns runtime locks and state; Plan 10 owns capacity and environment rules.

## Monitoring without intermediate cherry-picking

Permitted health signals:

- process alive/heartbeat and current stage;
- finite loss/gradients and configured learning rate;
- CPU/MPS memory pressure and fallback warnings;
- step throughput and forecast;
- checkpoint/write health; and
- predeclared overfit/smoke gate metric.

Intermediate validation may support the preregistered checkpoint-selection rule. It cannot be used to
change the hypothesis, select a new primary endpoint, stop only an unfavorable arm, or declare an
early winner unless that rule was fixed in advance. Intermediate observations remain in logs.

## Exploration budget

The exact hours are selected in Plan 10, but each week should reserve capacity for:

- critical-path required runs;
- one or more cheap diagnostics/smokes;
- the highest-value exploratory candidate when resources remain; and
- rerun/recovery headroom.

Do not fill all forecast capacity. A queue with no recovery headroom repeats the schedule problem the
professor asked the proposal to correct.

## Weekly evidence review

At least weekly, answer:

1. What ran, completed, failed, or was canceled?
2. What exact uncertainty did each run reduce?
3. Which conclusion is trustworthy, exploratory, null, invalid, or still pending?
4. Did new evidence change the failure-model ranking?
5. Are repeated runs testing the same idea under new names?
6. Which checkpoint/prediction artifacts must remain pinned?
7. What is the shortest next test that could change a decision?
8. Does the next run threaten a milestone, Week 9 buffer, or storage/compute reserve?

After each attempt, update the immutable experiment/run evidence and append its interpretation and
next decision to `docs/experiments.md`; do not wait for the weekly review. Use that review to reorder
the queue from accumulated evidence. Update Notion from the linked records afterward.

## Start strategy after documentation

Once all plans complete the G0 readiness review, do not immediately launch the longest model. Hold a
specific experiment-strategy session that:

1. audits the current code against Plans 02, 05, 06, 09, and 10;
2. identifies code that must exist before any valid new training;
3. separates reusable functions from historical entry points;
4. defines the first correctness fixtures and smoke cohorts;
5. estimates localizer/segmenter/preprocessing runtime on the 4 TB drive and MPS machine;
6. orders the first two weeks of smoke, diagnostic, and exploratory runs; and
7. writes the exact start gate for the first capstone training command.

This session is a required transition from planning to implementation and will explain why the queue
is ordered as it is.

## Stop/freeze behavior

- End open model search early enough in Week 8 to build and evaluate the release candidate.
- Week 9 training needs a verified defect/failed execution record and must preserve the selected
  scientific design.
- Week 10 does not accept a newly trained model into the release, even if a background run happens to
  score better.
- Unfinished exploratory work is documented as future work rather than allowed to blur delivery.

## Evidence

- versioned queue snapshots;
- run preregistrations and resolved preflights;
- health/failure/terminal records;
- weekly evidence reviews;
- pinned checkpoint/prediction retention list;
- measured runtime/capacity forecasts; and
- release-freeze audit proving no late experiment changed the selected system.
