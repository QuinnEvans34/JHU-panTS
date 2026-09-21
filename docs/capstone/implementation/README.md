# Component implementation plans

Each component has its own implementation file so work can proceed one verified handoff at a time.
These files follow [`../DOCUMENTATION-STANDARD.md`](../DOCUMENTATION-STANDARD.md).

## Sequence and dependencies

```text
01 Architecture + 09 Testing + 10 Operations
  ├── 02 PanTS/cohorts ──> 04 Tested orchestration ──> 05 Imaging ──> 06 Evaluation
  │    └── 03 PANORAMA ──> G2 ──> eligible PANORAMA/mixed-source experiments
  ├── 07 Literature retrieval ──────────────────────────────────────────┐
  └── 08 Review interface <── 11 Stakeholder feedback                   │
                                                                       v
                                                12 Integration and delivery
```

## Status board

| Plan | Status | Must become Ready before |
|---|---|---|
| [01 System architecture](01-system-architecture.md) | Ready | Any substantial implementation |
| [02 Data and cohorts](02-data-and-cohorts.md) | Ready | Week 2 cohort code |
| [03 PANORAMA integration](03-panorama-integration.md) | Ready | Week 3 source adapter; execution requires pinned CT/label snapshots |
| [04 Workflow orchestration](04-workflow-orchestration.md) | Approved design; gated | Explain the plan to Quinton, confirm Plan 10 boundaries, and run the bounded Prefect spike before Week 4 DAG implementation |
| [05 Autonomous imaging](05-autonomous-imaging.md) | Approved design; gated | Confirm Plan 10 resource/retention boundaries before implementation and the Week 5 baseline |
| [06 Evaluation/model experimentation](06-evaluation-and-model-experimentation.md) | Approved design; gated | Plan 09/10 boundaries before metric/registry implementation; G4 before required comparison selection |
| [07 Literature retrieval](07-literature-retrieval.md) | Approved design; gated | Plan 09/10 boundaries before live acquisition/tool installation; D-202 spike before index build |
| [08 Review interface](08-review-interface.md) | Approved design; gated | Plans 09/10 contracts and D-208/neutral-ordering boundary before Week 7 UI changes |
| [09 Testing and quality](09-testing-and-quality.md) | Approved design; gated | Plan 10 environment/lock/evidence boundaries and clean-environment verification before test installation and migration |
| [10 Reproducibility/operations](10-reproducibility-and-operations.md) | Approved design; gated | Confirm exact roots and backup target/budget; test/register `PROWL-Data` and environments through staged setup; retain unencrypted APFS under D-256; old-drive recovery is optional |
| [11 Stakeholder validation](11-stakeholder-validation.md) | Approved design; session pending | Actual participant/fixture/session readiness before the Week 7 walkthrough; outreach does not block early development |
| [12 Integration/delivery](12-integration-and-delivery.md) | Approved design; execution gated | Relevant contracts before each integration step; G1–G7 and verified requirement evidence before a complete release candidate |

## Rule

All twelve designs are approved. Follow [`../IMPLEMENTATION-START.md`](../IMPLEMENTATION-START.md)
for scoped startup: G0-design permits bounded foundation setup; full G0 additionally needs runnable
verification. G2 gates PANORAMA/mixed-source work, not the PanTS-only baseline. Plan 04 retains its
explicit explanation/authorization requirement. Stakeholder scheduling does not block early UI work.

Do not turn every Draft into Ready by removing open questions. Resolve the questions with evidence or
name the fallback and deadline. A bounded blocker is better than false certainty.
