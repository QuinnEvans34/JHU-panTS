# Claude packet: Plan 07 synthetic retrieval foundation

SUPERSEDED, retained as history. Do not dispatch the SQLite packet below.
Use [CLAUDE-PLAN07-P3-PACKET-2026-09-28.md](CLAUDE-PLAN07-P3-PACKET-2026-09-28.md),
issued after approved planning revision 4. Issuance is not Quinton dispatch.

> September 28 status correction: Quinton reports Claude has not written implementation
> files and wants scope/phases reviewed first. This implementation packet is ON HOLD until
> renewed authorization after planning approval. Read PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md
> in this directory for the planning-only allowlist and D1–D8 response. The original packet
> below remains the later implementation boundary, not current permission to start coding.

Owner: Quinton Evans. Implementation: Claude after Quinton hands over this packet.
Integration/review: Codex. Prepared September 28, 2026.

## Authority and stopping point

Quinton requested this packet to start an independent Plan 07 lane. This authorizes the
bounded synthetic foundation below when he dispatches it, not the entire Plan 07 system.
Design approval is not production readiness. Do not close G6, D-202 (vector selection),
D-209 (question-set freeze), or Plan 10 provider/privacy decisions.

Deliver a deterministic synthetic document-to-ranked-passages pipeline with independent
metric tests. Then stop for Codex review. No generated answers, real corpus, imaging
integration, provider calls, vector installation, or autonomous follow-on work.

## Workspace and baseline

Canonical checkout: `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
Never recreate the old Neuro-data path, create another GitHub folder, clone, switch branches,
or create a worktree. Stop if the confirmed checkout cannot be reached.

Before writing, run from that checkout:

```sh
pwd
git rev-parse --show-toplevel
python3 scripts/diagnostics/check_workspace.py
git status --short
git rev-parse HEAD
```

Preparation HEAD: `f4d7109b466fc12854be4a86c9893750399a0672`.
The working tree contains substantial intentional uncommitted work; HEAD alone is NOT the
implementation baseline. September 28 native verification: 452 tests passed, two upstream
torch.jit deprecation warnings. Do not revert unrelated differences or freeze Codex's work.
Record the actual baseline when starting and report later concurrent changes separately.

Use the existing `.venv-prowl` on the Mac. No dependency/environment/lockfile changes.
If running in a separate execution environment, disclose it; do not claim native verification.
No drive access is needed or authorized by this packet.

## Required reading before code

1. `AGENTS.md`, `docs/capstone/operations/WORKSPACE-SAFETY.md`, and the current header of
   `docs/capstone/operations/TEAM-STATUS-2026-09-28.md`.
2. `docs/capstone/README.md` and `docs/capstone/implementation/07-literature-retrieval.md`.
3. All six design files in `docs/capstone/retrieval/`: README, CORPUS-AND-RIGHTS,
   QUERY-AND-RETRIEVAL, QUESTION-SET-AND-EVALUATION, GROUNDED-RESPONSE, TOOL-SELECTION.
4. `docs/capstone/contracts/identity-and-versioning.md`, `artifact-layout.md`, and
   `VALIDATION.md`; inspect existing schemas and synthetic-test conventions read-only.

Later dated/user-approved scope takes precedence over stale historical status paragraphs.
The old voxel-audit reservation is CLOSED: Codex owns that implementation now.
If a contract conflicts with this bounded implementation, document the conflict and stop
that portion rather than quietly changing the shared contract.

## Exclusive write allowlist

These three namespaces were absent when this packet was prepared. Recheck before writing;
unexpected existing work means coordinate, not overwrite.

- `src/retrieval/`: `__init__.py`, `records.py`, `passages.py`, `query.py`, `lexical.py`,
  `metrics.py` only. No import-time execution or global registration.
- `tests/retrieval/`: `test_records.py`, `test_passages.py`, `test_query.py`,
  `test_lexical.py`, `test_metrics.py`, `test_pipeline.py`; `fixtures/` may contain only
  small invented JSON/text fixtures and a provenance README. No conftest/global hooks.
- `docs/capstone/contracts/retrieval/`: new JSON Schema files for this packet's source,
  rights, document, passage, corpus, query, index and retrieval records, plus a README
  naming their provisional integration status. No changes to existing contract files.
- `docs/capstone/retrieval/FOUNDATION-DESIGN-2026-09-28.md`.
- `docs/capstone/retrieval/CLAUDE-FOUNDATION-HANDOFF-2026-09-28.md`.

This is a bounded list, not permission for a new framework. Ask before adding other paths.
Use pytest temporary directories for disposable indexes. Do not write outputs to the
external drive or create a persistent real corpus. Do not stage, commit, push, clean, move,
or delete user files. Preserve all existing files outside this list.

Codex owns `src/data/`, diagnostics, imaging readiness, existing shared schemas/tests,
AGENTS, team status, daily plan, and dependency configuration. Claude must not edit these.
Codex will not edit the reserved new retrieval files until handback or coordinated transfer.

## Build order and required behavior

### 1. Records and identity

- Implement explicit versioned records and JSON Schema validation using existing dependencies.
  Reject unexpected fields, malformed IDs/hashes, invalid enums and inconsistent references.
- Source/work identity and document representations must be distinct; no title-only automatic
  merge. Exact duplicate identities must not create duplicate retrieval entries. Conflicting
  identity/content fails with a specific error rather than last-write-wins.
- Rights permissions are explicit and fail closed. Metadata retention is not indexing,
  display or redistribution permission. Missing/unknown/conflicting permission must not
  silently become true. This packet consumes synthetic rights decisions; it does not
  implement automatic legal/license interpretation.
- Preserve correction/retraction and quarantine states. Excluded or retracted material
  cannot become answer-support retrieval results under this foundation policy.
- Define canonical hashing precisely. Same content/config produces the same content IDs;
  timestamps and elapsed time belong in execution metadata, not deterministic content IDs.
  Avoid circular IDs: documents/passages can predate the corpus manifest that inventories
  their hashes; describe how corpus membership is associated without self-hashing.
- Validate relationships as well as individual JSON shapes. Corpus/index disagreement and
  unresolved passage/document/source links must fail, not be silently repaired.

### 2. Synthetic normalized documents and passages

- Use invented, clearly synthetic text, never copied medical claims or real abstracts.
  Do not promote root `pubmed_samples.xml` into fixtures or an approved corpus.
- Accept a small explicit structured document input with section/paragraph boundaries.
  A live PubMed/PMC parser is outside this first packet.
- Preserve wording, negation and section boundaries. No paraphrasing or translation.
- Provide stable section/paragraph and half-open character-offset locators. State which
  normalized string offsets address, and retain an inspectable original-to-normalized
  representation/locator. Assert passage text equals its referenced normalized span.
- Specify deterministic sentence/paragraph chunking, target size, overlap, and oversized
  sentence behavior; no model downloads or unpinned tokenizers. Do not span works or
  unrelated sections. Changed text or chunking policy must change affected identities.
- Reconcile included/excluded/quarantined counts and ordered inventories without silently
  dropping documents. State the deliberately limited normalization/chunking implementation.

### 3. Bounded query contract

- Allowlist modality/anatomy/task, finding-state and permitted warning/coarse bins from
  the approved design. Do not include unresolved D-208 case-score bands.
- Reject unknown structured keys, IDs, paths, reports, image/mask payloads and ground truth.
- Preserve original validated question and negation; deterministic normalization is versioned.
  No LLM rewriting, live synonym lookup or fabricated MeSH provenance.
- Limit length/control characters and define conservative scope/refusal behavior for the
  synthetic demonstration. Test diagnosis/treatment and injection examples. Explicitly
  state that keyword rules do not certify semantic safety or anonymize arbitrary free text.
  No external provider or clinical safety claim may rely on this fixture-level gate.

### 4. Lexical control, not vector selection

- Implement the planned SQLite FTS5 lexical control using Python's existing sqlite3, if
  FTS5 is available. Check availability first; if missing, report a blocker for this part
  without installing anything or silently substituting a different tool.
- Use an explicit temporary index path and transactional build; never overwrite an existing
  index. Treat it as derived from corpus/config, not the authority for text.
- Parameterize SQL. Handle FTS query metacharacters deliberately so reviewer text does not
  become executable query syntax accidentally. Document tokenizer and score direction.
- Enforce corpus membership, rights, notices and topic/source filters; exclusions must not
  consume final top-k slots. Apply deterministic passage-ID tie breaks and an explicit
  source cap. Preserve distinct passage-level versus source-level results.
- Record exact query/corpus/index/retriever identities, raw scores, ranks, locators and
  reasons for filtered candidates without exposing disallowed passage text.
- Prove reopen/rebuild parity in ranked IDs and policy-defined scores, not necessarily
  byte-identical SQLite database files. Missing/corrupt indexes return evidence_unavailable;
  no eligible results return insufficient_evidence. Neither is a generated answer.
- Do not claim lexical matches prove that a passage supports a claim. Semantic grounding,
  dense/hybrid retrieval and answer generation remain deferred.

### 5. Pure retrieval metrics and integration

- Implement recall@k and reciprocal rank/MRR as pure functions with documented conventions.
  k must be a positive integer (not bool); invalid ranked IDs/duplicate passage IDs fail.
  Source-level ranks collapse repeated source IDs by first occurrence before scoring.
- Relevant IDs are sets; duplicate hits cannot inflate recall. An answerable question with
  zero gold support is invalid, not a perfect score. Unanswerable items stay outside
  answerable retrieval means and retain explicit counts; no NaN JSON or fabricated zero
  mean for an empty evaluation set. Report undefined values explicitly.
- Example independent oracle: gold {A,C}, ranking [B,C,A] yields recall@1=0,
  recall@2=1/2, recall@3=1, reciprocal rank=1/2. A second no-hit answerable query
  yields reciprocal rank=0, so their MRR=1/4.
- End-to-end synthetic test: documents -> rights decisions -> passages -> corpus/index ->
  validated query -> ranked references -> hand-checked metric report. Include refusal,
  unavailable and insufficient-evidence branches without presenting generated prose.
- Synthetic test questions are not the 60-question scientific evaluation set. Do not author,
  freeze or tune against a real held-out set in this packet.

## Acceptance evidence

Provide a checklist mapping each requirement above to exact tests, including:

1. Deterministic identities; changed text/rights/chunking changes relevant artifact identity.
2. Invalid fields and dangling/cross-corpus references rejected.
3. Missing rights, display denial, retraction and quarantine fail closed independently.
4. Exact text/offset round trip; Unicode, whitespace and negation preserved as documented.
5. Duplicate identity/conflicting content behavior and bounded source-cap behavior.
6. Known lexical ranking, score direction, ties, punctuation and SQL/FTS metacharacters.
7. Rebuild/reopen parity, empty result, missing/corrupt index and corpus mismatch.
8. Independently calculated metrics, duplicate-source handling and undefined denominators.
9. Input order permutation where order should not matter; no network/data-drive dependency.
10. No import-time writes, external requests, restricted text, secrets or absolute local paths
    embedded in portable records/source.

Use manually calculated oracles, not expected values computed by the implementation under
test. Document at least five deliberate, reverted fault injections and the tests that catch
them (for example bypass rights, reverse score ordering, break offsets, permit a duplicate
hit, omit corpus mismatch). Mutate only owned files and restore all faults before handoff.

Native commands from repo root:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/retrieval -q -p no:cacheprovider
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Do not require exact test totals while Codex is adding tests concurrently. Report counts,
warnings, platform/Python/SQLite versions and whether FTS5 exists. Attribute unrelated
failures without changing somebody else's code. If unable to run native commands, provide
exact alternate environment/results and explicitly leave native verification to Codex.

## Handback and stop

In FOUNDATION-DESIGN, describe public APIs/record shapes, identity/offset/rights/ranking
conventions, deliberate limitations and open integration decisions before implementation
grows. Keep it short enough for Quinton to understand the system.

In CLAUDE-FOUNDATION-HANDOFF record:

- every created file and SHA-256, start/end HEAD and touched-path inventory;
- requirement-to-test matrix, commands/results and fault-injection evidence;
- a small synthetic input/output example with independently calculated expected metrics;
- proposed shared-interface changes, NOT made;
- remaining limitations and next proposed packet, without executing it.

Do not mark Plan 07 done. Codex will review contracts, run native tests and review the
failure paths before integration. D-202's bounded vector spike, real corpus rights/search
approval, frozen relevance labels, provider boundaries and G6 remain separate decisions.
Notify Quinton that ownership is handed back; do not continue editing during Codex review.
