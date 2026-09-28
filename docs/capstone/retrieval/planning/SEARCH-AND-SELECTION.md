# Search and selection protocol: policy v0

**Status:** PROPOSED policy v0, document revision 4 (third Codex review, 2026-09-28). Nothing has
been run. No counts here were produced by this policy. Items marked OPEN need Quinton's decision
before the first run.
**Route:** L-03. Selection runs locally over the ordered, parsed 2026 PubMed baseline plus update
files (`ACQUISITION-PLAN.md`). It is **PROWL's own versioned selection policy**, not a PubMed web
search and not PubMed's automatic term mapping.
**Inputs:**
- approved `INFORMATION-NEEDS.md`;
- a frozen `SEED-SET.md`;
- MeSH 2026 descriptor data (for tree-number explosion);
- the final parsed state of each PMID (last event wins, deletions removed).

**Freeze:** the selected version freezes in P6, before question labelling (P7).

## 1. Record fields used

- PMID;
- `MedlineCitation/@Status` (indexing status);
- title and all abstract sections;
- MeSH headings (descriptor UI, major flag, qualifiers);
- author keywords;
- publication types;
- `Language` elements;
- date fields (section 5.3);
- article IDs (PMC, DOI);
- CommentsCorrections (retraction, erratum, expression of concern).

## 2. Concept blocks

Each block matches if **any** MeSH rule **or** text rule matches. MeSH rules use descriptor UIs
verified in MeSH 2026 and exploded through that file's tree numbers. Names below are candidates to
verify.

| Block | MeSH (exploded) | Text rules (title, abstract, keywords) |
|---|---|---|
| **P: Pancreas** | Pancreas; Pancreatic Neoplasms; Pancreatic Ducts; Pancreatic Cyst | `pancrea*` |
| **C: CT** | Tomography, X-Ray Computed | `computed tomograph*`; case-sensitive tokens `CT`, `MDCT`, `CECT` |
| **A: AI/computation** | Artificial Intelligence; Neural Networks, Computer; Image Processing, Computer-Assisted; Radiographic Image Interpretation, Computer-Assisted; Diagnosis, Computer-Assisted | `segmentation`; `deep learning`; `machine learning`; `neural network*`; `convolutional`; `U-Net`; `nnU-Net`; `artificial intelligence`; `computer-aided`; `radiomic*` |
| **M: Measurement/annotation** | Observer Variation | `interobserver`; `inter-observer`; `intraobserver`; `observer variab*`; `annotat*`; `contour*`; `delineat*`; `manual segmentation`; `ground truth` |
| **W: Workflow/trust** | none (text only) | `automation bias`; `human-in-the-loop`; `reader study`; `AI-assisted`; `computer-assisted reading` |
| **IMG: Imaging context** (defined here, used by WORKFLOW) | Diagnostic Imaging (exploded) | the C block; `radiolog*`; `medical imaging`; `diagnostic imaging` |

## 3. Selection logic

```text
CORE     = P AND C
AI       = P AND A
MEASURE  = P AND M
WORKFLOW = W AND A AND IMG AND NOT (CORE OR AI OR MEASURE)   # general imaging-AI workflow
CANDIDATE = CORE OR AI OR MEASURE OR WORKFLOW_CAPPED
```

**WORKFLOW hard cap:** at most **500** records (PROPOSED; OPEN for Quinton).
- The cap is applied **after hard exclusions** (section 5, stage 1), so excluded records never
  consume slots.
- Deterministic order:
  1. number of distinct W-term matches, descending;
  2. derived publication year, descending, with **missing years placed after all dated records**;
  3. PMID, ascending.
- Take the first 500.
- Records that later become `metadata_only` in stage 2 do **not** trigger a refill. Their count is
  reported.
- The uncapped count is always reported.

**Diagnostic-imaging qualifier:**
- **v0 does not use it for inclusion.** Each CORE record with MeSH gets a recorded feature
  `has_dx_imaging_qualifier` (the "diagnostic imaging" qualifier on any P-block descriptor), and
  counts and precision samples are stratified by it.
- **Pre-set v1 rule:** in the v0 development sample, qualifier-absent CORE records that have MeSH
  might score below the precision bar while qualifier-present records meet it. If so, v1 requires
  the qualifier for CORE records that have MeSH. Records without MeSH are never affected.

## 4. Text matching (deterministic)

- Normalize: Unicode NFKC; casefold, except for the case-sensitive tokens; collapse whitespace.
- Tokenize on non-alphanumeric boundaries. Hyphenated terms match both with and without the hyphen.
- `*` is a single-token prefix wildcard. Quoted phrases match consecutive tokens.
- No stemming or synonyms beyond the listed terms. Any change creates a new policy version.
- The matching code and its unit tests are versioned with the policy.

## 5. Dispositions and reason codes

### 5.1 Model: two stages

Selection is **bibliographic** first. Full-text availability is resolved afterwards, so a candidate
without an abstract stays eligible for a permitted-full-text lookup.

**Stage 1: bibliographic disposition.** Each final-state record gets exactly one of:

| Precedence | Stage-1 disposition | Triggered by any reason code in |
|---|---|---|
| 1 | `deleted` | `deleted_by_update` |
| 2 | `excluded` | `not_candidate`, `pubtype_excluded`, `retracted`, `animal_only`, `language_non_english`, `year_out_of_range` |
| 3 | `excluded` | `workflow_capped_out` (applied after the rules above) |
| 4 | `candidate` | none of the above |

The frozen **bibliographic candidate set** is the stage-1 output. Precision sampling and seed recall
run on it.

**Stage 2: representation and rights** (after run record B's PMC lookup for every candidate with a
PMCID):

| Final disposition | Rule |
|---|---|
| `selected` | Has abstract text and/or permitted full text |
| `metadata_only` | No abstract **and** no permitted full text after the lookup (`no_abstract_no_permitted_fulltext`) |

Every record keeps all its reason codes; the disposition comes from precedence.

Informational codes do not change the disposition:
- `language_missing`, `date_missing`, `no_mesh`;
- `indexing_status_<value>`;
- `erratum_linked`, `concern_linked`;
- `has_dx_imaging_qualifier`;
- `fulltext_rights_unknown`.

### 5.2 Rules

| Code | Rule | Status |
|---|---|---|
| `pubtype_excluded` | Publication type in {Comment, Editorial, News, Letter, Published Erratum, Retraction of Publication}. Notices are linked as notices, not documents | PROPOSED |
| `retracted` | Record carries a retraction link (RetractionIn) or publication type "Retracted Publication" | PROPOSED |
| `animal_only` | MeSH includes Animals and not Humans. Records without MeSH never receive this code | PROPOSED |
| `no_abstract_no_permitted_fulltext` | Stage 2 only: no abstract text and no eligible PMC object after the lookup | PROPOSED (appendix A6) |

### 5.3 Language and dates

- **Language:** English if any `Language` element equals `eng`. No `Language` element gives
  `language_missing`, and the record is **included**. Otherwise `language_non_english`.
  English-only is **OPEN** for Quinton.
- **Derived publication year:** the first available of:
  1. `JournalIssue/PubDate/Year`;
  2. the first 4-digit year in `PubDate/MedlineDate`;
  3. `ArticleDate/Year` (electronic);
  4. `PubmedData/History/PubMedPubDate[@PubStatus="pubmed"]/Year`.

  If none exists: `date_missing`, and the record is **included**. Competing fields are recorded, and
  the first by this order wins.
- **Range:** 2000 to cutoff is proposed. **OPEN** for Quinton.

## 6. Treatment-focused literature

No keyword rule removes treatment literature. Its share is measured by precision sampling. Refusal
safety never depends on corpus content: the query gate and response validator enforce refusals
regardless.

## 7. Evaluation per policy version (bars set before the first run)

### 7.1 Counts

Report:
- counts per block, per branch, and overlaps;
- dispositions and reason codes, with multiple codes counted per code;
- no-MeSH inclusions by `indexing_status`;
- WORKFLOW uncapped versus capped counts.

Totals reconcile to the number of final-state records.

### 7.2 Seed recall

The share of frozen, verified seeds selected, with each miss diagnosed by rule. Proposed bar: at
least 90%, with every miss explained. **OPEN.**

### 7.3 Precision sampling

- **Scope:** sampling runs on the stage-1 **bibliographic candidate set**. Records without an
  abstract are labelled from the title and flagged.
- **Strata:** each candidate gets one primary stratum by precedence CORE, then AI, then MEASURE,
  then WORKFLOW. Overlaps are reported separately. Every record is inspected at most once.
- **Confirmation reserve (created before any development sampling):**
  - A PMID is reserved if `SHA-256(salt || PMID) mod 10 == 0` (about 10%), with the salt fixed and
    recorded in advance.
  - The reserve is independent of policy version.
- **Global inspected-PMID ledger (append-only):**
  - Every PMID shown to a labeller, in any policy version, stratum, round or census, is recorded
    with version, stratum, purpose and date.
  - **A PMID in the ledger is permanently ineligible for independent confirmation,** even if a later
    policy version moves it to a different stratum or expands its stratum.
- **Development samples:** 50 per stratum (fixed seed) from non-reserved, not-yet-inspected
  candidates. A stratum with 50 or fewer such records is labelled in full.
- **Confirmation (after the freeze):**
  - Up to 50 per stratum from **reserved PMIDs not in the ledger**.
  - It estimates precision for the **unseen remainder** of the stratum, and is reported that way.
  - **Minimum:** if fewer than 20 unseen reserved records remain in a stratum, no independent
    confirmation is claimed for it. The limitation is reported, and isolation is never relaxed to
    make up the number.
- **Small strata:** a stratum with fewer than 100 candidates at a given version is labelled as a
  **census**, which includes its reserved records. Those records enter the ledger. The stratum is
  reported as a census with **no independent confirmation claimed**, including in any later
  version.
- **Revision limits (preset):**
  - at most **3 policy revisions** during development (v0 to v3);
  - at most **2 confirmation rounds**, the second using only unseen reserved records;
  - a second failure escalates to Quinton;
  - **all attempts are reported**.
- **Rubric** (Quinton labels from title and abstract):

  | Label | Meaning |
  |---|---|
  | `relevant` | Directly addresses at least one approved need within D-074 scope, with usable text |
  | `partial` | On-topic (pancreas CT or imaging-AI workflow) but addresses no need directly, or only in passing |
  | `not_relevant` | Otherwise, including treatment-focused records with no need addressed |

- **Reporting:** `relevant` and `partial` counts reported **separately**, each with a 95% Wilson
  interval.
- **Proposed bar (confirmation or census):** at least 60% `relevant` + `partial`, and at least 40%
  `relevant`, per stratum. **OPEN.** These are provisional selection controls, not evidence that the
  evidence assistant is accurate or useful.

### 7.4 Need coverage

For each approved need: whether any sampled selected record was labelled `relevant` for it. Gaps are
reported.

### 7.5 Disclosure

Labelling titles and abstracts is literature inspection of this run. It happens after the needs and
seeds are frozen and is recorded in `RUNNING-LOG.md`. Prior exposure (proposal, appendix, earlier
project, planning research) is disclosed in `INFORMATION-NEEDS.md`.

## 8. Versioning

Each version records:
- policy text hash and code hash;
- MeSH version;
- input snapshot ID and cutoff;
- output PMID-list hash;
- the evaluation results above.

Versions are never overwritten. A post-freeze change creates a new corpus version under the
compatibility rules in `../QUESTION-SET-AND-EVALUATION.md` and PHASES P7.

## 9. PMC linkage (P6)

All stage-1 candidates with a PMCID are looked up, including those without an abstract.
- Eligibility comes from per-article JSON licence metadata, with OAI-PMH as corroboration.
- Unknown or conflicting rights mean no full text.
- XML text objects only.
- Bytes are frozen at retrieval (`ACQUISITION-PLAN.md` run record B).

## 10. Historical reference (not our policy)

The v2 proposal draft recorded a live PubMed query, "Pancreatic Neoplasms[MeSH] AND Tomography,
X-Ray Computed[MeSH]":
- 8,422 records;
- 6,949 with an abstract;
- about 880 in PMC OA.

That was a different route and date. It is orientation only.
