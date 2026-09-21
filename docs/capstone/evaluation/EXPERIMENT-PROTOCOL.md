# Experiment protocol

**Status:** Approved Plan 06 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P06-02, P06-11 through P06-15  
**Governing plan:** [`../implementation/06-evaluation-and-model-experimentation.md`](../implementation/06-evaluation-and-model-experimentation.md)

## Purpose

This protocol defines how a model idea becomes a valid experiment and how its result changes the
project. It supports frequent learning without pretending every run is confirmatory.

## Living notebook and evidence chain

Quinton reaffirmed on 2026-09-18 that [`../../experiments.md`](../../experiments.md) remains the living
notebook throughout development. Every experimental run, including a smoke, diagnostic, benchmark,
evaluation-only run, retry, failed attempt, or null result, is represented there. Ordinary automated
unit tests remain in test reports rather than becoming separate scientific experiments.

Before execution, record the game plan and link its immutable preregistration when required. At
launch, attach exact run/attempt and parent artifact identities. After each attempt, append outcome,
evidence, interpretation, and the next decision before launching a follow-up. Each follow-up names
the earlier experiment/evidence that motivated it, the settings or recipe being retained, the new
change, and the unresolved question. A first baseline instead records why it is the starting point.

New notebook entries use `CAP-EXP-NNN`; historical `EXP-*` IDs remain unchanged. The notebook is the
human-readable plan and interpretation; structured immutable artifacts remain authoritative for
executed inputs, metrics, and lineage. If a summary disagrees with those artifacts, append a dated
correction. Do not silently replace an original hypothesis, bar, or result. Notion mirrors links and
status, not an independent scientific record.

Historical future ideas must be reviewed and registered anew under current contracts. Prior
checkpoints remain ineligible as capstone initialization, and old proposals for tuning against the
publisher-test cohort are not executable capstone plans. A successful exploratory run can inform the
next controlled experiment, but cannot be retrospectively relabeled as controlled evidence.

## Run classes

| Class | Question type | Design strength | Permitted conclusion |
|---|---|---|---|
| `smoke` | Does the path execute and satisfy a binary gate? | Bounded correctness record | Working/not working under stated fixture |
| `diagnostic` | Which mechanism is plausible? | Frozen measurement and interpretation branches | Mechanism evidence, not model superiority |
| `exploratory` | What setting/intervention is worth formal testing? | Declared factors/cohort/metrics before run | Hypothesis generation and candidate ranking |
| `controlled` | Does intervention X beat/control Y under a preregistered rule? | Matched design and immutable preregistration | Accept/reject/inconclusive for that hypothesis |
| `confirmatory` | How does the frozen selected system perform on untouched data? | Release freeze plus final holdout | Generalization estimate, no tuning response |
| `stabilization` | Can the selected design be reproduced after a verified defect/failure? | Same scientific design and incident record | Restored/reproduced artifact, no new model claim |
| `historical` | What did the preceding project already show? | Imported provenance only | Context and hypotheses, never capstone model evidence |

Classification is immutable after start. A new question requires a new experiment version.

## Experiment record

Required before any nontrivial run:

- experiment ID/version/title/owner/status;
- notebook entry and motivating parent experiment/evidence references, or initial-baseline rationale;
- run class and decision/gate it serves;
- question, hypothesis, null, and mechanism;
- control/treatment or measurement definitions;
- exact changed factors and fixed factors;
- data/cohort/reference/prediction roles and hashes;
- initialization/model/preprocessing/training/inference/metric identities;
- primary endpoint and direction;
- critical non-inferiority guardrails;
- descriptive secondary metrics and subgroups;
- sample size/eligibility and resampling unit;
- decision bar and `accepted`/`rejected`/`inconclusive` logic;
- maximum steps/time/cost/storage and operational stop rules;
- smoke/validity gates;
- expected outputs and retention class;
- known confounds and limits; and
- timestamp/content hash proving design existed before treatment results.

Smoke runs need a smaller form but still require identity, expected gate, cost ceiling, and output.

## Changed-factor audit

Before a controlled comparison, generate a machine-readable diff across:

- cohort membership and reference annotations;
- source/annotation sampling;
- initialization/checkpoint ancestry;
- model architecture and output head;
- preprocessing, ROI, spacing, augmentation, and cache identity;
- loss, optimizer, schedule, batch/sampling, seed, and horizon;
- checkpoint selection/resume behavior;
- inference, post-processing, score, and threshold policy;
- metric version and uncertainty; and
- code/environment/resource settings.

Every difference is either the declared intervention, a necessary coupled change listed in the
intervention block, or a confound. An unexplained difference blocks controlled status.

## Single-variable and coherent-block experiments

Prefer one changed variable when it answers the question. Some practical interventions require a
coupled block—for example a new architecture may require a different head or memory-compatible batch
size. The block is acceptable when:

- the hypothesis concerns the complete practical intervention;
- all coupled differences are declared before execution;
- the conclusion is about the block, not an individual internal change; and
- a later isolation study is promised only if the answer is important enough.

Do not describe a block result as proof that one unisolated setting caused the difference.

## Baseline-driven required comparison

After G4, score each candidate intervention on:

| Dimension | Question |
|---|---|
| User impact | Would it reduce missed lesions, false alarms, review burden, invalid outputs, or latency? |
| Failure prevalence | How often and how severely does the baseline failure occur? |
| Mechanism | Is there evidence the intervention addresses that failure? |
| Identifiability | Can the comparison isolate a useful conclusion? |
| Feasibility | Can training/inference/evaluation finish before the freeze with recovery margin? |
| Reuse | Does the answer improve several downstream components? |
| Risk | Could the intervention weaken coverage, pancreas performance, or reproducibility? |

Record every candidate and the selection rationale. D-205 chooses one required comparison; other
exploratory work may continue if it does not threaten the critical path.

## Execution protocol

1. Validate experiment/preregistration content and hash.
2. Validate every parent cohort/artifact/model/environment/resource identity.
3. Run synthetic/overfit/smoke gates.
4. Publish the final resolved config and changed-factor audit before full treatment compute.
5. Execute control and treatment with the declared schedule and resource policy.
6. Preserve all attempts, checkpoints, logs, and terminal reasons.
7. Publish complete prediction sets under the same registered evaluation cohort.
8. Run the same metric version and paired comparison preflight.
9. Produce point/interval/per-case/subgroup/guardrail evidence.
10. Apply the preregistered decision rule before writing the narrative.
11. Record deviations and result status.
12. Append the result and interpretation to `docs/experiments.md`, link exact run/evidence IDs, and
    record the evidence-based next experiment or stop/defer decision.
13. Update the experiment queue and affected decision/risk/traceability entries.

## Intermediate reads and stopping

Allowed stopping reasons:

- nonfinite training or corrupted state;
- failed target/data/spatial/output validity gate;
- resource/schedule breach under the preregistered ceiling;
- exact preregistered futility rule; or
- external interruption recorded by orchestration.

An unfavorable interim score is not enough unless the futility rule says it is. A favorable interim
score is not an accept decision unless the preregistration defines a valid early-success rule. Both
arms receive equivalent opportunities under the declared horizon.

## Result states

| State | Meaning |
|---|---|
| `accepted` | Primary bar passes and all required guardrails pass |
| `rejected` | Primary bar fails or a critical guardrail fails at a valid evaluation horizon |
| `inconclusive` | Valid result does not distinguish the preregistered decision regions |
| `invalid` | Scientific/contract defect prevents interpretation |
| `operationally_failed` | Run could not complete for resource/environment/orchestration reason |
| `canceled` | Intentionally stopped before valid result; reason preserved |

A rejected experiment may still contain an interesting secondary observation. That observation enters
the exploratory queue; it does not rewrite the original result.

## Amendments

An amendment records old/new content, reason, author, time, and whether treatment results were already
available. Pre-result clarifications may preserve controlled status if they do not change the
substantive hypothesis. Post-result endpoint/bar/cohort changes create exploratory follow-up and do
not alter the original decision.

## Model promotion

A model becomes a release candidate only if:

- its run class and comparison allow promotion;
- all required lineage/cohort/config/checkpoint evidence validates;
- primary result and critical guardrails satisfy the recorded rule;
- autonomous rather than provided-region evidence is available;
- source/subgroup failures are reviewed;
- runtime/storage/UI requirements remain feasible; and
- the selection decision names the exact model/cascade/policy IDs.

An exploratory model that looks best must be rerun or evaluated through the controlled/frozen process
before promotion.

## Historical import

Import preceding-project entries with:

- original experiment ID/title/date/text/result where available;
- historical code/cohort/checkpoint/evaluation provenance;
- known contamination, oracle, metric, or reproducibility limitations;
- reusable lesson/hypothesis; and
- `capstone_candidate=false`.

Do not clean up uncomfortable nulls or failed runs. Their purpose is to prevent repetition.

## Required tests

- preregistration hash/timestamp precedes treatment result;
- immutable run class and result history;
- changed-factor diff identifies planted confound;
- control/treatment cohort mismatch blocks comparison;
- one-sided arm termination without declared rule invalidates comparison;
- null/guardrail result maps to correct decision state;
- post-result amendment cannot preserve controlled status improperly;
- exploratory model cannot enter release manifest directly;
- historical checkpoint/model is never capstone-promotable; and
- Notion/GitHub summary cannot mutate authoritative result fields.

Documentation review also checks that every experimental attempt has a pre-run notebook plan and a
terminal entry, and that follow-up plans name motivating evidence without rewriting prior outcomes.
