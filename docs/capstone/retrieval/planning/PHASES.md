# Plan 07 lane phases: how we build the evidence system

**Status:** Planning set v4, **approved by Quinton on 2026-09-28**. Each phase still starts only
when its entry criteria and authorizations are met. This document authorizes
nothing. Each phase starts only when its entry criteria and listed authorizations are met.
**Owner / decider:** Quinton Evans. **Implementer:** Claude. **Reviewer:** Codex.
**Scope and decisions:** [`SCOPE.md`](SCOPE.md) (L-xx and section references).

**Phase count:** 13 phases, **P0 to P12**, plus the gated extension **X1**. P4 has two parts, P4a
and P4b.

## Principles

1. **Problems on paper first.** Written entry and exit criteria, and a handback, for every phase.
2. **Evidence, not claims.** Exit criteria are tests, hashes, counts or measured numbers.
3. **Synthetic before real.** Behaviour is proven on invented fixtures and disposable instances
   first.
4. **Nothing irreversible without a record.** Downloads, installs, model pulls and shared-setting
   changes each need approval.
5. **Tune on development only.** The held-out set is used once, on a frozen complete configuration.
6. **Log as we go.** Every session appends to `RUNNING-LOG.md`; Notion gets a matching entry.
7. **Honest estimates.** Effort figures are rough and revised after each phase.

## Dependency map

```text
P0 Scope approval
 ├─ P1 Information needs ── P2 Protocols (selection v0, seed protocol, run records)
 │                                 │
 ├─ P3 Synthetic foundation ──────┐│
 │        (contracts reviewed)    ││
 ├─ P4a Platform infrastructure ──┤│   (independent of P3)
 │                                v│
 │                   P4b Contract-bound database work (needs P3 contracts reviewed + P4a)
 │                                 │
 │   P5 Acquisition (needs P2 run record A signed) ── P6 Selection + Tier 1 corpus v1
 │                                                       │   (needs P3, P5; seeds frozen)
 │                                                       v
 │                                          P7 Evaluation set frozen (needs P1, P6)
 │                                                       v
 │                                  P8 Embeddings + published build (needs P4b, P6, P7)  [Week 5]
 │                                                       v
 │                                  P9 Retrieval development selection (dev only)      [Week 6]
 │                                                       v
 │                                  P10 Response development (dev only)
 │                                                       v
 │                                  P11 Freeze complete config + held-out evaluation   [Week 8]
 │                                                       v
 │                                  P12 Integration + G6                               [by Week 8]
 └─ X1 Tier 2 extension (separately approved; never Weeks 9-10)
```

## Calendar alignment (proposal v3.8)

| Window | Phases | Proposal checkpoint |
|---|---|---|
| Now to Oct 4 | P0-P2; P3; P4a if install is authorized; P5 started if run record A is signed | Front-loaded capacity |
| Weeks 1-4 | P4b; P5 finish; P6; P7 (Quinton's authoring and labelling); P8 begins | Week 1 retrieval requirements satisfied by P0-P2 |
| Week 5 | P8 complete | Queryable retrieval prototype |
| Week 6 | P9 | Retrieval metrics (development) |
| Week 7 | P10; P12 UI integration begins with development outputs | Integrated review flow |
| Week 8 | P11 held-out evaluation (once); P12 complete; G6 | Locked metrics, end-to-end demo |
| Weeks 9-10 | Defects and packaging only | Protected; no Tier 2 |

---

## P0: Scope and phase approval

- **Entry:** Codex review of v1. D-260 recorded.
- **Work:** Revise to v2. Quinton reviews PROPOSED items. Quinton confirms L-03, L-08 and L-09 so
  Codex can record them.
- **Exit:**
  - Every PROPOSED item needed by P1-P4 is approved or revised.
  - Codex acknowledges SCOPE section 10.
  - The revised foundation packet is issued (L-15).

## P1: Information needs

- **Entry:** P0 approved for P1.
- **Work:** Quinton edits Claude's drafted needs (kept, edited or added). Refusal families and
  boundary wording are finalized.
- **Rule:** needs are frozen **before inspecting this selection run's results**. Prior literature
  exposure (the proposal, appendix, earlier project and today's research) is disclosed in the file,
  not denied.
- **Exit:** Quinton approves. Every family has needs. Provenance is recorded.

## P2: Protocols on paper

- **Entry:** P1 approved.
- **Work:**
  - `SEARCH-AND-SELECTION.md` v0 with every rule executable (no undefined terms, numeric caps,
    disposition precedence, date/language handling, sampling protocol).
  - `SEED-SET.md` protocol plus **assisted candidate discovery**: Claude proposes candidates from
    independent references, Quinton reviews.
  - `ACQUISITION-PLAN.md` run records S (bounded sizing preflight), A and B, with complete
    safety envelopes.
- **Exit:**
  - Quinton approves selection v0 and the seed candidate list.
  - Run record S is ready for signature. Run record A becomes signable after S's measurements.
  - Codex has recorded the storage aliases and the L-03 channel reconciliation.
- **Note:** seeds are **frozen later**, after their identifiers are verified against the local
  baseline in P5 and before the first selection run in P6.

## P3: Synthetic foundation (pure Python)

- **Entry:** Revised packet dispatched. Allowlisted paths re-checked.
- **Work:**
  - schemas and validators with relationship checks;
  - canonical hashing;
  - fail-closed rights;
  - passages with half-open offsets and an original-to-normalized mapping;
  - deterministic chunking;
  - query gate;
  - span-based relevance data structures;
  - pure metrics, including span-hit recall.
- **Exit:**
  - Packet acceptance evidence is met.
  - At least five reverted fault injections, each caught.
  - Codex native re-run and **contract review**. P4b depends on this.
- **Oracle example:** gold {A,C} with ranking [B,C,A] gives recall@1=0, @2=1/2, @3=1, RR=1/2.
  Adding a no-hit query gives MRR=1/4.

## P4a: Platform infrastructure (independent of P3)

- **Entry:**
  - Install authorization (runtime, pinned PostgreSQL image, pgvector).
  - Docker inventory completed before any shared-setting proposal (SCOPE 5.5).
  - Hardware recorded: **64 GiB physical RAM** (verified by Codex, 2026-09-28). The SCOPE 5.5
    coexistence limits remain PROPOSED until P4a measures them.
- **Work (disposable synthetic instances only; production sources untouched):**
  1. Runtime and image pinned by digest; record the stop signal and set the grace period.
  2. Compare storage layouts (B and C first; A only if approved): throughput, random-read latency,
     permissions, internal-SSD footprint.
  3. Start/stop procedure rehearsal. Process-crash drill (container kill). Scoped recovery rehearsal
     (preserve, verify, rebuild into a new instance).
  4. Backup/restore drill (`pg_dump`/restore) on the synthetic instance.
  5. Vector baseline on a generic synthetic table: **exact search plus one representative
     approximate configuration** (HNSW at pgvector defaults), including filtered queries and
     iterative scans.
  6. Synthetic, bounded coexistence test against the SCOPE 5.5 limits.
- **Expansion rule:** further index types or precision settings (IVFFlat, `halfvec`, tuned HNSW)
  are tested only if a defined measurement triggers them. Triggers: exact-search p95 above the
  latency limit at projected Tier 1 scale; recall of the approximate configuration at k=10 below
  0.95 versus exact; or memory above the cap.
- **Not claimed:** durability under USB disconnection or power loss. The drive is never unplugged as
  a test.
- **Exit:**
  - A pinned platform record.
  - Measured numbers against the limits.
  - Drill logs.
  - Quinton approves the layout.
  - A proposal for the rewritten `TOOL-SELECTION`.
- **Stop rule:** limits cannot be met, or a layout fails the crash/recovery rehearsal. Stop and
  return options.

## P4b: Contract-bound database work

- **Entry:** P3 contracts reviewed by Codex; P4a exit; psycopg 3 dependency authorized.
- **Work:**
  - migrations for the SCOPE 5.3 model;
  - least-privilege retrieval role and published view;
  - staging, validation (content hashes and embedding checksums), publication;
  - interrupted-ingestion resume;
  - duplicate rejection;
  - cross-configuration query rejection;
  - rights filters applied identically across branches;
  - lexical `ts_rank_cd` with safe query parsing;
  - hybrid reciprocal rank fusion (RRF) as the default rule;
  - rebuild from synthetic canonical artifacts with exact and tolerance checks.
- **Exit:** Every SCOPE 5.4 invariant has a passing test. Codex review.

## P5: Acquisition (live network; background)

- **Entry:**
  - Run record S completed.
  - Run record A signed.
  - Storage aliases exist.
  - The tested downloader and event-log parser packet is approved and passing (ACQUISITION-PLAN).
  - The capacity check passes, using measured samples plus stated conservative projections and caps.
    It does not wait for P6/P8 artifacts to exist.
- **Work:**
  - Download to scratch, verify, promote.
  - Parse into the event log and derived parsed store.
  - Deterministic replay check.
  - Verify seed identifiers against the **final baseline-plus-updates snapshot**, and record
    whether each seed's MeSH headings are actually absent.
- **Exit:**
  - Every file verified.
  - Event-log reconciliation is exact.
  - Replay is identical.
  - Seed verification results recorded.

## P6: Selection and Tier 1 corpus v1

- **Entry:**
  - P5 exit.
  - Selection v0 approved.
  - **Seed list frozen** (hash in the log) after verification against the final snapshot.
  - P3 contracts available.
  - Capacity rechecked.
- **Stage 1: bibliographic selection** (`SEARCH-AND-SELECTION.md` section 5):
  1. Create the confirmation reserve (hash-based, fixed before any sampling). Reserved PMIDs are
     never inspected during development.
  2. Run selection v0 (candidate logic, hard exclusions, WORKFLOW cap after exclusions) and
     measure seed recall.
  3. Draw **development** precision samples from non-reserved records. Revise the policy at most
     **3 times** (v0 to v3). Every version is kept and reported.
  4. Freeze the bibliographic policy.
  5. Draw the **confirmation** sample from the reserve and evaluate it once. At most **2
     confirmation rounds**; a second failure stops and escalates to Quinton. All rounds are
     reported. Small strata are handled as a census, per section 7.3.
  6. Freeze the **bibliographic candidate set**.
- **Stage 2: representation and rights resolution:**
  1. Sign run record B. Look up PMC for **all** candidates with a PMCID, including candidates that
     have no abstract.
  2. Resolve rights. Assign final dispositions; `metadata_only` is assigned only after the lookup.
  3. Normalization, passages, manifest.
  4. Rebuild check.
  5. Measure the Tier 1 rebuild set and propose the independent-backup allocation (SCOPE 5.7).
- **Exit:**
  - Pre-set bars met on the confirmation sample (or census, as labelled), or documented failure and
    escalation.
  - Seed-recall bar met, or every miss explained and approved.
  - Quinton approves the freeze.

## P7: Evaluation set frozen (Quinton-owned)

- **Entry:** P1 needs approved. Corpus v1 frozen.
- **Work:**
  - Quinton writes 60 questions from approved needs: 30 development and 30 held-out, each with 20
    answerable and 10 refusal, stratified by family (D-209).
  - Label relevance as **evidence spans** (definition below), plus source-level labels.
  - **Required second consistency pass** across similar questions and duplicate sources
    (`../QUESTION-SET-AND-EVALUATION.md`). An optional blinded repeat sample is a separate activity.
  - Freeze questions, splits, relevance rules and labels with hashes.
- **Span and label definition (PROPOSED):**
  - **Coordinates:** a span is (`representation_id`, `representation_sha256`, `start`, `end`),
    half-open over Unicode code points of that immutable normalized representation text (the same
    normalization as P3).
    - A normalization change creates a new representation hash, so labels are remapped into a **new
      label version**. They never silently carry over.
  - **Gold spans are minimal and self-contained:** the smallest continuous text that supports the
    required concept on its own, including any qualification or negation that changes its meaning.
  - **Grades:** `direct`, `partial_context`, `contradicting_or_limiting` or `uncertain`, each tagged
    with the required-concept IDs it supports.
  - **Uncertain** spans are excluded from primary binary relevance until adjudicated.
  - **From spans to passages (per configuration):**
    - a passage is **direct** evidence for a question only if it **completely contains** a direct
      span;
    - any partial overlap is **partial evidence** and never counts as direct support;
    - a looser rule would need an explicitly adjudicated semantic rule, approved before use;
    - overlapping or duplicate chunks can each contain the same span.
  - **Metrics, part A: ranked retrieval** (scored on the ranking, with no context budget):
    - **Ranking definition:** each configuration outputs an ordered passage list of length 50,
      with deterministic tie-breaking (score, then `passage_id`).
    - **Source-level ranking:** map each passage to its `source_work`. Keep the first occurrence of
      each work (later duplicates are dropped), then renumber ranks 1, 2, 3 and so on.
    - **Official metrics (D-085, unchanged):**
      - source-level recall@1/3/5/10 and MRR over the deduplicated source ranking (comparable
        across chunking);
      - passage-level recall@1/3/5/10 and MRR, where a relevant passage completely contains a
        direct span. These are reported only **within** one chunking configuration, because the
        passage count per question changes with chunking.
      - A reciprocal rank of 0 means no relevant item appears within the ranking list.
    - **Proposed additional ranked metric: span-hit recall@k,** the fraction of a question's direct
      spans completely contained in at least one top-k passage. Its denominator is fixed across
      chunking. It is **not** a D-085 replacement unless the amendment in SCOPE section 10 is
      approved.
  - **Metrics, part B: delivered evidence under a context budget** (evaluated separately):
    - **Budget:** proposed 2,000 tokens, a starting experimental setting, not a product limit.
    - **Tokenizer:** a single pinned tokenizer, recorded by name and hash. Before the generator is
      chosen, a pinned reference tokenizer is used and named in each result. After P10, the chosen
      generator's tokenizer is used and results are re-reported.
    - **Packing rule (proposed):** walk the ranked passage list in order. Add each **whole** passage
      if it fits in the remaining budget; if it does not fit, **skip it** (never truncate it) and
      continue down the list until the budget or the list runs out.
    - **Scoring:** a direct span counts as **delivered** only if it is completely contained in the
      text actually supplied to the response system. A span in a retrieved but skipped or truncated
      passage is not delivered support. Any future truncation policy is scored on the truncated
      text.
    - **Reported:** delivered-span recall, delivered concept coverage, and delivered token count.
  - **Storage:**
    - Development questions and labels go to the normal lane artifacts and Git.
    - Held-out authoring, freeze and evaluation follow the lifecycle in SCOPE 5.8, never the
      working checkout.
- **Exit:**
  - Freeze recorded before any P8-P10 tuning.
  - Tuning code and Tier 2 never reference the held-out location (static check and test; this is
    not an access-control guarantee). Access follows the procedural boundary in SCOPE 5.8.
- **Effort:** the largest human-time item. Claude provides a labelling helper and validators.

## P8: Embeddings and first published build (Week 5)

- **Entry:**
  - P4b exit.
  - Corpus v1 frozen (P6).
  - **P7 frozen.**
  - Each embedding-model download authorized, with licence checked (L-13).
- **Work:**
  - Generate and freeze embedding artifacts (L-08).
  - Load, validate, publish.
  - Rebuild and verify.
  - Smoke-query all branches with synthetic and development questions only.
- **Exit:** Queryable prototype demonstrated. Rebuild verified. Measurements recorded.

## P9: Retrieval development selection (Week 6; development only)

- **Entry:** P7 and P8.
- **Work:**
  - Preregister the primary metric **from the D-085 set** (proposed: source-level recall@10), with
    source-level MRR secondary.
  - Also report span-hit recall@k (part A, proposed) and delivered-evidence metrics (part B) at
    the 2,000-token starting budget.
  - Compare lexical, dense (each L-13 configuration), hybrid, and optional rerank.
  - Compare chunking candidates (new corpus and label versions via spans) and top-k/pool values.
- **Exit:** Selected retrieval configuration recorded (the held-out set is not touched).

## P10: Response development (development only)

- **Entry:** P9 selection. Plan 10 boundary review for the generator; each model pull authorized.
- **Work:**
  - Sufficiency gate.
  - Extractive fallback first.
  - Fixture adapter.
  - Local LLM candidates (L-14) scored for groundedness, citation support, refusal, latency and
    memory against the SCOPE 5.5 limits.
  - Post-validator.
  - Adversarial tests.
- **Exit:** Selected response configuration. Zero unsupported clinical claims or invented citations
  on development.

## P11: Freeze and held-out evaluation (by Week 8)

1. Freeze the **complete** configuration: corpus, labels version, chunking, embeddings, index,
   query, fusion, top-k, sufficiency thresholds, prompt, generator. Record hashes.
2. Quinton mounts the **frozen held-out image read-only** for a logged evaluation session
   (SCOPE 5.8). The evaluator runs held-out retrieval **and** response evaluation **once**, then
   the image is unmounted.
3. Report without subsequent tuning. A genuine defect triggers a documented complete rerun under the
   rules in `../QUESTION-SET-AND-EVALUATION.md`.

- **Exit:** Held-out report (retrieval and response) published.

## P12: Integration and G6 (by Week 8)

- **Entry:** P10 outputs for integration work; P11 for final G6 evidence; Plan 04 coding
  authorization; Plan 08 integration point.
- **Work:**
  - Literature workflow stages under Plan 04.
  - Static and FastAPI transport parity.
  - UI states: answered, partial, refused, unavailable.
  - G6 evidence.
- **Exit:** Every SCOPE section 7 item evidenced.

## X1: Tier 2 extension (gated)

- **Entry:** A separate approved extension plan. Tier 1 checkpoints on schedule. Never Weeks 9-10.
- **First step:** a bounded broader sample as its own corpus ID; measure whether breadth helps
  without hurting precision.
- **Never:** mixed into Tier 1, given access to held-out labels, or used for product answers.

---

## Authorization checklist (none granted by this document)

| Item | Phase | Status |
|---|---|---|
| Approve the planning set; confirm L-03/L-08/L-09 for recording | P0 | **Done**: Quinton, 2026-09-28 (SCOPE 12A/12B) |
| Codex acknowledges SCOPE section 10 | P0-P2 | Pending |
| Revised foundation packet | P3 | Pending |
| Runtime/PostgreSQL/pgvector install; Docker inventory; RAM recorded | P4a | Pending |
| psycopg 3 dependency | P4b | Pending |
| Storage aliases | P4a-P5 | Pending (Codex) |
| Downloader/parser packet | P5 | Pending |
| Run record S (sizing preflight) signed | P2-P5 | Pending |
| Run record A signed | P5 | Pending |
| Run record B signed | P6 | Pending |
| Literature backup allocation | P6 | Pending (after measurement) |
| Protected held-out store and evaluator access procedure | P7 | Pending |
| D-085 amendment for the additional span-hit metric | P7-P9 | Proposed (Codex/Quinton) |
| Embedding model downloads | P8 | Pending |
| Generator runtime/model | P10 | Pending (Plan 10) |
| Plan 04 workflow coding | P12 | Pending |
| Tier 2 plan | X1 | Not requested |
