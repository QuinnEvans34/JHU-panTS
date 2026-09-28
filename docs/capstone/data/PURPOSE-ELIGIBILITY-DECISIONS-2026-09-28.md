# Preserve source data; qualify use by purpose

September 28, 2026. Owner: Quinton Evans. Status: agreed policy and case dispositions;
implementation/publication pending. This is the Codex data lane, separate from the
concurrent Plan 07 review. No shared retrieval decisions amended.

## Decision and rationale

Quinton agreed with purpose-specific eligibility and preserving original data/membership.
He added: "As long as we dont delete data, and test both through out training then we
should be fine."

Preserve source scans, masks, evidence, historical packages and accepted base memberships.
Eligibility for a particular training or evaluation purpose is recorded separately.
Do not delete or silently replace difficult examples. Equally, do not use a missing,
unqualified or out-of-coverage target as though it were a verified negative.

Unusual but valid examples may be valuable for robustness. Exclusions must follow
predeclared task/evidence criteria, not whether a model scores poorly on the example.
No evidence reviewed here establishes the prevalence of unusual scans in held-out data.

## Agreed present dispositions

| Item | Decision | Retained uncertainty |
|---|---|---|
| Case 78 | Exclude from pancreas-present localizer training eligibility; preserve original training membership and source records | Selected-plane coverage review supports hip/pelvis coverage; it is not an exhaustive expert read or a disease assessment |
| Cases 2 and 266 | Keep geometry-dependent training uses blocked while physical units remain unresolved | Plausible spacing alone is not evidence of mm; this is a hold, not a permanent all-purpose exclusion |
| All cases | Grant uses separately by purpose, backed by evidence | Readability, binary decoding or a passing software test does not establish annotation provenance, rights or scientific suitability |

Case 78 must not become a disease-negative example or move into validation/test.
Any future out-of-coverage robustness use needs a defined task, qualified target and
registered train-role membership. It is not activated by this decision.

## Meaning of "test both": both comparisons confirmed

Quinton explicitly confirmed both: compare training with/without qualified unusual
categories, and evaluate each approach on ordinary and unusual groups. He wants broad
experimentation to establish what works and what does not. This approves the experiment
direction; exact categories, targets, runs and budgets still need their game plans.

For a given comparison, use the same evaluation groups for both training approaches.
Report results for each group and a prespecified aggregate where scientifically valid.
Keep other factors matched where practical; if sample size, class balance or compute
changes with inclusion, control it or explicitly record the confounding. Use small
train-role pilots to check feasibility before committing larger resources. Prioritize
experiments that answer distinct questions; record failures and null results alongside
improvements. Broader experimentation remains subject to the protected Week 9/10 schedule.

Unusual categories require explicit definitions. Valid difficult anatomy, missing
physical units and out-of-coverage scans are not interchangeable. A with/without arm
cannot bypass an unresolved eligibility hold. Out-of-coverage behavior requires its own
appropriate task and metrics; it cannot silently become pancreas-present supervision
or disease-negative evaluation.

Existing protected-role rules continue to apply. Repeated model development uses
registered training cohorts and the designated development-validation protocol.
Protected final-test data must not guide inclusion policies, model choice or thresholds.
Do not move known training cases into held-out evaluation or call training robustness
checks evidence of generalization. Any evaluation exclusions/failures and denominators
must be reported explicitly; difficult cases cannot silently disappear from headline
metrics. Task-specific metrics for out-of-coverage scans must be defined before scoring.

A future comparison needs a prior game plan in `docs/experiments.md`: hypothesis,
qualified categories, cohort identities, matched evaluation, retained/changed factors,
metrics, acceptance criteria and resource budget. Every attempt/outcome is recorded.
This note launches no experiment and does not allow training with unqualified targets.

## Evidence and next steps

- [Case 78 coverage](CASE78-COVERAGE-REVIEW-2026-09-28.md).
- [Spatial-unit evidence and approved paired-CT inference boundary](SPATIAL-UNITS-REVIEW-2026-09-28.md).
- [Five-study evidence, including case 266](VOXEL-FOLLOWUP-RESULTS-2026-09-28.md).
- [Policy lineage and remaining holds](BINARY-POLICY-LINEAGE-2026-09-28.md).
- [First-experiment gates](../operations/FIRST-EXPERIMENT-READINESS-2026-09-28.md).

Next discussion: define a bounded unit-evidence search for cases 2/266 with an explicit
stopping point. Then address source-protocol applicability and remaining qualification
requirements before publishing new purpose dispositions/cohorts. Then draft the
confirmed two-part experiment matrix with exact categories, matched evaluation groups,
metrics and budgets before registering individual runs.

Future implementation must preserve original membership and artifacts, reject these
cases for the disallowed purposes, and retain the evidence/decision linkage. Any new
package needs a new identity and verified hashes; historical issue records stay intact.
No source reads, code changes, package publication or test execution occurred in this
documentation pass. Last verified suite remains 578 passes with two upstream warnings.
