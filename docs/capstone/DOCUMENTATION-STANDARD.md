# Implementation-plan standard

**Status:** Active  
**Applies to:** Every file under `docs/capstone/implementation/`

The purpose of these plans is to remove avoidable uncertainty before code is written. A plan should
allow Quinton or a future AI session to understand what is being built, why it belongs in the
approved project, what may not be changed casually, how failure will be detected, and when the work
is genuinely complete.

## Plan status vocabulary

- **Outline** — component is identified but major design work remains.
- **Draft** — scope, dependencies, risks, sequence, and initial tests are recorded.
- **Approved design; gated** — Quinton approved the design, but named operational/contract/evidence
  prerequisites remain. Approval is not implementation completion.
- **Ready** — blocking choices are resolved, contracts are precise, and acceptance tests are defined.
- **Active** — implementation is underway.
- **Blocked** — a named dependency or decision prevents safe progress.
- **Complete** — every acceptance criterion has linked evidence.
- **Superseded** — replaced by a named document or decision; retained for history.

## Required sections

Every implementation plan must contain:

1. **Metadata** — status, owner, target week, dependencies, source requirements, last review date.
2. **Outcome** — a one-paragraph statement of what will exist when complete.
3. **Why it belongs** — connection to the proposal, user workflow, or a measured failure.
4. **Scope and non-goals** — explicit boundaries against scope creep.
5. **Current state** — reusable code, known results, missing pieces, and technical debt.
6. **Inputs and outputs** — schemas, units, identity rules, paths, and version requirements.
7. **Invariants** — rules that must always hold, preferably enforceable by tests.
8. **Open decisions** — options, selection evidence, decision deadline, and fallback.
9. **Implementation sequence** — small ordered changes with a testable outcome after each step.
10. **Test matrix** — unit, integration, regression, data-quality, performance, and manual checks as
    applicable.
11. **Failure modes** — expected ways the implementation can go wrong, detection signal, prevention,
    and recovery.
12. **Observability and evidence** — logs, manifests, reports, screenshots, metrics, and lineage.
13. **Acceptance gate** — binary conditions for declaring the component complete.
14. **Rollback or fallback** — how to recover without corrupting data or losing earlier behavior.
15. **Artifacts** — exact files or reports that should be created.
16. **Handoff** — what plan becomes eligible next and what context it needs.

## Definition of ready

Readiness is scoped to the work about to begin. G0-design permits the bounded environment, fixture,
and test setup needed to prove G0-verification; full G0 requires both. See
[`IMPLEMENTATION-START.md`](IMPLEMENTATION-START.md). A component can remain gated for real-data or
production execution while an explicitly bounded synthetic/setup task proceeds under its approved
design. This is not permission to bypass Plan 04's separate explanation/authorization gate.

A plan may be marked `Ready` only when:

- it is consistent with proposal v3.8 and appendix v3.1;
- required inputs are available or a tested fallback exists;
- every externally visible output has a schema or wireframe;
- every cross-component boundary has an owner and contract;
- privacy, licensing, data leakage, and clinical-claim risks have been reviewed;
- unit and integration tests are named before implementation;
- success and failure are measurable;
- the recovery path does not require overwriting source data or old artifacts;
- effort fits the approved schedule without consuming Weeks 9 or 10 for new scope.

## Definition of complete

`Code runs` is not sufficient. Completion requires:

- tests pass in the documented environment;
- output artifacts validate against their schemas;
- results are reproducible from recorded inputs, configuration, code revision, and seed where
  relevant;
- acceptance criteria have evidence links;
- known limitations are recorded;
- decisions and risks are updated;
- no previous source artifact or historical result was overwritten.

## Decision protocol

Use a decision record when a choice changes architecture, scientific interpretation, schedule,
data use, or user behavior. Record options before choosing. The smallest reversible implementation
is preferred when options perform similarly. A tool is selected because it meets a requirement, not
because an older draft named it.

## Update cadence

- Before implementation: confirm the relevant design is approved and the scoped task is Ready;
  retain any broader pending prerequisites instead of declaring the whole component ready early.
- During implementation: record discoveries that alter sequence, risk, or interfaces.
- After implementation: link verification evidence and update the handoff.
- Weekly: review the master plan, traceability table, decision register, and risk register together.
- Never rewrite an experiment's original hypothesis or result; append corrections and new decisions.

## Planning quality check

Before marking a plan Ready, ask:

- What assumption would make this design invalid?
- What input can be malformed, missing, duplicated, or stale?
- What looks successful while being scientifically wrong?
- What can leak evaluation information?
- What can silently differ between training and inference?
- What happens after interruption or partial completion?
- Which result would cause us to stop, simplify, or choose the fallback?
- What will Quinton see and approve before the implementation becomes expensive to change?
