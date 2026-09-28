# Plan 07 approval integration handoff — September 28, 2026

Quinton explicitly confirmed the planning-set approval and directed Codex to complete the
last RUNNING-LOG handoff. Shared reconciliation is complete. The revised
[Phase 3 packet](CLAUDE-PLAN07-P3-PACKET-2026-09-28.md) is issued and ready for Quinton
to dispatch to Claude. No dispatch, installation, acquisition or service launch occurred.

## Reconciliation results

| SCOPE section 10 item | Recorded result |
|---|---|
| D-077 / L-03 | D-261 clarifies baseline + ordered updates and bounded E-utilities checks. |
| P07-05 / corpus channels | Updated the component plan and CORPUS-AND-RIGHTS with event order/replay and PMC Cloud route. |
| D-082 / D-202 | Old engine direction marked superseded; pgvector configuration/embedding evidence remains open. |
| D-211 | Literature answered by D-260; broader relational persistence remains unapproved. |
| L-03 / L-08 / L-09 and approved design | D-261–D-265 record route, frozen embeddings, external database direction, design and provisional controls. |
| D-085 | Span-hit and delivered-evidence amendment recorded as a proposal, not official adoption. |
| Evaluation labels/held-out | Added immutable representation spans, full-containment scoring and encrypted-store lifecycle with honest same-user limitations. |
| Plan 07 sequence | Replaced old engine sequence with P0–P12; response development precedes complete freeze/held-out evaluation. |
| Retrieval tool/query/README | PostgreSQL FTS ts_rank_cd and pgvector; historical tool rationale explicitly retained as superseded. |
| Old foundation packet | Superseded by revised P3 records/passages/query/labels/metrics packet without SQLite. |
| Old decision response D8 | Historical header names SCOPE.md + PHASES.md and replacement packet. |
| Storage aliases | Added optional disabled literature_source and prowl_literature_db to design/schema/example. Real ignored roots.yaml unchanged. |
| Backup/D-258 | Shared 20 GiB cap and 100 GiB floor unchanged; literature allocation deferred to measured P6 proposal. Same-drive database/canonical files are one failure domain. |
| Appendix v3.1 | Preserved unchanged. Reporting must explain the later approved literature-only relational amendment; imaging remains file-first. |

Also updated CURRENT-CHECKPOINT and the current AGENTS pointer. No edits to the seven
Claude-owned planning files. No changes to GROUNDED-RESPONSE, imaging code or real data.

## Verification

Workspace path/root/checker passed. Full native suite: **587 passed**, two existing upstream
torch.jit warnings, 5.05 seconds. Command:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Nine added registry checks verify backward compatibility without literature aliases and
reject attempted activation/role/failure-domain changes to either disabled alias. This does
not implement a production resolver or authorize live paths. Scoped changes reviewed against
the pre-task file snapshot; older unrelated work remains preserved. These tests validate
current Python contracts, not PostgreSQL performance or retrieval quality.

## Remaining decisions and handoff

- Quinton dispatches P3 using its packet; Claude stops after synthetic handback for Codex review.
- Quinton still edits/freezes information needs and reviews seeds (P1/P2).
- D-085 additional metrics remain a decision proposal. Existing ranked recall/MRR stay official.
- Named embedding/generator models remain proposed; execution permissions remain phase-specific.
- P4a resource bars are proposed measurements; external DB layout is an approved direction,
  not a measured configuration. No global Docker change is authorized.
- Include the approved seven-file planning set in the proposed scoped Git checkpoint.
  [Candidate scope](GIT-CHECKPOINT-SCOPE-2026-09-28.md) is prepared; full historical diff and
  publish/privacy review plus explicit authorization remain. No staging/commit/push performed.
- Existing unit-evidence holds and all imaging eligibility/training gates remain unchanged.

## Planning inputs verified unchanged

| File | SHA-256 |
|---|---|
| `PHASES.md` | `b4abe42d9d1b43504087175ab8f168356fd16356e6868402713ada862d1da4ca` |
| `SCOPE.md` | `ca9a0de192cf5d6b241c17ca1796f02b7c39b006e2e9d872afc1c3b767861672` |
| `SEARCH-AND-SELECTION.md` | `bcddbb4b78ba6ab50be059936ecb606fb145b9a1db81f1ab58761edd30c0728c` |
| `RUNNING-LOG.md` | `0697c30751b5f00734d3cd1b84d7250e22d1043a965bce973716ca5cb3e131b7` |
| `ACQUISITION-PLAN.md` | `39e3752005907483d60667603a520ab549f9219dcb17d213f9c6de4f9e99fd2d` |
| `INFORMATION-NEEDS.md` | `5e9764cc94c6d06db4b9b84ec766128aaa6c1d3599fe18f04c8e8d8e9f1a0721` |
| `SEED-SET.md` | `39ee09bc8327c6bccc9f15f859ebf041345bde68385d4a3639134aa6f8f66d81` |
