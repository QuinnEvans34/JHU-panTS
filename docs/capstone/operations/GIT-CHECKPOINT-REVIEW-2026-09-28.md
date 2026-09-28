# Scoped Git checkpoint review

September 28, 2026. Prepared for Quinton's agreement before commit/push.
No files staged, commits created, branches changed or remote content written.

## Proposed checkpoint

Preserve the September acquisition/data-contract work, synthetic tests, qualification
evidence notes, approved Plan 07 planning/reconciliation and next-step documentation.
Suggested commit subject: `Checkpoint September data qualification and approved retrieval planning`.

Base: main at `f4d7109b466fc12854be4a86c9893750399a0672`.
Configured origin: https://github.com/QuinnEvans34/JHU-panTS, default branch main.
Read-only GitHub metadata check confirmed **PUBLIC** visibility. Publication is therefore
public, not merely a private off-device backup. Local commit and remote push are separate
actions for Quinton to agree to after this review.

The exact path/byte/hash inventory is
[GIT-CHECKPOINT-FILES-2026-09-28.json](GIT-CHECKPOINT-FILES-2026-09-28.json).
That control file is also part of the proposal but excludes its own hash to avoid recursion.
The reviewed byte copies and patch are retained temporarily outside the checkout for
comparison; they are not another clone/worktree or a durable independent backup.
Revalidate the base, candidate bytes and index before staging. Preserve subsequent edits
as uncommitted changes; never revert the shared workspace to this snapshot.

## Review findings and scope

- Reviewed tracked changes and the data-contract, source-evidence, extraction and diagnostic
  boundaries, with tests for non-promoting records, hash/relationship checks, protected roles,
  archive safety, bounded reads and preservation of failed/partial artifacts.
- Corrected stale current-status pointers in AGENTS, the documentation hub and implementation
  entry point. Dated historical evidence retains its original counts/status.
- The initial 110-file inventory contained only Markdown, Python, JSON and example YAML;
  no binary payload, symlink or file above 250,000 bytes. The final manifest adds this
  review and the later email/next-slice documentation, with the same checks repeated.
- Pattern checks for private keys, common GitHub/AWS credentials, credential-bearing URLs
  and long assigned secret literals found no matches. This is a bounded publication check,
  not a guarantee that every possible secret format is detected.
- Existing local checkout paths, public dataset IDs/hashes, internal evidence references
  and owner name remain in the planning/audit documentation. These are intentional context,
  not live credentials; they will be visible in a public push.
- No raw scans/masks, private patient reports, source workbook, model weights, downloaded
  literature or held-out question/label content is proposed for publication.
- Source archives, local configuration and ignored outputs remain off Git. Evidence notes
  identify local receipts; a clone cannot replay real-data audits without those separately
  retained inputs. This checkpoint is not a backup of all evidence or a G1 completion claim.
- Native non-retrieval tests: **587 passed**, two existing torch.jit deprecation warnings,
  5.03 seconds. No source-drive access, extraction or training was run.
- Python candidates parse; JSON candidates load. Candidate document links resolve against
  the proposed file set plus tracked HEAD. No new software behavior was introduced by
  this review; the purpose guard is a proposal only.
- `git diff --check` reports the two pre-existing Markdown hard-break spaces in
  DATA-ACQUISITION-QUEUE lines 3–4. Preserve their intentional formatting. Other scoped
  whitespace errors must be absent before staging.

This is a preservation/publication review of a diagnostic foundation, not certification
of production ingestion, cohort consumers, full source integrity or scientific validity.

## Claude boundary

Exclude src/retrieval, tests/retrieval, contracts/retrieval and Claude's new foundation
design/handback files until its handback review. Do not stage by directory or wildcard.
The manifest pins the existing planning RUNNING-LOG through the observed P3-start entry;
later appends are not part of this reviewed snapshot. The P3-start entry reports Linux
testing limitations, not completed native verification. Claude owns its active files.

Also exclude unrelated proposal copies, historic draft binaries, MedFormerPanTS, loose
XML/ID files, unreviewed assets and unrelated scripts, as recorded in the initial scope.
All excluded material remains untouched.

## Follow-through

1. Obtain agreement on local commit and whether to push this exact scope to the public origin.
2. Check HEAD/index and compare the live tree with pinned bytes; review any new differences.
3. Stage exact reviewed content only, inspect staged diff/file types, then commit.
4. If push is authorized, check remote branch state, push without force and verify the
   remote commit. If it moved, stop for reconciliation rather than overwriting it.
5. Record actual commit/push identities and remaining unstaged work. Do not claim an
   independent data/evidence backup merely because code/docs reached GitHub.

Next work is specified in
[PURPOSE-DISPOSITION-IMPLEMENTATION](../data/PURPOSE-DISPOSITION-IMPLEMENTATION-2026-09-28.md).
Quinton will send the publisher email himself in a couple of days. No email was sent and
no reminder was scheduled. The imaging smoke remains gated on R0–R8; Claude's retrieval
work is independent of that first imaging smoke.
