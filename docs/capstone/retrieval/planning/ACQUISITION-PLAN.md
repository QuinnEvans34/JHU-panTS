# Acquisition plan and run records

**Status:** PROPOSED, revision 4 (third Codex review, 2026-09-28). All run records (S, A, B) are **unsigned**.
No download is authorized.
**Route:** L-03, approved by Quinton in the Claude discussion on 2026-09-28. It is not part of
D-260. Reconciliation of the E-utilities-specific channel text is listed in SCOPE section 10.
**Rule:** every acquisition is a live network job under a run record Quinton has signed. Nothing
here records terms as accepted; Quinton accepts them at signing.

## Facts relied on (checked 2026-09-28)

- **PubMed 2026 baseline:**
  - released 2026-01-30 as `pubmed26n0001`-`pubmed26n1334` (XML, with MD5 files);
  - updates start at `pubmed26n1335`;
  - the baseline must be processed before any update;
  - updates carry new, revised and deleted citations;
  - DTD `pubmed_250101`.

  ([NLM bulletin](https://www.nlm.nih.gov/pubs/techbull/jf26/jf26_PubMed_2026_BaselineRelease.html);
  [Download PubMed Data](https://pubmed.ncbi.nlm.nih.gov/download/))
- **NLM conditions:** no signed licence; acknowledge NLM; do not imply endorsement; if
  redistributing, keep data current or disclose that it is not; no warranty. Abstracts may be
  publisher-copyrighted. ([NLM](https://www.nlm.nih.gov/databases/download.html))
- **PMC Cloud Service** (`pmc-oa-opendata`): anonymous access, per-article JSON metadata with
  licence, a daily inventory. Objects can change without a version change.
  ([NCBI Insights](https://ncbiinsights.ncbi.nlm.nih.gov/2026/02/12/pmc-article-dataset-distribution-services/);
  [PMC on AWS](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/))
- **Not guaranteed:** that this year's baseline files stay downloadable after the next annual
  baseline release, or that PMC bytes stay the same. Reacquisition is not a guaranteed recovery path
  (SCOPE 5.7).

## Prerequisites per run record (no run's prerequisites include itself)

**Before signing run S (sizing preflight):**
1. The storage alias `prowl_scratch` exists, and the volume-identity check is implemented.
2. A **sizing-only tool** passes tests on synthetic fixtures: a downloader subset (checksums, caps,
   no promotion) plus the **sizing-only parser mode** described below.
3. Quinton signs run S.

**Before signing run A (full baseline + updates + MeSH):**
1. Quinton confirms L-03 for recording, and Codex reconciles the channel text.
2. Plan 10 aliases exist: `literature_source` (read-only after promotion), `prowl_scratch` and
   `prowl_artifacts/literature/`.
3. The **full downloader and event-log parser packet** is approved, with tests passing on synthetic
   fixtures. Required tests:

   **Downloader:**
   - checksum verification (MD5 and SHA-256);
   - resume from partial;
   - no overwrite;
   - bounded concurrency;
   - volume identity before every promotion;
   - receipts;
   - interruption leaves only scratch partials.

   **Parser / event log:**
   - additions;
   - replacements;
   - deletions (`DeleteCitation`);
   - repeated events (identical and changed content);
   - delete-then-re-add;
   - interrupted update application;
   - deterministic replay;
   - malformed XML fails closed;
   - order violations and sequence gaps refused.
4. **Run S completed**, and its receipt reviewed.
5. The capacity check passes using S's measurements plus the projections and caps below.

**Before signing run B (PMC objects):**
1. The stage-1 bibliographic candidate set is frozen (`SEARCH-AND-SELECTION.md` section 5).
2. The capacity is rechecked.
3. Quinton signs run B.

## Sizing-only parser mode

- Parses **each sampled file independently**, whatever its position in the sequence.
- Records per-file:
  - compressed and decompressed sizes;
  - record and delete counts;
  - parsed-output size ratio;
  - parse time;
  - peak scratch use.
- **Builds no event log and no final state, and claims no valid snapshot.** Outputs are marked
  `sizing_only`. Selection code and promotion refuse them (enforced by a flag, with a test).
- Nonconsecutive samples are expected in this mode. The production parser's sequence-gap refusal
  is unchanged.

## Source revisions and the event log

- **Revision identity:** `revision_id` = SHA-256 of the canonicalized record XML (stable
  serialization of the `PubmedArticle` element). Bibliographic version fields are recorded but
  never assumed to identify an update uniquely.
- **Event provenance:** each record occurrence or deletion is an event (`source_file`, `ordinal`
  within the file, `event_type` in {`add_or_replace`, `delete`}, `pmid`, `revision_id` or null).
  - Final state = the last event per PMID in (file sequence, ordinal) order.
  - A delete removes the PMID from the final state, but its history is retained.
  - Identical repeated content keeps the same `revision_id`; the event is still logged.
- **Replay:** the final state is always computed from the ordered event log, never by in-place
  mutation, so an interrupted application can be replayed deterministically.

## Parsed PubMed store

- **Location:** `prowl_artifacts/literature/parsed/<parser-version>/<snapshot-id>/`.
- **Authority:** **derived**, regenerable from the raw files plus the parser version. It is never the
  canonical source, and it is never a vector index.
- **Format (proposed):** one compressed JSON Lines partition per source file (events plus parsed
  fields), a partition manifest with SHA-256 hashes, and a final-state index keyed by PMID.
  Chosen for inspectability and zero new dependencies; revisited only if measured parse or query
  time requires it.
- **Lifecycle:**
  - retained while its raw inputs and parser version are current;
  - a new parser version produces a new store alongside the old one;
  - old stores are deleted only on approval.
- **Tier 2:** turning any part of this store into embeddings requires X1 approval.

## Capacity model (measured where possible, capped where not)

The download is authorized on **measured samples plus explicit conservative projections and
caps**. It does not wait for P6/P8 artifacts that cannot exist yet. Capacity is **rechecked before
each phase** (P5, P6, P8) against actual usage, and a phase stops if its cap would be exceeded.

| Component | Basis | Proposed rule |
|---|---|---|
| Raw baseline + updates | **Measured**: publisher listing sizes (run S) | Exact bytes x 1.05 |
| Decompression / temporary peak | **Measured**: run S sample | Measured peak per file x 2 (two concurrent transfers) |
| Parsed store | **Projected** from run S's sample parse ratio | Ratio x total raw bytes x 1.5 |
| Retry / duplicate revisions | Projected | 10% of raw bytes |
| Tier 1 canonical artifacts (representations, passages, PMC bytes, embeddings) | Not yet measurable | **Cap:** 100 GiB reserved; P6/P8 stop if exceeded |
| Database + indexes + WAL, plus a second instance during scoped recovery | Measured in P4a on synthetic scale, projected | **Cap:** 100 GiB reserved |
| Operational headroom | Plan 10 policy | max(100 GiB, 10% of usable capacity) |

## Run record S: sizing preflight (UNSIGNED; tightly bounded)

| Field | Value |
|---|---|
| Purpose | Measure what run A's capacity check needs, and nothing more |
| Actions | Fetch the publisher directory listings (file names and sizes) for baseline and update files. Download **at most 3 baseline files and 2 update files** (proposed: first, middle and last baseline file; the two most recent updates) plus the MeSH 2026 descriptor file |
| Measurements | Listing totals; per-file download and decompression peak; per-file parse ratio and time from the **sizing-only parser mode** |
| Caps | Downloaded bytes at most 10 GiB. **Total scratch use** (downloads + decompressed data + sizing-parser outputs) at most 40 GiB. At most 2 hours wall-clock. 1 concurrent transfer |
| Ongoing checks | Before each file and every 60 s during transfer and parse: volume identity unchanged, and free space at least headroom floor + the remaining scratch cap. Otherwise stop |
| Destination | `prowl_scratch/literature/sizing-<run-id>/`. **Not promoted.** Samples may be reused in run A only if their checksums match |
| Integrity | Publisher MD5 plus local SHA-256 |
| Volume identity and capacity | Checked at start |
| Stop conditions | Any cap reached; checksum failure; volume change |
| Receipt | Listing hashes, sample file hashes, measurements, times |
| Authorization | Quinton signs. **Not signed** |

---

## Run record A: PubMed baseline, updates and MeSH (UNSIGNED)

| Field | Value |
|---|---|
| Purpose / tier | Canonical snapshot for Tier 1 selection. Serves Tier 2 only after X1 approval |
| Sources | Baseline `pubmed26n0001`-`n1334` + `.md5`; update files `n1335` to the cutoff; MeSH 2026 descriptor data (filename verified at signing); terms README |
| Cutoff | Proposed: the latest update file published on the signing date, recorded by name. Later updates are not applied to this snapshot |
| Transport | NLM's documented bulk distribution, over HTTPS where offered |
| Destination | Scratch `prowl_scratch/literature/<run-id>/`, promoted to `literature_source/pubmed/2026/{baseline,updatefiles,mesh}/` |
| Expected files / bytes | Measured from the listing at signing |
| Concurrency | At most 2 simultaneous transfers (proposed); follow any current NLM guidance |
| Per-file timeout | Proposed 30 min without progress, then abort that file and retry |
| Time cap | Proposed 72 h wall-clock per attempt; resumable. Overnight only with explicit approval |
| Capacity | The capacity model above passes, with a stop at the headroom floor |
| Volume identity | UUID/mount check at start and before every promotion. Mismatch stops the run |
| Integrity | Publisher MD5 plus local SHA-256 for every file; sequence reconciled (no gaps) |
| Retry | Transient errors: bounded exponential backoff (proposed at most 5 attempts per file). Checksum mismatch: one retry, then stop |
| No-overwrite | Promoted files are immutable. A same-name difference is a stop condition |
| Interruption | Only scratch partials exist; resume re-verifies them; nothing is half-promoted |
| Stop conditions | Checksum failure after retry; sequence gap; floor reached; volume change; unexpected file type; time cap |
| Receipt | Run ID, times, host, code hash, per-file name/bytes/MD5/SHA-256/time, cutoff, failures, reconciliation |
| Rights | NLM attribution recorded; no endorsement language; abstracts local and off-Git |
| Executed by / on | Claude or Codex, on Quinton's Mac |
| Authorization | Quinton: name, date, "terms reviewed". **Not signed** |

## Run record B: PMC objects for selected Tier 1 works (UNSIGNED; P6)

| Field | Value |
|---|---|
| Purpose | Resolve full-text availability and rights for bibliographic candidates, then retrieve permitted XML text |
| Selection input | Frozen stage-1 **bibliographic candidate set** (hash recorded): every candidate with a PMCID, **including those without an abstract** |
| Source | `pmc-oa-opendata`, anonymous HTTPS/S3: per-article JSON metadata first, then XML text objects for eligible works only |
| Rights gate | JSON licence (OAI-PMH as corroboration). Unknown or conflicting means no full text |
| Excluded | PDFs, media, supplements |
| Destination | Scratch, promoted to `literature_source/pmc/<snapshot-id>/` |
| Expected objects / bytes | Measured from selection plus inventory at signing |
| Concurrency | At most 4 simultaneous requests (proposed) |
| Per-object timeout | Proposed 5 min |
| Time cap | Proposed 24 h per attempt; resumable |
| Capacity | Checked against the measured expected bytes plus headroom |
| Volume identity | Checked at start and before promotion |
| Integrity / freeze | Per object: key, inventory date/ETag, SHA-256 of bytes, retrieval time, licence text/ID. PMCID + version is **not** a content hash |
| Retry | Transient errors: bounded backoff (at most 5 attempts). Persistent 404/missing: recorded as `missing`, not retried endlessly |
| No-overwrite | A re-fetch with different bytes becomes a **new** object version, never an overwrite; recorded as a change |
| Interruption | Only scratch partials; resume by manifest |
| Reconciliation | Requested / retrieved / eligible / missing / changed, by reason |
| Stop conditions | Error rate above 5% of requests (proposed); floor reached; volume change; time cap |
| Receipt | As run A, per object |
| Authorization | Quinton signs. **Not signed** |

## Not planned

- Full PMC mirroring.
- Downloading via article web pages.
- API keys in documents or logs.
- A full-PubMed vector index (that is X1 only).
