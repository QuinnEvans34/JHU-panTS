# Grounded response and refusal contract

**Status:** Approved Plan 07 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Decision:** P07-01, P07-03, P07-15, and P07-16  
**Governing plan:** [`../implementation/07-literature-retrieval.md`](../implementation/07-literature-retrieval.md)

## Purpose

The response layer converts ranked literature passages into concise review context. It may improve
wording and organization; it may not create evidence, clinical conclusions, or citations. Safe
refusal/extractive display is a first-class successful behavior.

## Input boundary

The generator receives only:

- validated allowed structured context;
- validated reviewer question;
- exact final retrieved passage text/snippets allowed for processing;
- passage/source IDs and citation metadata;
- rights/display state;
- response/prompt policy; and
- non-diagnostic/refusal instructions.

It never receives patient identifiers, images, masks, source reports, labels, ground truth,
evaluation results, private paths, unrelated case-package fields, or unrestricted corpus access.

## Response states

| State | Meaning | Display |
|---|---|---|
| `answered` | Retrieved evidence directly supports the bounded question | Atomic cited claims plus limitations |
| `partially_answered` | Some required concepts supported, others absent/uncertain | Supported claims plus explicit gap |
| `insufficient_evidence` | Retrieval/corpus cannot support a safe answer | Refusal reason; optional ranked source cards |
| `out_of_scope` | Diagnosis/treatment/prognosis/private/unsupported task | Clear boundary and safe redirection |
| `conflicting_evidence` | Direct sources conflict and synthesis cannot safely resolve | Describe conflict with citations or refuse |
| `unavailable` | Corpus/index/retriever/generator failed | Honest service-unavailable state; no canned claim |

## Sufficiency gate

Run before generation. Required checks:

- query is in scope and input schema valid;
- retrieval/corpus/index identities agree;
- every candidate passage resolves and passes rights/display filters;
- minimum direct-support evidence for at least one required concept;
- development-calibrated rank/score/margin evidence;
- source diversity requirement when the claim cannot rely on one passage;
- contradiction/retraction/notice flags; and
- no prompt-injection or forbidden clinical request.

Similarity threshold is one signal, not proof. The gate emits a structured state/reasons and the
allowed evidence subset.

## Atomic claims

Each claim record contains:

- stable claim ID/order;
- one independently checkable sentence or clause;
- supporting passage IDs (one or more);
- support type (`direct`, `qualified`, `conflicting`);
- optional required-concept ID;
- post-validation support status; and
- display citation order.

A paragraph cannot hide several uncited claims under one reference. General non-diagnostic caveats
may be policy text and are identified separately from literature claims.

## Citation record

- exact passage/document/source IDs and content hashes;
- title, authors/year/journal as available;
- PMID, PMCID, DOI, and canonical NCBI/source link as available;
- section/paragraph/sentence/offset locator;
- rights/display status;
- claim IDs supported; and
- response/retrieval/index/corpus identities.

The UI can display a short allowed snippet and link. It must not substitute a different article title
or URL based on free generator output.

## Generation policy

- Keep response short and technical/general.
- Use only facts in the supplied passages.
- Preserve hedging, uncertainty, population/context, and source disagreement.
- Do not infer patient diagnosis, malignancy, stage, cause, prognosis, or treatment.
- Do not turn the PROWL model score/measurement into literature evidence.
- Do not cite a passage for a broader claim than it supports.
- Identify missing concepts rather than filling them from model memory.
- Prefer partial answer/refusal over unsupported completeness.
- Emit structured claims/citation IDs, not manually formatted bibliography strings.

Generation temperature/sampling/schema-repair behavior is pinned. Repeated generation behavior is
measured; nondeterministic variation cannot change the evidence set.

## Post-generation validation

Reject or repair only through evidence-preserving deterministic rules when:

- citation ID is not in retrieved allowed set;
- claim lacks a citation;
- citation/source does not resolve;
- forbidden patient/clinical language appears;
- response state conflicts with sufficiency gate;
- schema, length, or claim atomicity fails; or
- output exposes private path/secret/prompt/system detail.

Semantic claim-support validation combines deterministic integrity checks with the frozen human/
model-assisted rubric. An automated “grounded” judge is not treated as unquestionable ground truth.

## Safe fallback order

1. Valid structured cited response.
2. Supported subset only with explicit missing concepts.
3. Deterministic extractive passage/source cards.
4. Insufficient/out-of-scope/conflict refusal.
5. Unavailable state.

The system never falls back to an unconstrained general-purpose answer.

## Provider/model boundary

Plan 10 chooses local versus external generation after measuring environment, quality, reproducibility,
privacy, cost, and credential needs. Regardless of provider:

- public corpus passages and allowlisted non-identifying context are the only prompt data;
- request/response provider/model/version/config are recorded;
- secrets are never stored in artifacts/logs;
- provider retention/training terms are reviewed if external;
- a deterministic fixture adapter exists for tests/offline UI; and
- failure degrades to extractive/refusal, never blocks imaging review.

## Evidence-response contract

- response ID/version;
- query/retrieval/corpus/index identities;
- response state/reason codes;
- allowed structured-context summary;
- claims and citations;
- unsupported/missing/contradictory concept records;
- sufficiency and post-validation policy versions/results;
- generation provider/model/prompt/sampling identity;
- latency/tokens/cost/failure attempts as applicable;
- content hash/completion marker; and
- static/FastAPI-compatible presentation payload.

## Required tests

- every claim citation belongs to retrieved allowed set;
- invented/unknown citation rejected;
- valid citation that fails to support claim is caught by golden rubric;
- multi-claim sentence split/rejected;
- hedged source cannot support certain/broader wording;
- contradictory evidence represented/refused;
- answerable question with missing concept becomes partial;
- diagnosis/treatment/prognosis and prompt-injection refusal;
- no evidence/index/generator failure fallback order;
- secret/path/patient-field absence from prompt/log/output;
- repeat response within configured determinism expectations; and
- identical evidence-response values over file/FastAPI transport.
