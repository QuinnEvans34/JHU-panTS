# Plan 07: Codex response to Claude's decision brief

Historical response. September 28 planning approval (D-261–D-265) supersedes D1's
E-utilities-first recommendation and D8's single scope/phases filename. The approved
files are SCOPE.md and PHASES.md. D-260 supersedes the earlier engine recommendation.
The [revised P3 packet](CLAUDE-PLAN07-P3-PACKET-2026-09-28.md) replaces the old
foundation implementation boundary; Quinton dispatch remains required.

September 28, 2026. Recommendations for Quinton's scope review, not approval of a new
bulk download, provider, database selection or expanded corpus. Read before drafting.

## Corrected status and context

Quinton reports that Claude has NOT implemented the synthetic packet or written files.
Earlier shared status saying implementation was underway was based on "Claude is working"
and was too specific. Current lane: planning only. Hold the implementation packet until
Quinton approves the scoped phases. Preserve its later code acceptance criteria.

The approved Plan 07 includes a real local dense/vector retrieval implementation and
comparison with a lexical baseline. D-082/083/084 and D-202 do not authorize quietly
dropping vector retrieval. SQLite FTS is the control/fallback, not completion of the vector
objective. Default remains a bounded LanceDB local evaluation; alternatives require the
documented evidence and Quinton's scope decision if they cannot meet the required database
demonstration. A vector store need not be a hosted service or a second operational server.

## D1 — Acquisition: retain A for the first focused corpus

E-utilities was selected for targeted PubMed selection, explicit query translations,
batching, immutable response capture and a manageable corpus linked to reviewer questions.
It was not selected because broad acquisition is forbidden or disk space is scarce.
Preserve exact query/version, search time, returned PMID list, fetched response bytes,
hashes and selection reasons. Search/history tokens alone are not durable snapshots.
Endpoint result limits, partitioning/deduplication, retries, update semantics and reproducible
counts belong in the acquisition design; never assume raising a page size retrieves everything.

B is technically reasonable for a separately approved local PubMed mirror. NLM confirms
the [2026 baseline](https://www.nlm.nih.gov/pubs/techbull/jf26/jf26_PubMed_2026_BaselineRelease.html)
contains 1,334 files and must be loaded before updates starting with 1335. It does not
eliminate governance or search implementation work: apply additions, replacements and
deletions in order; pin update cutoff, XML/MeSH versions, all input hashes and local filters.
PubMed citation data are not the full text of every paper. [NLM download guidance](https://support.nlm.nih.gov/knowledgebase/article/KA-03504/en-us)
describes new, revised and deleted citations in updates.

Local MeSH/keyword filtering is a new search policy, not reproduction of PubMed automatic
term mapping. Missing MeSH on recent/non-indexed records must not silently exclude them.
Even a baseline plus updates is a historical local snapshot, not necessarily byte-equivalent
to a contemporaneous PubMed search result. E-utilities results also drift on rerun; archived
responses/ID lists, not live reruns, define our reproducibility claim.

Recommendation: A now. Keep B/C as an optional later acquisition adapter with its own
justification and decision amendment. Acquisition breadth and index breadth are independent:
a bulk mirror could still feed only a focused vector corpus; API retrieval can also be broad.

## D2 — Index scope: A committed; C only as a gated extension

Keep the focused, frozen, rights-reviewed corpus for graded retrieval and reviewer UI.
Neither approximately 8.4k records nor 40–60k passages is a quota or a measured current count.
Information needs, seed coverage, search precision samples and rights determine the count.

Whole-PubMed evaluation is possible in principle. [TREC pooling](https://trec.nist.gov/data/reljudge_eng.html)
collects candidates from diverse retrievers for relevance judgments. We could use lexical,
dense and hybrid pools, blinded judging, coverage audits and a frozen qrels set. Recall against
known judgments is NOT exhaustive recall over all PubMed. Report that limitation, unjudged
coverage and pooling bias; do not treat unjudged as definitively irrelevant. Precision@k,
graded nDCG and bpref can supplement the required metrics under an approved protocol.
[NIST's pooling study](https://www.nist.gov/publications/bias-and-limits-pooling-large-collections)
explains why fixed pools can become incomplete/biased as collections grow. Even a focused
corpus requires honest relevance-judgment limitations; small is not automatically exhaustive.

More documents can add evidence but also distractors. Treatment/prognosis literature being
present does not itself force unsafe answers: explicit query scope, retrieval/display filters
and response refusal gates remain required at any size. Removing such papers alone is not
a safety proof. Broader coverage must be tested, not assumed to improve accuracy.

Scale affects more than disk: embedding time, memory, index rebuilds, evaluation labor,
version/update handling and competition with CT training. Illustration only: 40 million
768-dimensional float32 vectors are 122.88 GB before text, indexes, replicas or multiple
passages per article. This is not a measured resource estimate for our selected model.

Recommendation: do not make all PubMed the first graded corpus. C is acceptable as a proposed
extension only if Tier 1 has independent delivery and Tier 2 has separate approval/budget.
Start any Tier 2 with a bounded broader sample, not an automatic PubMed+PMC mirror.

## D3 — Personal research assistant / Tier 2

This is additional scope, even if it is ungraded, local and non-identifying. Record a decision
and a separate extension plan, not a second mandatory 10-week deliverable. Specify owner,
resource/time ceiling, acquisition rights, storage roots, intended users, uncertainty/citations,
and stop rules. Weeks 9–10 cannot be consumed by it.

It may reuse stable components, but needs independent corpus/index/query identities, configs
and evaluations, an explicit resolver that cannot silently union/fall back across tiers, and
no patient material or protected evaluation labels. Development agents must not access
held-out question answers through the research library. It is a research aid, not trusted
medical advice or a source of unverified engineering truth. "Not graded" does not waive
quality/privacy safeguards. Promotion of Tier 2 material to Tier 1 creates a reviewed new
corpus version and evaluation-compatibility decision before any retuning.

## D4 — PMC route correction: confirmed

Claude is right. The [OA Web Service retirement notice](https://pmc.ncbi.nlm.nih.gov/tools/oa-service/)
and [PMC Cloud documentation](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)
confirm the August transition. Use current anonymous HTTPS/S3 access to pmc-oa-opendata
for permitted article objects; no AWS account or paid cloud compute is inherently required.
Check per-article/version JSON rights; OAI-PMH can provide rights metadata too. The PMC
transition does NOT retire PubMed's separate annual baseline distribution.

Critical reproducibility detail: PMC objects may change without a new article-version prefix.
Freeze inventory/selection metadata, object hashes, retrieval times and actual allowed bytes;
do not treat PMCID plus version as an immutable content hash. Reconcile removals, missing
objects and lagging inventory. Do not download all PDFs/media/supplements by default.
Anonymous public access is not blanket permission for embedding, display or redistribution.

## D5 — Live acquisition governance

Agree that already-local processing needs no API probe. Bulk acquisition is still a live
network job. No all-database job is authorized by this brief. Reviewing public documentation
is not equivalent to authorizing corpus acquisition or experiments.

Before either targeted or bulk acquisition, create one approved acquisition/run record with:

- purpose, tier, search/release/cutoff and exact endpoint/allowed-file selection;
- root alias, verified volume/capacity, source versus scratch destination and concurrency;
- rights/terms review, required attribution, contact/tool registration when applicable;
- expected counts/bytes, time/space caps, retry/resume, stop conditions and no-overwrite rules;
- publisher checksums where supplied plus local SHA-256, corruption/missing-file handling;
- receipt, count reconciliation, immutable input retention and provenance outputs;
- relevant Plan 09/10 tests and explicit Quinton authorization for that bounded job.

NLM says [a signed download license is not required](https://www.nlm.nih.gov/databases/download.html),
but usage conditions remain. Do not invent a mandatory click-through or say terms were
accepted by Quinton merely because this plan was drafted. No API key is placed in docs.
Need only the relevant stage gates, not completion of every unrelated Plan 09/10 deliverable.

## D6 — Proposal and grading expectations

Direct read of proposal v3.8 AND v3.9 confirms the relational/vector storage pillar wording.
Direct read of appendix v3.1 confirms its explicit file-first boundary with relational
database/managed-vector-service implementation optional pending measured need. There is
a presentation/grading ambiguity; do not pretend either sentence does not exist.

Recommended demonstration: versioned authoritative artifacts plus a coherent retrieval data
model; relational source/document/passage/rights tables and integrity checks in the SQLite
lexical control if useful, alongside the actual selected vector store. Join using stable
IDs and show matching corpus identity, rights filters and measured retrieval. An ER diagram,
rebuild evidence and tests make this concrete. A table-shaped JSON file alone is not proof
of relational database implementation. SQLite FTS alone is not the vector implementation.

"Same data layer" can describe one PROWL repository/adapter boundary across local stores;
it need not mean all scans/reviews must be moved into PostgreSQL. This is an interpretation,
not a guarantee of the instructor's rubric. Ask a short clarification before relying on it
for grading: does SQLite relational metadata plus a local vector store under one logical
layer meet the pillar, or is a single physical relational+vector engine expected?

If a single engine is explicitly required, reassess pgvector or another suitable stack
through D-202/D-211; don't quietly reinstate superseded mandatory Postgres. No proposal or
appendix was revised or instructor contacted during this response.

## D7 — Embedding and generation models

Locked: pinned local embedding baseline, versioned vectors and no automatic external calls.
Not locked: embedding model, generator, Ollama, Qwen, model size or quantization. Old v2
draft names are historical candidates, not commitments. Plan 07's grounded-response design
leaves local versus external generation to the Plan 10 boundary review.

A bounded general-versus-biomedical embedding comparison is reasonable after the local
store spike and development labels exist. Keep corpus/chunking/query/scope fixed, report
rebuild/latency/resources and select on development only. [MedCPT's official repository](https://github.com/ncbi/MedCPT)
uses distinct query and article encoders: pin the matched pair and verify input conventions,
code/weight licenses and chunk suitability. Don't use one arbitrary encoder for both sides
or assume precomputed PubMed vectors match our corpus/chunk versions.

Local generation is a good candidate, not selected yet. Measure actual available Mac memory,
context/KV-cache load, throughput and contention with imaging—not model-file size alone.
Pin weights/tokenizer/runtime/quantization/prompt, define timeouts, and select by groundedness,
citation support, refusal and latency. Ranked evidence cards remain a valid fallback while
generation is gated; they do not remove the dense/vector deliverable.

## D8 — Planning ownership and sequencing

Agree to plan first. Claude may draft ONLY these new files now, checking each is absent:

- `docs/capstone/retrieval/planning/SCOPE-AND-PHASES.md`
- `docs/capstone/retrieval/planning/INFORMATION-NEEDS.md`
- `docs/capstone/retrieval/planning/SEARCH-AND-SELECTION.md`
- `docs/capstone/retrieval/planning/SEED-SET.md`
- `docs/capstone/retrieval/planning/ACQUISITION-PLAN.md`
- `docs/capstone/retrieval/planning/RUNNING-LOG.md`

The new planning directory is intentional. Do not create another project/root or overwrite
an unexpected existing file. Keep recommendations labeled proposed until Quinton approves;
the running log records work actually done and append-only corrections. Seed candidates
need verified citations; no copied unreviewed abstracts or fabricated relevance labels.

Codex owns changes to existing plans/decisions/shared contracts and this response. Claude
must propose amendments through the handoff, not rewrite D-074 or remove vector storage.
Earlier foundation source/test namespaces stay reserved but ON HOLD. New proposal changes,
dependency installs, downloads, model pulls and paid calls need their own authorization.

Suggested phase sequence:

1. Scope/requirements/risks and information needs; Quinton approves boundaries.
2. Draft search, seed and acquisition protocols (no corpus job); review rights/resource plan.
3. Authorize synthetic foundation packet; implement contracts, lexical control and metric tests.
4. Authorize bounded local vector-store spike and small rights-cleared acquisition pilot.
5. Freeze corpus, development/held-out questions and relevance protocol; compare retrievers.
6. Select and test generation/citation/refusal behavior; integrate approved outputs with UI.
7. Consider separate Tier 2 only if explicitly approved and core milestones remain protected.

These phases organize already approved work; they do not reset the 10-week plan or authorize
every subsequent phase now. Return drafts to Quinton/Codex before any foundation code.
