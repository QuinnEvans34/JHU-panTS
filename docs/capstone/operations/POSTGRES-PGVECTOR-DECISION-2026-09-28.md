# D-260: PostgreSQL + pgvector for the evidence layer

Quinton approved PostgreSQL + pgvector in conversation on September 28, 2026, then
accepted the planning handoff: literature only, files authoritative. Architecture approved;
deployment, detailed schema and implementation remain to be reviewed.

## Scope and authority

Plan 07 stores/query-serves source revisions, rights/provenance, passages, corpus membership,
embedding configurations/vectors and validated build publication state in PostgreSQL.
pgvector supplies vector search inside that database. Canonical versioned literature
artifacts remain the rebuild authority; database-only undocumented corpus edits are forbidden.
Keep imaging manifests/cohorts, scans/masks, checkpoints and review-event contracts file-first.
No imaging mirror, global database authority, cloud service or second vector engine is approved.
Tier 1 remains the focused graded corpus; broader Tier 2 requires separate scope approval.

This supersedes D-082/D-202's earlier vector-engine selection direction for Plan 07 and
the SQLite/LanceDB recommendation in PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md.
D-401's rejection of mandatory project-wide Postgres/Neon remains intact: this is a new,
narrow evidence-layer decision, not restoration of the old architecture. Older proposals,
appendices and historical decisions must not be overwritten.

## Claude planning requirements / Codex review checklist

- Define canonical rebuild inputs, IDs and hashes, passage/source lineage, rights fields,
  corpus membership, encoder/tokenizer versions and embedding preservation/regeneration.
- Map each invariant to schema validation, SQL constraint, transaction, query rule or test.
  Include valid parents, required fields, logical uniqueness, dimensions and embedding-space
  compatibility; equal dimensions do not establish compatible encoders.
- Specify resumable staging, validation and atomic publication. Never expose partial builds.
- Plan PostgreSQL lexical baseline, dense retrieval, measured hybrid fusion and optional
  evaluated reranking. Do not call native PostgreSQL full-text ranking BM25 by assumption.
- Apply eligibility/corpus/model restrictions to every retrieval branch; evaluate restrictive
  filters against exact-search references and judge relevance separately from vector recall.
- Evaluate citations, support/groundedness, insufficient-evidence behavior, latency/memory,
  not just fluent responses. Retrieval engine choice does not select an embedding or LLM.
- Rebuild verification compares identities/hashes/counts/relationships exactly and search
  behavior using declared acceptance criteria; approximate index rebuilds need not be bit-identical.
- Include interrupted-ingestion, duplicate rejection, citation resolution and restore tests.
- Decide service versions, credentials, migrations, storage placement and safe shutdown.
  No live database on removable media without an explicit storage/risk decision.
- A representative prototype precedes full indexing. No claim that this architecture is
  benchmark-proven or that SQLite is fragile; benefits are relational integrity and one
  transaction boundary for metadata/vectors.

Claude owns the previously allowlisted new retrieval planning files; Codex reviews and
reconciles shared plans/decisions. Do not expand ownership silently. Current Plan 07/master
documents need coordinated reconciliation after Claude's handback; this amendment governs
the changed engine choice meanwhile. No services installed or corpus/model downloads started.
