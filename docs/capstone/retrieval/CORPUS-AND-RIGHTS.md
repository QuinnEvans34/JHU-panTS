# Corpus, acquisition, identity, and rights

September 28: D-261/D-264 approve the intended baseline/update and PMC Cloud routes.
The approved [acquisition plan](planning/ACQUISITION-PLAN.md) keeps S/A/B unsigned.
[Selection](planning/SEARCH-AND-SELECTION.md) is local and versioned; its provisional
settings are recorded in D-265. No corpus download is authorized by this document.

> Route verification, September 28, 2026: the legacy PMC OA Web Service and legacy FTP/
> Cloud article packages have been retired. Plan current PMC retrieval through anonymous
> HTTPS/S3 objects from pmc-oa-opendata, with per-article/version JSON rights and frozen
> content hashes. Article version alone is not immutable content identity. This does not
> retire PubMed baseline distribution or authorize a corpus download. See the official
> [PMC Cloud documentation](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/) and
> [Codex's D1–D8 response](../operations/PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md).

**Status:** Approved Plan 07 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P07-02 and P07-04 through P07-09  
**Governing plan:** [`../implementation/07-literature-retrieval.md`](../implementation/07-literature-retrieval.md)

## Purpose

This contract ensures every retrieved passage comes from an in-scope, reproducible, rights-reviewed
source. The index is disposable; source/document/passage records are authoritative.

## Initial topic boundary

Include literature addressing general:

- CT appearance and delineation of the pancreas and pancreatic lesions;
- pancreas/lesion contouring, measurement, localization, and review considerations;
- imaging factors that affect visibility or annotation difficulty;
- AI-assisted pancreas/lesion detection/segmentation performance, limitations, false alarms,
  uncertainty, and human review; and
- annotation-assist/review workflow where relevant.

Exclude as primary corpus targets:

- treatment, surgery, chemotherapy, radiation, or patient-management guidance;
- prognosis/survival/genomics/pathology unless directly necessary to explain an in-scope imaging
  question and safe to include;
- non-pancreatic disease with no workflow relevance;
- animal/preclinical-only work unless explicitly needed and separately labeled;
- editorials/news without evidence needed by the question set;
- non-retrievable records lacking sufficient permitted text; and
- retracted evidence from answer support under the selected notice policy.

The exact search strings and inclusion decisions are versioned, not embedded in code.

## Approved source channels

### PubMed

- Primary route: NLM 2026 baseline plus ordered updates to a pinned cutoff and matching MeSH.
- Retain raw file checksums and ordered source-file/ordinal add/replace/delete events. A revision
  uses canonical record-content identity, not bibliographic version alone. Repeated content keeps
  its revision ID but every event is retained. Reject gaps/order violations; replay deterministically.
- Sizing-only samples create neither a snapshot nor production event state; selection refuses them.
- Apply PROWL's own versioned two-stage selection; missing MeSH never silently excludes records.
- E-utilities remain for bounded search/record checks. The following API rules apply to those calls:
- Record exact query, NCBI translation, database, dates, history/query identifiers where used,
  retrieval time, page/batch, response hash, tool, and contact configuration.
- Follow the current no-key/key rate and large-job guidance at execution time.
- Batch with history/EFetch rather than one request per PMID.
- Cache immutable responses under source-snapshot identity.

PubMed metadata may be retained for citation. Abstract availability and copyright are recorded; an
abstract is not assumed redistributable simply because EFetch returns it.

### PMC

- Confirm membership in the PMC Open Access Subset or another explicitly permitted dataset route.
- Fetch selected permitted XML through PMC Cloud pmc-oa-opendata under signed run B; retain per-article JSON rights and exact object-byte hashes. Do not use retired legacy routes.
- Prefer structured XML for stable sections/paragraphs and exclude figures/supplementary media unless
  specifically rights-reviewed.
- Capture the article's exact license statement/identifier and retrieval route.
- Never crawl article HTML pages for bulk corpus acquisition.

## Credential and request behavior

- NCBI API key is optional unless the planned rate requires it; it remains in environment/secret
  storage and never appears in URL logs, manifests, Git, or error text.
- Registered `tool` and contact email values are configuration/secrets as appropriate.
- One local rate limiter governs all E-utilities calls from the workflow.
- Retry only transient network/rate/server failures with bounded backoff and respect server guidance.
- Invalid query, permission, license, or parser errors fail closed without repeated requests.
- Resume uses cached response/hash and the Plan 04 artifact identity.

## Canonical work and representations

One bibliographic work may have:

- PMID record/version;
- PMCID full-text representation/version;
- DOI/publisher identity;
- abstract representation;
- full-text XML representation;
- correction, erratum, expression-of-concern, or retraction notice; and
- revised metadata/text snapshot.

Canonicalization links these representations; it does not merge text bytes. Matching priority uses
validated PMID/PMCID/DOI relationships, then normalized bibliographic evidence/content hashes with
manual review for ambiguity.

## Rights record

Each text representation records:

- work/document/source-snapshot IDs;
- acquisition service/endpoint/evidence URI;
- visibility/access category;
- exact license identifier/text/evidence locator when available;
- copyright/rights holder statement where available;
- permitted `metadata_only`, `local_text_store`, `local_embedding`, `display_snippet`,
  `release_text`, and `redistribute` booleans/statuses;
- attribution/citation requirements;
- commercial/noncommercial/share-alike/no-derivatives flags where relevant;
- reviewer/date/policy version;
- `allowed`, `restricted_local`, `metadata_only`, `quarantined`, or `excluded` decision; and
- reason/evidence.

Unknown or conflicting rights default to `metadata_only` or quarantine, not permission.

## Git and release policy

- Search protocols, source IDs, citations, manifests, hashes, counts, and rights decisions may be
  committed.
- Restricted/large abstracts/full text, embeddings, and indexes stay under configured local artifact
  roots and are ignored by Git.
- Small synthetic or rights-cleared test snippets may be committed only with provenance/license noted.
- Release packaging rechecks `release_text`/`display_snippet` rather than assuming local indexing
  grants redistribution.
- The UI may show citation metadata/link even when full passage text cannot be released; local demo
  display follows the rights record.

## Source and document states

| State | Meaning | May become passage? |
|---|---|:---:|
| `discovered` | Search returned bibliographic identity | No |
| `retrieved` | Exact metadata response/document bytes stored | No |
| `identity_resolved` | Canonical work/representation established | No |
| `rights_allowed` | Intended local text/index/display use is supported | Yes |
| `restricted_local` | Local retrieval permitted but release/display constrained | Yes, with filters |
| `metadata_only` | Citation record retained; text not indexed | No |
| `quarantined` | Ambiguous identity/rights/content/notice | No |
| `excluded` | Out of scope or prohibited | No |

## Text normalization

Normalization may:

- decode XML entities/Unicode consistently;
- remove navigation/formatting artifacts;
- retain title, abstract sections, body section hierarchy, paragraph order, captions only if allowed,
  and source notices;
- normalize whitespace deterministically; and
- identify sentence boundaries with a pinned version.

It may not paraphrase, summarize, silently translate, remove negation, merge conflicting sections, or
strip evidence needed to locate the source span.

## Passage construction

Each passage stores:

- passage and document/corpus IDs;
- section path/title and paragraph/sentence range;
- original normalized character offsets and content hash;
- text or rights-controlled local artifact reference;
- title/section prefix fields used for embedding/retrieval;
- token/sentence counts and chunking version;
- overlap-parent/neighbor IDs;
- source citation metadata and rights/display status; and
- correction/retraction/notice flags.

Build passages on section/sentence boundaries near a configured target size. Overlap is bounded and
explicit. A passage cannot cross from abstract into unrelated full-text section or span two works.

## Corpus identity and reconciliation

The corpus manifest includes:

- search protocol/source snapshot IDs and cutoff;
- included/excluded/quarantined work/representation counts by reason;
- rights categories and license counts;
- document/passage ordered inventory and content hashes;
- normalization/chunking versions;
- correction/retraction policy;
- content language/source-type/topic counts;
- build environment/code/config; and
- completion/reconciliation report.

Same inputs/config must reproduce stable source/document/passage identities and counts. Changed
search result, document bytes, rights decision, normalization, or chunking creates a new corpus.

## Existing PubMed sample

Before use, inventory and hash `pubmed_samples.xml`, record how/when it was created if discoverable,
and compare its PMIDs/topic coverage with the approved search protocol. It may become:

- a local exploratory parser fixture;
- a source of IDs to refetch through the approved acquisition pipeline; or
- excluded historical material.

Its embedded text does not become an approved corpus merely by being parsable.

## Required tests

- current rate limiter/batching behavior and redacted credentials;
- transient retry and cached resume without duplicate source records;
- unsupported acquisition route rejection;
- PMID/PMCID/DOI duplicate linking and ambiguous-case quarantine;
- correction/retraction/notice preservation;
- missing/conflicting license fails closed;
- rights booleans block index/display/release correctly;
- normalization preserves negation and source locator;
- same build produces stable passage identities/counts;
- changed text/chunking creates new corpus IDs;
- restricted text absent from Git/release fixture; and
- corpus reconciliation sums included/excluded/quarantined records exactly.
