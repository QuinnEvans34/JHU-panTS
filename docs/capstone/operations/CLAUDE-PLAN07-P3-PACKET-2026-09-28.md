# Claude packet: revised Plan 07 Phase 3 synthetic foundation

Issued by Codex September 28, 2026 after Quinton confirmed planning-set approval.
Status: **ready for Quinton dispatch; not dispatched by issuance**.
Replaces the earlier SQLite foundation packet, which remains historical.
Owner/decider: Quinton. Implementer: Claude. Contract/integration reviewer: Codex.

## Objective and authority

Build a small, deterministic, pure-Python synthetic foundation: records, passages,
query gate, span-based labels and ranked/delivered-evidence metric demonstrations.
Finish with native tests, design notes and handback; stop for Codex contract review.
No search engine is implemented. Supplied fixture rankings are not retrieval results
from an implemented ranker and cannot demonstrate relevance quality or G6 readiness.

D-260–D-265 govern this packet. D-085 recall/MRR stays official. Additional span-hit and
delivered-evidence metrics are a **proposal**: implement/test them as labelled synthetic
prototypes, never silently adopt them as official model-selection/release criteria.
The provisional context budget is 2,000 tokens; no real tokenizer/model acquisition.

## Workspace and required reading

Use only `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
Before writes: `pwd`, `git rev-parse --show-toplevel`,
`python3 scripts/diagnostics/check_workspace.py`, `git status --short`, `git rev-parse HEAD`.
Never recreate old paths, clone, switch branches or create a worktree. Preserve existing work.
The retrieval source/test/schema directories were absent at issuance; recheck before creation.
Unexpected files require coordination, not overwrite. Use existing `.venv-prowl` only.
Prior native baseline: 587 passes, two upstream warnings; remeasure at start rather than
assuming a count while Codex is working. No dependency, environment or lockfile edits.

Read AGENTS, WORKSPACE-SAFETY, CURRENT-CHECKPOINT; D-260–D-265; the seven approved
`retrieval/planning/` files (especially SCOPE 5/10/12 and PHASES P3/P7); the updated Plan 07
and six retrieval design files; shared identity/versioning, artifact layout and validation
contracts. P1 needs and P2 seeds are not frozen by this packet. Do not read real held-out data.

## Exclusive write allowlist

- `src/retrieval/`: `__init__.py`, `records.py`, `passages.py`, `query.py`, `labels.py`,
  `metrics.py`, `context.py` only. No lexical.py, database driver or global hooks.
- `tests/retrieval/`: `test_records.py`, `test_passages.py`, `test_query.py`,
  `test_labels.py`, `test_metrics.py`, `test_context.py`, `test_pipeline.py`;
  `fixtures/` contains only small invented JSON/text and provenance README. No conftest.
- `docs/capstone/contracts/retrieval/`: new JSON Schemas plus README for source/work,
  revision/event, rights, representation, passage, corpus membership, query, supplied
  ranking, span label and metric/context results. Document provisional integration status.
- `docs/capstone/retrieval/FOUNDATION-DESIGN-2026-09-28.md`.
- `docs/capstone/retrieval/CLAUDE-FOUNDATION-HANDOFF-2026-09-28.md`.
- Append-only P3 progress/handback entries in `docs/capstone/retrieval/planning/RUNNING-LOG.md`.

New implementation namespaces are intentional. Keep fixtures small and use pytest temporary
directories. Request a scoped extension before adding other paths. Codex owns data, shared
schemas/plans/decisions, registry, dependencies and checkpoint. Do not edit those. Codex will
not edit these reserved implementation paths until handback/transfer. No staging/commit/push.

## Required behavior

### Records, evidence and identities

Use explicit schema versions and existing JSON Schema dependencies. Reject unknown fields,
invalid IDs/hashes/enums, duplicate logical records, conflicting content and unresolved
relationships. Separate work, revision, source event and representation. Repeated identical
revision content may recur through distinct source events; do not confuse that with duplicate
passage/corpus entries. Canonicalize/hash deterministically, excluding timestamps/paths from
scientific identity; specify float/nonfinite rejection and avoid circular IDs. Changed text,
rights or chunking must invalidate the appropriate artifact identity. No production XML parser.

Synthetic rights records distinguish retention, embedding/indexing, display and redistribution.
Unknown/missing permissions fail closed; retraction/quarantine cannot become answer support.
Verify source/revision/representation/passage/corpus links and content hashes, not schema shape
alone. No legal interpretation engine or real corpus promotion.

### Passages and labels

Accept explicit synthetic sections/paragraphs, preserve wording/negation, and define the exact
normalization plus original-to-normalized locator mapping. Offsets are half-open Unicode code
points into immutable normalized representation text. Passage text must equal the referenced
slice. State deterministic sentence/paragraph chunking, overlap and oversized-unit handling;
never cross works/unrelated sections. No hidden tokenizer download or paraphrasing.

Labels identify representation ID/hash, start/end, grade and required-concept IDs. Validate
bounds and referenced concepts; normalization changes invalidate old labels. Direct support
requires complete containment of a direct span. Partial overlap is not direct; uncertain labels
do not enter primary binary gold sets. Overlapping chunks may contain the same gold span, but
span-hit recall counts that span once. Real labels require Quinton's authoring/adjudication;
synthetic schema checks do not prove semantic support or minimality.

### Query gate

Allowlist non-identifying modality/anatomy/task, finding-state and approved coarse bins/warnings.
Reject unknown keys, identifiers, paths, source reports, image/mask payloads and ground truth.
Do not use unresolved D-208 score bands. Preserve original validated question/negation and
version deterministic normalization. Bound length/control characters; test out-of-scope and
injection fixtures. Keyword rules are a fixture-level scope demonstration, not proof of semantic
safety or anonymization of arbitrary free text. No external requests or generated answers.

### Ranked metrics

Accept validated supplied rankings with corpus/query/config identities and explicit score
direction/tie policy. P7's target depth is 50; permit fewer when the eligible pool is smaller,
with result count/reason. Reject duplicate passage IDs, unknown links and cross-corpus results.
Compute official source and passage recall@1/3/5/10 and RR/MRR. Source ranks collapse by first
work occurrence, then renumber. Passage relevance is configuration-specific; do not compare
its changing denominators as if fixed across chunking. k must be positive integer, not bool.
Gold sets cannot inflate from duplicates. Answerable/zero-gold is invalid; refusal items stay
outside answerable means. Empty means are explicitly undefined, never NaN JSON or fake zero.

Independently calculated oracle: gold {A,C}, ranking [B,C,A] gives recall@1=0, @2=1/2,
@3=1 and RR=1/2. A second no-hit answerable query gives MRR=1/4.
Additional proposed span-hit recall counts distinct direct spans fully contained in top-k.
Report denominators, configuration and proposal status separately from official metrics.

### Delivered-evidence prototype

Implement whole-passage packing in ranking order: add if it fits, otherwise skip and continue.
Never truncate silently. Inject a named/versioned deterministic synthetic token counter or
explicit validated fixture counts; label this as synthetic counting, not a production model
tokenizer. No tokenizer library/model install. Record counting identity and budget in results.
Production use later needs an actual pinned reference/generator tokenizer and re-reporting.

Score proposed delivered-span recall and concept coverage from passages actually packed,
with full span containment, not the initial retrieved list. Report token total, selected and
skipped IDs, reasons and unique concept/span denominators. Positive-integer budget/count
validation rejects bool/negative/nonfinite values; define empty-text/zero-count behavior.
Oracle: ranking A/B/C with token counts 8/7/2 and budget 10 delivers A/C, skips B; direct
spans only in B are not delivered. Overlap must not double-count concepts or gold spans.

## Acceptance and handback

Provide manual goldens, adversarial cases and an end-to-end synthetic chain:
documents -> rights -> passages -> corpus -> validated query -> supplied ranking -> labels ->
ranked and delivered metrics. Include refusal, unavailable and insufficient-evidence outcomes
as explicit fixture states, not claims of a working retriever/response service.

Test Unicode/whitespace offsets; changed representation hashes; missing/dangling references;
rights/display independence; source dedup/renumbering; span partial/full containment;
packing skipped-large-then-fitting-small passages; empty denominators; input permutation where
order is irrelevant; no input mutation; deterministic rebuild and no network/drive dependency.
Perform at least five deliberate reverted faults in owned files and name the catching tests
(rights bypass, broken offset, stale hash, duplicate span credit, skipped passage credit, etc.).

Run from the native checkout:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/retrieval -q -p no:cacheprovider
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Report actual counts/warnings/environment, tests-to-requirements map, exact changed files,
hashes, limitations and remaining gates. Do not change unrelated tests to make totals pass.
No SQLite/FTS5, PostgreSQL service, SQL migrations, embeddings, real abstracts, publisher
downloads, raw pubmed_samples.xml reuse, imaging data, real held-out labels or Plan 04 runner.
Stop after handback. P4b cannot start until Codex contract review and separate dependency approval.
