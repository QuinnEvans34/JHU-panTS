# Plan 07 lane running log

**Rules:**

- **Append-only.** New entries go at the bottom. Earlier entries are never edited. Corrections are
  new entries that name what they correct.
- Each entry records what was actually done, why, what was decided and by whom, what was **not**
  done, and what comes next.
- Plans and intentions go in `SCOPE.md` and `PHASES.md`, not here.

---

## 2026-09-28: Lane opened; planning set drafted (Claude)

**Context:** Quinton asked Claude to own the Plan 07 lane while Codex focuses on imaging/data
readiness. Quinton wants all problems found on paper before code, reasoning documented throughout,
and all three team members kept current, including Notion.

**What Claude did:**

1. Read the approved design:
   - `implementation/07-literature-retrieval.md`;
   - `retrieval/CORPUS-AND-RIGHTS.md`, `QUESTION-SET-AND-EVALUATION.md` and `README.md`;
   - relevant rows of `DECISIONS.md` (D-073..D-087, D-202, D-209, D-211, D-401);
   - `operations/STORAGE-ROOTS-AND-ARTIFACTS.md` excerpts;
   - Codex's `CLAUDE-PLAN07-FOUNDATION-PACKET-2026-09-28.md` and
     `PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md`;
   - proposal v3.8/v3.9 and appendix v3.1 text (read-only extraction), and the historical v2 draft
     `docs/_build_proposal.md` / `_build_appendix.md`.
2. Checked current public facts (web):
   - the PubMed 2026 baseline (1,334 files, released 2026-01-30; updates from n1335);
   - NLM data-use conditions;
   - the PMC distribution change (OA Web Service API retired, datasets off FTP, August 2026; PMC
     Cloud Service on AWS);
   - the E-utilities API-key rate guidance.

   Sources are cited in `ACQUISITION-PLAN.md`. The NLM FTP terms README could not be fetched by
   Claude's web tool (robots policy) and was not bypassed. Quinton reviews it at signing.
3. Wrote a decision brief (D1-D8) for Codex through Quinton. Codex answered in
   `PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md`.
4. Created six planning documents in this directory (hashes below) and this log. Directory and
   files were checked absent first. HEAD at start: `f4d7109b466fc12854be4a86c9893750399a0672`.

**Decisions made by Quinton (2026-09-28):** see `SCOPE.md` section 2.

- L-01 Tier 1 committed.
- L-02 Tier 2 as a gated extension.
- L-03 bulk baseline + updates acquisition.
- L-05 PostgreSQL + pgvector for the literature layer.
- L-06 literature only.
- L-07 files authoritative.
- L-08 frozen embeddings.
- L-09 database on the external drive (procedure pending).
- L-12 two documents for scope and phases.
- Docker preferred (L-10, proposed).
- Lexical baseline delegated to Claude (L-11, proposed).

**How the reasoning evolved (recorded for honesty):**

- Claude first framed PubMed only as an API. Quinton pointed out it is also a downloadable dataset.
  That was correct; the annual baseline is an approved NLM route.
- Claude argued against embedding all of PubMed as the graded corpus. Codex corrected two
  overstatements in that argument:
  - removing treatment papers is not a safety proof; refusal gates are required at any size;
  - a small corpus does not guarantee complete relevance labels.

  Claude accepted both. The conclusion still holds: Tier 1 is focused and graded, and broader
  coverage is tested through Tier 2 rather than assumed.
- On acquisition, Claude first recommended bulk, then agreed with Codex's recommendation of
  E-utilities for Tier 1. The reasons were the MeSH gap on recent records, selection being a new
  search policy, and no need for a decision amendment. Quinton chose bulk (L-03). Codex's cautions
  are carried into `SCOPE.md` section 6 as requirements.
- On storage, Claude recommended the internal SSD for the live database. Quinton chose the external
  drive because internal space is limited and everything is in one place. Claude agrees this is
  acceptable **because** L-07 makes the database rebuildable. The residual risks (Docker/fsync
  durability, drive latency, memory) are measured in P4 with a stop rule.
- The vector database was never in question. The approved proposal requires vector search.
  PostgreSQL + pgvector replaced the SQLite + LanceDB direction on Quinton's decision, with Codex's
  rundown (literature only, files authoritative).

**What was NOT done:**

- No code written.
- Nothing downloaded, installed or pulled (no Docker, PostgreSQL, models).
- No shared or Codex-owned file edited. No commit, stage or push.
- No PubMed or PMC query issued.
- The foundation packet remains on hold (L-14).

**Files created (SHA-256):**

| File | SHA-256 |
|---|---|
| `SCOPE.md` | `708967652b442b1e54a9666b21a5d7a4d4de004979683c1bf62797cd87d4b931` |
| `PHASES.md` | `8d50491b56ef7c32e658f646234ccae2198ac7bfaa0f188ab16333be21b80602` |
| `INFORMATION-NEEDS.md` | `b92f504c0894ece49b5b22281b345ecbbd2ad15f7721fa9b8772fdc29c8db171` |
| `SEARCH-AND-SELECTION.md` | `d4c82214258f6cbc3d288f0248c2ac763563d15743cca2ca4a42dc4e3e8d5ee1` |
| `SEED-SET.md` | `df6136575ad218bfe004f135811eb8c7e930f3e15aab2f1b7efd86f8082e3d9a` |
| `ACQUISITION-PLAN.md` | `f32d1351b122bf5fe46f106d508dd2c25557ef3100f838b9d8b0b322cc5961a6` |

**Pending decisions (owner):**

- Quinton:
  - approve or revise the PROPOSED L-items;
  - edit `INFORMATION-NEEDS.md`;
  - add and freeze seeds;
  - set the seed-recall and precision bars;
  - decide language and date rules.
- Codex: record the SCOPE section 10 amendments; revise the foundation packet (L-14); add the storage
  aliases.

**Next:** Quinton and Codex review this planning set. No phase beyond P0 starts until approved.

---

## 2026-09-28: Correction to SCOPE section 10 (Claude)

After the planning set was written, `git status` showed that Codex had concurrently added a PMC
route-verification note to `retrieval/CORPUS-AND-RIGHTS.md`. That file was not touched by Claude.
The SCOPE section 10 row for that file was updated to say the PMC part is done and only the bulk
baseline channel remains. New `SCOPE.md` SHA-256: `b29a15956cee3d183f2fd9088100e45af3b59d343c83c191e07262e4353d5346`. No other file changed.

---

## 2026-09-28: Notion work-log entry (Claude)

Created one Work Log entry in the PROWL Notion hub: "Plan 07 evidence system: lane opened and
planning set drafted" (Session, 2026-09-28).

- Hours left blank.
- Evidence is labelled local and uncommitted.
- The hub snapshot page was not edited; Codex keeps it.
- Entry: https://app.notion.com/p/3e9171a931408152ac59ecb71794a23d

---

## 2026-09-28: Revision 2 after Codex review (Claude)

**Trigger:** Codex reviewed all seven v1 files (message relayed by Quinton). It accepted the
architecture in principle and required revisions before implementation approval. Claude
revised only its own planning files. No shared or Codex-owned file was edited. No code, installs
or downloads.

**Corrections to Claude's earlier claims (recorded plainly):**

1. **Wrong recovery claim.** In v1 (SCOPE L-09, R-01) and in chat to Quinton, Claude said files
   being authoritative turns worst-case corruption into "a rebuild, not data loss". That was
   wrong. The database and the canonical artifacts share `PROWL-Data`, so a drive or filesystem
   failure can take both. Recovery then depends on verified independent backups or reacquisition,
   and upstream bytes (PMC objects, past-year baselines) may no longer be available. Fixed in
   SCOPE 5.7.
2. **Drills over-claimed.** A container kill proves process-crash recovery only, not durability
   under USB disconnection or power loss. `amcheck` does not validate pgvector indexes. v1's
   automatic "drop and rebuild" became a scoped recovery that preserves evidence. v1 assumed
   "smart shutdown"; the actual stop signal and grace period are now recorded at pin time.
3. **Unmeasured claims.** "Nothing on the internal SSD" and "mostly memory-resident" were removed.
   Moving Docker's disk image is a global setting, so it now needs inventory and approval.
4. **Wrong decision attribution.** L-05/L-06/L-07 now cite **D-260** (which Claude had not read
   before v1). L-03, L-08 and L-09 are attributed to Quinton's Claude discussion and need his
   confirmation to be recorded. D-077's text permits approved services generally; the
   E-utilities specificity is in P07-05 and `CORPUS-AND-RIGHTS.md`.
5. **Phase contradictions.** v1 said "11 phases" but listed 12 (P0-P11). P4 was described as fully
   parallel despite depending on P3's contracts. P8 did not gate on P7's freeze. P9's held-out run
   came before response development.
6. **Seed-set errors.** v1 wrongly said family 2 was empty (S-01 covers it). It treated a recent
   publication year as evidence of missing MeSH. It proposed treatment papers as negative seeds,
   which the current rules do not exclude.

**Changes by file:**

- **SCOPE v2:**
  - status labels distinguish D-260 approvals from discussion approvals;
  - embedding and generation choices marked PROPOSED (L-13, L-14);
  - packet hold renumbered L-15, selection specifics L-16;
  - 5.2 verification now covers content hashes and embedding checksums;
  - 5.3 adds `source_event` and content-hash revision IDs;
  - 5.5 covers Docker scope, measured footprint and numeric coexistence limits on a synthetic
    workload;
  - 5.6 is the corrected procedure;
  - 5.7 is new: recovery honesty and a rebuild-set backup table (the shared 20 GiB cap is not
    assumed to be available);
  - reconciliation list rewritten.
- **PHASES v2:**
  - 13 phases (P0-P12) plus X1;
  - P4 split into P4a (infrastructure, independent) and P4b (contract-bound, after P3 review);
  - P4a starts with exact search plus one approximate configuration, with numeric triggers for
    expansion;
  - P8 gates on P7;
  - development selection (P9) and response development (P10) are separate, then a complete freeze
    and one held-out run (P11), then integration (P12);
  - P7 defines span coordinates, grade mapping, span-hit recall (denominator fixed across
    chunking), label versions and the required second consistency pass;
  - fresh confirmation sampling added to P6.
- **SEARCH-AND-SELECTION (policy v0, revision 2):**
  - IMG defined;
  - WORKFLOW cap of 500 with a deterministic order;
  - qualifier used as a recorded feature with a preset v1 rule;
  - one disposition plus multiple reason codes with precedence;
  - language, missing-date and competing-date rules;
  - sampling rubric, strata, census for small strata, relevant/partial reported separately,
    development versus fresh confirmation samples.
- **ACQUISITION-PLAN revision 2:**
  - full envelope for run B;
  - capacity model with every component;
  - parsed-store location, authority, format and lifecycle;
  - event-log revision identity and replay;
  - required downloader and parser tests;
  - upstream-availability caveat.
- **SEED-SET revision 2:**
  - assisted citation-chaining discovery with Quinton's review;
  - identifiers verified against the local baseline;
  - indexing status taken from `MedlineCitation/@Status`;
  - negative seeds must be genuinely outside the policy;
  - prior exposure disclosed;
  - coverage table corrected.
- **INFORMATION-NEEDS revision 2:**
  - prior exposure disclosed;
  - N1.4 and N3.4 phrased as general and literature-based;
  - RF8 narrowed to prohibited disclosure, with answerable provenance questions separated.

**New SHA-256 (this entry does not include its own hash):**
- `SCOPE.md`: `009a596afc764f804f84ab0247f000c55390c0d31db09276b4dfb1f26f680112`
- `PHASES.md`: `9ed4af47ace244134336f4a9d5a9a825f6b0993d34d9b810087d778d0f006744`
- `INFORMATION-NEEDS.md`: `5e9764cc94c6d06db4b9b84ec766128aaa6c1d3599fe18f04c8e8d8e9f1a0721`
- `SEARCH-AND-SELECTION.md`: `9dc44a5d16506f2c3af65a4277400d116135ebfc42c2bf8eecb82338a0a54315`
- `SEED-SET.md`: `6581117aad954af13b661b067bfc04c75a74baad586930b73e72670338b0185c`
- `ACQUISITION-PLAN.md`: `d8a611fcdc84c86d099b26d85d8f974e4b6d32164bae5f3c6e907ae9f1b56591`

**Unresolved decisions:**

- **Quinton:**
  - confirm L-03, L-08 and L-09 for recording;
  - approve PROPOSED items (L-04, L-10, L-11, L-13, L-14, L-15);
  - selection OPEN items (English-only, the 2000-cutoff range, WORKFLOW cap, seed-recall and
    precision bars);
  - Docker inventory approval if any shared setting is proposed;
  - record the Mac's RAM so the coexistence limits can be confirmed;
  - literature backup allocation after the P6 measurement;
  - whether to plan a second independent drive for raw sources.
- **Codex:**
  - SCOPE section 10 reconciliation;
  - revised foundation packet;
  - storage aliases;
  - the downloader/parser packet allowlist.

**Next:** Quinton and Codex review v2. No phase beyond P0 starts until approved.

---

## 2026-09-28: Notion work-log entry for revision 2 (Claude)

Created the Work Log entry "Plan 07 planning set revised (v2) after Codex review" (Session,
2026-09-28). Hours blank. Evidence labelled local and uncommitted.
https://app.notion.com/p/3e9171a9314081b89933fc2498fdf11a

---

## 2026-09-28: Revision 3 after second Codex review (Claude)

**Trigger:** Codex reviewed v2, confirmed the six document hashes against this log, and accepted
the architecture and phase structure. It requested six targeted corrections. It also verified the
Mac has **64 GiB physical RAM**, now recorded in SCOPE 5.5 and PHASES P4a; resource limits stay
PROPOSED until P4a measures them. Claude edited only its own planning files. No code, installs,
downloads or shared-file edits.

**Corrections (what was wrong in v2, and the fix):**

1. **The 50% span-overlap rule was unsound.** The missing half of a span can hold the negation or
   qualification that changes its meaning.
   - Gold spans are now minimal and self-contained, and direct support requires **complete
     containment**. Partial overlap counts only as partial evidence.
   - Span-hit recall is now a **proposed additional metric**; D-085's metrics stay official. A D-085
     amendment was added to SCOPE section 10.
   - Retrieved token volume is recorded, and cross-chunking comparisons use a fixed context budget
     (proposed 2,000 tokens).
   - The P9 primary metric is preregistered from the D-085 set (proposed: source-level recall@10).
2. **Capacity dependency cycle.** v2 required sample measurements and future Tier 1 artifacts
   before run A could be signed.
   - Added **run record S**, a separately authorized, tightly bounded sizing preflight (at most 3
     baseline + 2 update files + MeSH, at most 10 GiB, at most 2 h, not promoted).
   - The capacity model is now measured-plus-capped (100 GiB caps for Tier 1 artifacts and for
     database/recovery), rechecked before each phase.
3. **Selection depended on PMC eligibility before PMC was looked up.**
   - Selection is now two-stage: bibliographic candidates are frozen first; full-text availability
     and rights are resolved after.
   - `metadata_only` is assigned only after the lookup, so no-abstract candidates are looked up too.
   - The WORKFLOW cap is applied after hard exclusions, with missing years sorted last. There is no
     refill after stage 2, and that is reported.
4. **Confirmation edge case.**
   - A hash-based confirmation reserve (about 10%, salt fixed in advance, independent of policy
     version) is created before any development sampling.
   - Confirmation estimates the unseen remainder of each stratum.
   - Strata under 100 candidates are a census, with no independent confirmation claimed.
   - Preset limits: 3 policy revisions and 2 confirmation rounds. A second failure escalates. All
     attempts are reported.
5. **Backups conflicted with held-out isolation.**
   - Added SCOPE 5.8, a protected held-out store: an encrypted disk image using the built-in
     `hdiutil`, Quinton holds the passphrase, an independent encrypted copy is kept on the internal
     backup, evaluator access only in P11, and every access audited.
   - Git holds schemas, synthetic examples and the held-out manifest hash only.
   - Stated plainly: a local commit is not an independent backup until pushed.
   - Regenerated embeddings get a new artifact and build identity.
6. **Contract details.**
   - The filtered-search invariant now returns up to `min(k, eligible_count)`, with an explicit
     count and reason.
   - Seed verification uses the final baseline-plus-updates snapshot.
   - The missing-MeSH test condition is actual absence of MeSH headings, not non-MEDLINE status.

**New SHA-256 (this entry does not include its own hash):**
- `SCOPE.md`: `1568a473e1ff5f37baecb37896da0aa684a9b35e98b6d513a5d56c0d905580b5`
- `PHASES.md`: `a045dcce9f146cafb8109c8301deefcf4a659fa10ac6134002e79e6b676d954e`
- `SEARCH-AND-SELECTION.md`: `e09a4456d2cb908f95f747aad4f041b7dca3deba5b4cfb318ab63b72f2828da8`
- `ACQUISITION-PLAN.md`: `27bf156d47ac17dc31f6990b599641f94ef865f137e0ae14efdd8e2d5f05a0d2`
- `SEED-SET.md`: `39ee09bc8327c6bccc9f15f859ebf041345bde68385d4a3639134aa6f8f66d81`
- `INFORMATION-NEEDS.md`: `5e9764cc94c6d06db4b9b84ec766128aaa6c1d3599fe18f04c8e8d8e9f1a0721`
- `INFORMATION-NEEDS.md` is unchanged in this revision.

**Remaining decisions:**

- **Quinton: confirm for recording.**
  - L-03 bulk PubMed acquisition. Codex's view: reasonable if you want the reusable snapshot; not
    required for a capable focused expert; confirm separately from the database choice.
  - L-08 frozen embeddings. Codex: yes.
  - L-09 external-drive database as a direction to test, with the SCOPE 5.7 backup limits
    understood. Codex: acceptable.
- **Quinton: approve or revise the provisional selection controls.** Codex: reasonable as
  provisional controls, not proof of accuracy.
  - English-only, with explicit missing-language handling.
  - 2000 to cutoff; known foundational-paper misses are reviewed through seed recall.
  - WORKFLOW cap of 500.
  - Bars: seed recall at least 90%; confirmation at least 60% relevant+partial and at least 40%
    relevant.
- **Quinton: the remaining PROPOSED items.**
  - L-04, L-10, L-11, L-13, L-14, L-15.
  - Proposed context budget of 2,000 tokens.
  - Protected held-out store design (SCOPE 5.8).
  - Run record S caps.
  - Tier 1 and database capacity caps (100 GiB each).
- **Codex / Quinton:** the D-085 span-hit metric amendment; SCOPE section 10 reconciliation; the
  revised foundation packet; storage aliases; the downloader/parser packet allowlist.
- **Later (measured):** literature backup allocation (P6); a second drive for raw sources (OPEN).

**Next:** Quinton decides. Codex reviews v3 only if Quinton wants another pass. Nothing executes
until the relevant authorizations exist.

---

## 2026-09-28: Notion work-log entry for revision 3 (Claude)

Created the Work Log entry "Plan 07 planning set revision 3 (second Codex review)". Hours blank.
Evidence labelled local and uncommitted.
https://app.notion.com/p/3e9171a93140816891e5c6ea623c77d7

---

## 2026-09-28: Revision 4 after third Codex review (Claude)

**Trigger:** Codex accepted the architecture and asked for four procedural corrections plus an
approval checklist that separates design, provisional settings and execution permissions. Claude
edited only its own planning files.

**Corrections:**

1. **Run S dependency cycle.** v3 listed "run S completed" among the prerequisites for signing,
   which included run S itself.
   - Prerequisites are now separated for S, A and B.
   - Added a **sizing-only parser mode**: per-file, no event log or snapshot, outputs refused by
     selection and promotion.
   - Run S gets a total scratch cap of 40 GiB (downloads + decompressed + parsed) alongside the
     10 GiB download cap.
   - Volume and free-space checks happen before each file and every 60 s.
2. **Confirmation isolation.**
   - Added a global, append-only **inspected-PMID ledger** across versions, strata, rounds and
     censuses. Any inspected PMID is permanently ineligible for confirmation.
   - A stratum with fewer than 20 unseen reserved records gets no confirmation claim, and the
     limitation is reported.
   - A census stratum never later claims confirmation.
3. **Held-out lifecycle.** v3's "access only in P11" was impractical, because authoring, the
   consistency pass, freezing and backup verification all need access.
   - SCOPE 5.8 now defines authoring (read-write, logged), freeze (a new frozen image, hashes
     recorded), backup verification (image-hash comparison) and evaluation (read-only mount,
     logged).
   - The access boundary is stated honestly as procedural: a mounted image is readable by any
     process running as Quinton's user, so it is mounted outside agent-connected folders and the
     passphrase is not given to agents. The static path check is not an access-control guarantee.
   - This is not drive-wide encryption.
4. **Ranked metrics versus context-budget metrics.**
   - Part A (ranked): a defined 50-passage ranking, deterministic tie-breaking, source
     deduplication by first occurrence with renumbered ranks, the official D-085 metrics, and
     proposed span-hit recall.
   - Part B (delivered evidence): 2,000-token starting budget, pinned and named tokenizer,
     whole-passage packing that skips rather than truncates, and support counted only if a span is
     completely inside the text actually supplied.

**Added:** SCOPE section 12, an approval checklist in three groups:
- A. architecture and design;
- B. provisional experimental settings;
- C. execution permissions, none granted.

The 100 GiB caps are labelled ceilings, not expected sizes. The model choices are listed as
needing specific named models before any download.

**New SHA-256 (this entry does not include its own hash):**
- `SCOPE.md`: `e603d5799939b19fd4e12c2afd603e4837c196b948a823c11ecd192063c8956a`
- `PHASES.md`: `98bd849e3bfbb76310d9d29fddb66951878bca7c79d42f5c09f8d0c0682d261c`
- `SEARCH-AND-SELECTION.md`: `bcddbb4b78ba6ab50be059936ecb606fb145b9a1db81f1ab58761edd30c0728c`
- `ACQUISITION-PLAN.md`: `39e3752005907483d60667603a520ab549f9219dcb17d213f9c6de4f9e99fd2d`
- `SEED-SET.md` and `INFORMATION-NEEDS.md` are unchanged in this revision.

**Next:** Quinton decides the SCOPE section 12 groups A and B. Group C items are requested one at a
time. Codex issues the revised synthetic foundation packet (P3).

---

## 2026-09-28: Notion work-log entry for revision 4 (Claude)

Created the Work Log entry "Plan 07 planning set revision 4 (architecture accepted; approval
checklist)". Hours blank. Evidence labelled local and uncommitted.
https://app.notion.com/p/3e9171a931408136bd83f8f24ca388ea

---

## 2026-09-28: Quinton approves the planning set (Claude records)

**Decision (Quinton, in the Claude discussion, 2026-09-28):** "full approve on everything
suggested". Recorded with this exact scope:

- **Approved (SCOPE section 12, group A, design):**
  - Plan 07 scope, the 13-phase structure, and development/held-out separation;
  - L-03 bulk PubMed baseline + updates as the intended route;
  - L-08 frozen embedding artifacts;
  - L-09 external-drive database as a direction, subject to the P4a trial and the SCOPE 5.7 backup
    limits;
  - L-10 Docker and L-11 `ts_rank_cd` baseline as prototype candidates;
  - the encrypted held-out container (SCOPE 5.8);
  - two-stage selection, the confirmation reserve and the inspected-PMID ledger.

  L-04 (the PMC Cloud route) and L-15 (the packet plan) are recorded as approved as part of the
  approved scope. L-03, L-08 and L-09 are **confirmed for recording** by Codex.
- **Approved as provisional (group B):** every setting in SCOPE 12B. Each is changeable by a
  recorded decision.
- **Not granted (group C):** every execution permission. That means:
  - no install, dependency, download (runs S, A, B) or model pull;
  - no Plan 04 coding.

  Each is requested separately when its phase is reached.
- **Still PROPOSED:** L-13 and L-14. Specific models must be named, with licences and sizes,
  before approval.
- **Not covered by this approval, and still Quinton's work:**
  - editing and freezing `INFORMATION-NEEDS.md` (P1);
  - reviewing seed candidates (P2).

**Files updated to show approval status (status lines only; no content changes):**
- `SCOPE.md`: header, section 2 register status cells, section 12 statuses.
- `PHASES.md`: header, and the P0 checklist row.

New SHA-256:
- `SCOPE.md`: `ca9a0de192cf5d6b241c17ca1796f02b7c39b006e2e9d872afc1c3b767861672`
- `PHASES.md`: `b4abe42d9d1b43504087175ab8f168356fd16356e6868402713ada862d1da4ca`

The other planning files are unchanged since revision 4.

**Notion:** Task Board rows created (Plan 07):
- "Plan 07: scope, phases and protocols planning set" (Done);
- "Plan 07 P1: Quinton reviews and freezes information needs" (Ready);
- "Plan 07 P3: synthetic retrieval foundation (revised packet)" (Planned);
- "Plan 07: record approvals and reconcile shared documents" (Ready, Codex);
- "Plan 07 P4a: PostgreSQL + pgvector platform prototype" (Planned; requires drive).

A matching Work Log entry is added separately.

**Handoff to Codex (integration owner):**

1. Record Quinton's approvals (L-03, L-08, L-09, and the approved lane design) in `DECISIONS.md`,
   citing this entry and SCOPE section 12.
2. Record the D-085 span-hit/delivered-evidence amendment as a **proposal** for Quinton's decision.
3. Work through the SCOPE section 10 reconciliation list.
4. Add the storage aliases `literature_source` and `prowl_literature_db`.
5. Issue the revised P3 synthetic foundation packet: records, passages, query gate, span-based
   labels, metrics (ranked plus delivered-evidence), with no SQLite FTS5.
6. Decide whether the uncommitted planning set joins the pending scoped Git checkpoint (Notion task
   "Review and publish a scoped Git checkpoint"). That checkpoint needs Quinton's explicit
   authorization.

**Claude's next action:** none until the revised P3 packet is issued and dispatched by Quinton.

---

## 2026-09-28: Phase 1 complete, information needs frozen v1 (Claude records)

**Decision:** Quinton reviewed the drafted needs with Codex and approved Codex's recommended
revisions as the final version.

- 11 needs kept; 11 edited to Codex's wording.
- 3 added: N4.6 reported performance and comparison limits; N5.5 public-dataset label provenance;
  N5.6 incomplete coverage and uncertain labels.
- The cystic/solid topic is folded into N2.4 (target extent), with no subtype inference.
- None dropped.
- Refusals: RF2, RF5, RF7 and RF8 edited. **RF9 added:** no case-specific certification of a
  contour and no acceptance decision on the reviewer's behalf.
- Authorship recorded as: Claude drafted, Codex recommended revisions, Quinton reviewed and approved.
- The added needs do not change the 60-question set (D-209).

**Frozen file:** `INFORMATION-NEEDS.md` v1, SHA-256
`d71577c27cebd5d54f516a7b2120273c3afba7dc077be3799bae4ccecbde8ac0`. Any change creates v2 with a
recorded reason.

**Observed (not reviewed in depth by Claude):**
- Codex has recorded D-261 to D-265 in `DECISIONS.md` (acquisition route, frozen embeddings, drive
  placement, design, provisional settings).
- Codex has issued `operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md`, plus
  `PLAN07-INTEGRATION-HANDOFF` and `GIT-CHECKPOINT-SCOPE` documents.

Claude's other planning files are unchanged by this entry.

**Next:** Claude reads the P3 packet and begins the synthetic foundation once Quinton dispatches it.

---

## 2026-09-28: P3 started (Claude)

Quinton dispatched `operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md`: "Go on P3 using Codex's
revised packet. Follow its write allowlist and synthetic-only scope. Keep the additional metrics
explicitly provisional, run the required tests, and stop after preparing your handback."

**Preflight:**
- `pwd` / `git rev-parse --show-toplevel` point to the PROWL checkout, as seen from Claude's Linux VM
  mount.
- `check_workspace.py` passed.
- HEAD is `f4d7109b466fc12854be4a86c9893750399a0672`, with 154 existing modified/untracked entries
  preserved.
- None of the allowlisted P3 paths existed.

**Environment:** the native `.venv-prowl` is a Mac venv. Its interpreter is a broken symlink inside
Claude's Linux VM, so native tests cannot run here. Claude develops and tests in a Linux container
(Python 3.12.3, jsonschema 4.26.0 and pytest 9.1.1 pinned as in the project). Native verification is
left to Codex.

**Scope held:**
- pure Python, synthetic fixtures only;
- no SQL, services, tokenizers, downloads, real text or held-out data;
- the span-hit and delivered-evidence metrics are labelled as a proposal.
