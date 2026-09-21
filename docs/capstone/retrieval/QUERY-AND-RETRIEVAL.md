# Query and retrieval contract

**Status:** Approved Plan 07 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P07-03 and P07-09 through P07-12  
**Governing plan:** [`../implementation/07-literature-retrieval.md`](../implementation/07-literature-retrieval.md)

## Purpose

This contract turns a bounded non-identifying review question into inspectable lexical/vector ranks.
It keeps query creation deterministic, records every filtering/ranking decision, and prevents a
retrieval library from becoming the evidence authority.

## Inputs

### Structured finding

Allowed fields:

- modality/anatomy/task enums;
- selected-prediction finding state;
- coarse lesion count/size bin when valid;
- allowlisted localization/geometry/model warning category; and
- selected case-score band only after D-208, labeled non-diagnostic.

Forbidden fields:

- patient/source case identifiers, dates, institution/site, private paths;
- image, probability, mask, label, or report content;
- ground truth/evaluation result;
- diagnosis, subtype, stage, prognosis, treatment, or unvalidated morphology; and
- arbitrary case-package keys.

### Reviewer question

Validate length, language, control characters, prompt-injection/out-of-scope patterns, and allowed
question family. Preserve original validated wording in the query record. Do not silently rewrite a
diagnosis/treatment question into an answerable one; refuse it.

## Canonical query record

- query ID/version;
- structured-finding schema/version and allowed values;
- original validated reviewer question;
- normalized lexical query tokens/phrases;
- dense query text/template version;
- MeSH/synonym expansions and their source/version;
- filters (source type, language, rights/display, date/topic);
- corpus/index/retriever versions;
- top-k/candidate/fusion/rerank settings;
- hash of canonical content; and
- timestamp/run identity.

Same input and query policy must produce the same query identity before nondeterministic provider
behavior is considered.

## Query construction

1. Validate scope and structured fields.
2. Normalize whitespace/case only as configured; retain the original.
3. Map allowed enums to controlled search terms.
4. Add versioned pancreas/CT/segmentation/review synonyms or MeSH terms relevant to the family.
5. Keep negation and question intent.
6. Construct lexical and dense text separately; record both.
7. Apply rights/display/source filters explicitly.
8. Do not inject model score as evidence or a diagnostic premise.

Question expansion is rules/configuration initially. LLM query rewriting is optional later and must
be versioned/evaluated against the deterministic baseline.

## Retrieval channels

### Lexical

- Search passage text plus configured title/section/MeSH/keyword fields.
- Record raw score/rank and exact query representation.
- Deterministic tokenization/stemming/stopwords and field weights.
- Serves as the control and fallback.

### Dense

- Embed the configured dense query representation with the same pinned embedding family as passages.
- Record query vector identity/model/hash, normalization, distance/similarity metric, raw score/rank.
- Apply metadata filters in a documented pre/post stage and record exclusions.
- Prefer exact search for a small corpus unless measured latency requires approximate indexing.

### Hybrid/rerank

- Retrieve bounded lexical and dense candidate pools independently.
- Preserve both channel ranks/scores.
- Fuse using a deterministic recorded rule such as reciprocal-rank fusion or normalized score fusion.
- Optional cross-encoder/LLM reranking is a separate version/experiment and cannot erase base ranks.
- Apply per-document passage cap and stable tie-break to improve source diversity.

## Metadata filters

Minimum filters:

- rights permits local retrieval and requested display mode;
- not quarantined/excluded/retracted under the selected policy;
- source/document/passage belongs to exact corpus/index;
- question-family/source-type boundary; and
- language/version compatibility.

Filters are semantic policy, not a vector-store convenience. The same policy must be implementable in
every D-202 candidate or enforced and tested in the retriever adapter.

## Ranked passage record

For every candidate/final item:

- passage/document/source IDs and exact locator;
- corpus/index/query/retriever IDs;
- lexical/dense/rerank/fusion ranks and scores, including absent-channel state;
- applied filters and exclusion reason;
- duplicate/source-cap effect;
- final rank and stable tie-break;
- rights/display status;
- text/content hash and allowed snippet/local reference; and
- retrieval latency/timestamp/run.

The response receives only the final eligible ranked set. Evaluation retains full candidate evidence.

## Determinism and tolerance

- Lexical indexing/ranking is expected deterministic under one environment/config.
- Embeddings must reproduce within a validated numerical tolerance; vector row/passage mapping and
  top-k fixture ordering must be stable under that tolerance.
- Equal scores use stable passage ID tie-break.
- Approximate indexes require measured recall against exact search and fixed build seed/settings.
- Library upgrade creates a new index/retriever version unless compatibility is proven.

## Failure behavior

| Condition | Behavior |
|---|---|
| Invalid/out-of-scope query | Refusal before index access |
| Missing/corrupt index | `evidence_unavailable`; optional lexical fallback if it is valid and named |
| Empty eligible result | `insufficient_evidence` |
| Only rights-ineligible passages | Filtered/refused; no hidden display |
| Dense channel fails | Named lexical fallback; response/evaluation records degraded path |
| Lexical channel fails | Dense-only allowed only if predeclared and valid; otherwise unavailable |
| Reranker fails | Use preserved base hybrid/lexical/vector rank if policy allows |
| Corpus/index mismatch | Hard failure; never coerce IDs |

## Required tests

- allowlisted fields accepted and each forbidden field rejected;
- deterministic query identity and synonym/MeSH expansion;
- negation/out-of-scope intent preserved;
- known exact-term lexical and semantic-paraphrase dense fixtures;
- rights/retraction/topic filter enforcement across candidate stores;
- lexical/dense component ranks preserved after fusion;
- duplicate passage/source cap and tie-break determinism;
- vector/passages row mapping and dimension mismatch rejection;
- approximate-versus-exact recall gate where applicable;
- empty/corrupt/channel-failure fallback states; and
- same contract/output fields from file and FastAPI adapters.
