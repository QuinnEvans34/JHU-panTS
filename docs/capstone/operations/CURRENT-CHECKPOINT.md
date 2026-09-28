# Current PROWL checkpoint

Updated September 28, 2026 during the scoped Git review and next data-slice planning.
This is the current navigation/status summary. Earlier dated checkpoints retain their
historical evidence, not current authorization. Read component plans and evidence before
acting; this summary does not waive gates or supersede Quinton's latest instructions.

## Start here in a new conversation

1. Confirm checkout `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
   Run `pwd`, `git rev-parse --show-toplevel`, `git status --short`, and
   `python3 scripts/diagnostics/check_workspace.py` there. Never recreate the former path.
2. Read `AGENTS.md`, `WORKSPACE-SAFETY.md`, this file, and `../README.md`.
3. Read the relevant component plan, decision amendments, and the evidence listed below.
4. State the task, owned paths, acceptance tests and prohibited actions before edits.
   Missing evidence is a blocker to the affected claim, not permission to reconstruct facts.

## Verified checkpoint

- Last native Python suite run (Git review, excluding Claude's active retrieval tests): **587 passed**, two existing upstream
  torch.jit warnings. Command:
  `env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests --ignore=tests/retrieval -q -p no:cacheprovider`.
- Data evidence: `../data/MANIFEST-V2-SLICE-2026-09-28.md` records five training studies,
  ten quarantined annotations, twenty blocking holds and zero eligibility. These holds
  are not twenty corrupt files. All 25 recorded package hashes were rechecked and the
  five manifest output files replayed identically from persisted inputs in this task.
- D-259 explicitly approves the strict binary rule. Read
  `../data/BINARY-DECODING-APPROVAL-2026-09-28.md`. Approved policy identity exists;
  no training wiring, bulk normalization, annotation promotion or source modification.
- Approved lineage verification is implemented alongside the unchanged structural
  validator; 25 added tests bind policy identity/tolerance and approval/implementation
  bytes to independently reviewed pins. No schema change or new real-data package.
  See `../data/BINARY-POLICY-LINEAGE-2026-09-28.md` for evidence and trust boundaries.
  Existing annotations retain null mappings and quarantine; future approved-mapping
  publication must explicitly invoke the new verifier with reviewed inputs.
- Acquisition/extraction evidence exists; complete source qualification, frozen production
  cohorts and G1 remain open. Publisher-test images remain outside the work scope.
- No capstone experiment launched. `../../experiments.md` remains the living notebook:
  preregister every experiment and record every attempt/result. No prior project-trained
  checkpoint reuse. Official course begins October 5; week 9 buffer, week 10 delivery.
- This checkpoint did not access the external drive. Recheck identity and authorization
  before any future operation; do not infer mount/process state from this document.
- The working tree contains extensive existing modified/untracked work. No staging,
  commit, push or cleanup occurred. A Git revision alone cannot reproduce this checkpoint.

## Ownership and latest architecture

- Codex owns data qualification, shared contracts/decisions and integration review.
- Quinton confirmed approval of Claude's seven Plan 07 planning files. Codex recorded
  D-261–D-265 and reconciled shared documents. See
  `PLAN07-INTEGRATION-HANDOFF-2026-09-28.md` for scope, evidence and remaining gates.
  Claude's planning files were preserved byte-for-byte during reconciliation.
  Subsequently Claude recorded Quinton's approval and froze INFORMATION-NEEDS v1:
  25 needs, nine refusal families, unchanged 60-question evaluation size. SHA-256
  `d71577c27cebd5d54f516a7b2120273c3afba7dc077be3799bae4ccecbde8ac0` was verified
  against RUNNING-LOG. P1 is complete; seed review remains pending. Quinton now explicitly
  confirms Claude is working on P3; RUNNING-LOG also records the start. Claude reports
  Linux-container testing because the Mac venv cannot run in its VM; Codex must perform
  native verification at handback. No native P3 result is claimed yet.
- Read `POSTGRES-PGVECTOR-DECISION-2026-09-28.md` (D-260). Literature-only PostgreSQL +
  pgvector replaces the SQLite/LanceDB direction. Canonical files remain authoritative;
  the database is a rebuildable operational query layer. Imaging stays file-first.
- `CLAUDE-PLAN07-P3-PACKET-2026-09-28.md` was dispatched by Quinton and is active;
  its new retrieval implementation paths remain reserved for Claude.
  The earlier foundation packet is superseded. The old decision response is historical
  where D-260–D-265 differ. Span/delivered metric adoption remains a proposed D-085 amendment.
  Literature registry aliases are optional disabled placeholders, not live root bindings.
- Plan 04 explanation completed; coding/tool-spike authorization remains separate.
  Stakeholder preparation remains deferred until Quinton requests it or secures a participant.

## Next bounded Codex data task

The prior policy-lineage task is complete; its finding, code scope, tests and remaining
purpose-specific holds are in `../data/BINARY-POLICY-LINEAGE-2026-09-28.md`.

Quinton agreed to preserving originals/base membership while qualifying use separately
by purpose. See `../data/PURPOSE-ELIGIBILITY-DECISIONS-2026-09-28.md`: exclude case 78
from pancreas-present localizer training; keep cases 2/266 blocked for geometry-dependent
training pending unit evidence. These decisions are documented, not yet published into
new machine-readable dispositions/cohorts. Existing packages remain unchanged.

The approved bounded unit-evidence investigation is complete. See
`../data/UNIT-EVIDENCE-INVESTIGATION-2026-09-28.md`: paper, release documentation,
publisher issue replies and downstream preprocessing code do not establish units for
the acquired unknown-unit files. Both cases remain on hold. Two retained diagnostic
receipts passed all 26 file-hash checks; no raw data accessed. A precise publisher
question is drafted but not sent. A standalone sendable message, including the separate
release-license clarification, is now in `../data/PANTS-PUBLISHER-EMAIL-DRAFT-2026-09-28.md`.
Quinton will send it himself in a couple of days; no contact or reminder automation occurred.
The [Git review](GIT-CHECKPOINT-REVIEW-2026-09-28.md) prepares a specific public-repository
checkpoint for agreement before commit/push. Claude's active implementation is excluded.
The next data slice is specified in
`../data/PURPOSE-DISPOSITION-IMPLEMENTATION-2026-09-28.md`: tested purpose-specific
rejection using existing issues, followed by qualification/cohort/run prerequisites.
That proposal is not implemented and grants no eligibility or smoke-run permission.
Quinton confirmed
both comparisons: train with/without qualified unusual categories, and evaluate each
approach on fixed ordinary/unusual groups. Broad experimentation is the intended
direction; exact categories, targets, matched comparisons and budgets need preregistered
run plans after qualification. Protected final-test data remain outside iterative development.
Biological subject identity, source provenance and terms remain open. This investigation
changed documentation only; no software tests rerun or unit override introduced.

No additional serialization layer is justified. Any future diagnostic package needs a
new identity and verified input/output hashes; preserve the five-study package and its
historical mapping status. G1, cohort publication and training remain gated.

## Claude handback review gate

Planning reconciliation is complete. After Quinton dispatches the revised P3 packet and
Claude returns implementation, review its synthetic contracts, evidence and tests against
the packet and D-260–D-265 before P4b. Do not infer installation, corpus-download or model
permission from planning approval. P1 is frozen; P2 seed review remains Quinton's work.

## Recommended conversation/agent protocol

Use one integration conversation plus bounded component conversations when requested.
Each task packet names its objective, required reading, allowed paths, shared interfaces,
acceptance commands, evidence outputs, prohibited actions and handback requirements.
Only the integration owner edits shared decisions/contracts after review. Parallel agents
must not edit the same files or independently launch writers/accelerator jobs.

At every handoff, update this summary in place (do not prepend another competing latest
status), retain dated evidence, and report changed files, actual tests, unresolved gates and
the exact next action. A new agent first summarizes these boundaries back to Quinton.
This is a recommended working protocol, not permission to spawn tasks or create worktrees.

Suggested new-conversation prompt:

> Continue PROWL in /Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL.
> Read AGENTS.md and docs/capstone/operations/CURRENT-CHECKPOINT.md, then the linked
> task-specific evidence. Verify the checkout and existing changes. Summarize current
> approvals, blockers and Claude ownership, then continue the next bounded Codex data
> task. Do not launch training, touch publisher-test data, install databases, or overwrite
> Claude's planning files. Review Claude's plan when I provide it. Preserve prior artifacts.

## Deferred housekeeping

AGENTS.md and several hubs still contain accumulated historical status prose. The explicit
current pointers avoid treating it as current; a later scoped consolidation should preserve
history while making AGENTS.md a shorter rules/index document. Notion reconciliation and a
reviewed Git checkpoint also remain pending. Do not mark either complete from this handoff.
