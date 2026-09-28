# Seed set

**Status:** PROPOSED protocol, revision 3 (second Codex review, 2026-09-28). Two starter candidates,
unverified. **Not frozen.**
**Purpose:** papers we already know belong in Tier 1, fixed before the selection policy runs. A missed
seed is objective evidence of a sensitivity gap (the known-item check from systematic-review search
design).

## Rules

1. **Independent of the selection policy.** Candidates come from citation-based sources, not from
   running our own query terms:
   - references in the approved proposal and appendix;
   - reference lists of the starter seeds and of the PanTS, PANORAMA and Medical Segmentation
     Decathlon papers (citation chaining);
   - papers Quinton has read;
   - stakeholder or librarian suggestions.
2. **Assisted discovery, then review.**
   - Claude proposes candidates, each with its source of knowledge.
   - Quinton reviews: accept, reject or add.
   - Quinton is not expected to supply all candidates alone.
   - Citation chaining is literature inspection. It is disclosed in `RUNNING-LOG.md`, and it happens
     before this selection run's results exist.
3. **Verified identifiers only.**
   - A candidate becomes a seed only after its PMID (or its DOI mapped to a PMID) resolves in the
     **final baseline-plus-updates snapshot** (P5), after deletions and replacements are applied.
   - No recalled-from-memory identifiers. No copied abstracts.
   - Verification uses local data, so no live lookup is needed.
4. **Frozen before the first selection run** (start of P6), with the list's SHA-256 recorded in
   `RUNNING-LOG.md`. Later additions are reported separately and do not count toward that version's
   recall.
5. **Coverage target:** 15-25 seeds, at least two per question family, mixing study types.
6. **Actual MeSH absence, not year or status.** To test missing-MeSH handling, include **at least
   three seeds whose final-snapshot record has no MeSH headings** (the `MeshHeadingList` is absent
   or empty). Verify this directly in P5.
   - `MedlineCitation/@Status` is recorded as context only. Non-MEDLINE status alone is not the test
     condition.
   - A recent publication year is not evidence either.
7. **Only PubMed-indexed works count toward seed recall.** arXiv and Zenodo references are listed
   separately.
8. **Negative seeds (optional)** must be genuinely outside the policy: records that fail the
   candidate logic, or hit a hard exclusion rule, in `SEARCH-AND-SELECTION.md`. Examples:
   - an animal-only study;
   - an editorial;
   - an imaging-AI paper on a non-pancreatic organ without the WORKFLOW terms.

   **Treatment-focused pancreas CT papers are not negative seeds.** The current rules do not
   exclude them by design; precision sampling measures them.
9. **Prior exposure disclosed.** The project has already inspected literature (proposal, appendix,
   earlier project, planning research). The defensible rule is that seeds and needs are frozen
   before inspecting **this run's** results, not that nobody has read anything.

## Seed record fields

| Field | Meaning |
|---|---|
| `seed_id` | S-01, S-02, ... |
| `citation` | Authors, year, title, venue |
| `identifier` | PMID (verified) and/or DOI |
| `families / needs` | Families 1-5 and need IDs |
| `source_of_knowledge` | Where it came from |
| `proposed_by / reviewed_by / date` | Claude or Quinton; review outcome |
| `verification` | `unverified`, `resolves_in_local_baseline`, `not_in_pubmed` |
| `indexing_status` | `MedlineCitation/@Status` in the final snapshot (context) |
| `mesh_present` | Whether MeSH headings exist in the final snapshot (the missing-MeSH test condition) |
| `expected_branch` | Predicted branch (CORE, AI, MEASURE, WORKFLOW), recorded before the run |

## Starter candidates (from approved appendix v3.1; unverified)

| ID | Citation | Identifier | Families | Source | Verification |
|---|---|---|---|---|---|
| S-01 | Suman, G., Patra, A., Korfiatis, P., et al. (2021). Assessment of pancreatic ductal adenocarcinoma using CT imaging. | PMID 33840636 (per appendix) | 1, 2 | Appendix v3.1 key references | unverified |
| S-02 | Artificial Intelligence in Pancreatic Imaging: A Systematic Review. *United European Gastroenterology Journal*, 2025. | PMID 39865461 (per appendix) | 4 | Appendix v3.1 A6 example record | unverified |

Current coverage: family 1 (S-01), family 2 (S-01), family 4 (S-02). Families 3 and 5 have no
candidates yet.

## References outside PubMed seed recall

| Reference | Status |
|---|---|
| Antonelli, M., et al. (2022). The Medical Segmentation Decathlon. *Nat Commun* 13, 4128. doi:10.1038/s41467-022-30695-9 | May be PubMed-indexed. Becomes a seed only if its DOI maps to a PMID in the local baseline |
| Li, W., et al. (2025). PanTS. arXiv:2507.01291 | Not a PubMed seed; used for citation chaining |
| Alves, N., et al. (2024). PANORAMA protocol. Zenodo doi:10.5281/zenodo.10599559 | Not a PubMed seed; used for citation chaining |

## Next steps

1. **P2:** Claude proposes candidates by citation chaining (disclosed). Quinton reviews.
2. **P5:** verify identifiers and MeSH presence against the final baseline-plus-updates snapshot.
3. **P6 start:** freeze and record the hash.
