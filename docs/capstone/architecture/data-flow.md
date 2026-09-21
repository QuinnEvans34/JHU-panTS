# Data-flow architecture

**Status:** Approved architecture baseline

## 1. Training and cohort flow

```mermaid
flowchart LR
    A[Immutable source snapshot] --> B[Source adapter validation]
    B --> C[Unified manifest]
    C --> D[Identity + duplicate resolution]
    D --> E[Frozen cohort]
    E --> F[Prepared-cache version]
    F --> G[New capstone model run]
    G --> H[Immutable model version]
```

Each arrow creates or consumes a versioned artifact. A source, identity rule, cohort membership,
preprocessing, model configuration, or code change creates a new downstream derivation identity.

## 2. Autonomous inference and evaluation flow

```mermaid
flowchart LR
    CT[Full CT] --> L[Autonomous localizer]
    L --> ROI[Predicted pancreas region]
    CT --> S[Segmenter]
    ROI --> S
    S --> P[Raw source-space prediction]
    P --> M[Multi-lesion-safe processing + measurements]
    M --> CP[Case package]

    GT[Protected reference annotations] --> E[Evaluation only]
    P --> E
    M --> E
    E --> ER[Evaluation artifact]
    ER -. optional reference block .-> CP
```

The protected reference path never enters localization or segmentation. Reference information may
be included in a prepared demonstration package only as a separately labeled optional block with an
explicit reveal state.

## 3. Literature and evidence flow

```mermaid
flowchart LR
    PM[PubMed / permitted PMC] --> CM[Corpus manifest]
    CM --> PS[Stable passage records]
    PS --> IX[Versioned index]
    SF[Non-identifying structured finding] --> Q[Query builder]
    UQ[Reviewer question] --> Q
    Q --> R[Retriever]
    IX --> R
    R --> RP[Ranked passages]
    RP --> G[Cited response or refusal]
    G --> EP[Evidence response artifact]
```

No patient image, ground-truth label, source report, or direct identifier crosses into this flow.

## 4. Review flow

```mermaid
sequenceDiagram
    participant O as Operator/workflow
    participant T as File or FastAPI transport
    participant U as PROWL UI
    participant R as Review-event writer

    O->>T: Case package v1
    T->>U: Same schema and values
    U->>U: Inspect prediction and optional reference
    U->>T: Evidence question/context
    T-->>U: Evidence response with passages/citations or refusal
    U->>R: accept | edit_required | reject + prediction_id
    R-->>U: Durable review_event_id and sequence
    U->>R: Optional later revision
    R-->>U: New event superseding prior event
```

Transport does not alter the case package. A static demonstration can read the JSON directly; a
running workstation can receive the identical payload through FastAPI.

## 5. Invalidation flow

| Change | Must create a new version of |
|---|---|
| Source file/version or label repair | Source snapshot, manifest, affected cohorts and all descendants |
| Subject/study/duplicate rule | Manifest identity version, affected cohorts and descendants |
| Cohort definition/membership | Cohort and all models/predictions/evaluations trained from it |
| Preprocessing configuration/code | Prepared cache and downstream model/prediction artifacts |
| Model weights/config/code | Model version and all its predictions/evaluations/case packages |
| Inference/post-processing config | Prediction set or derived measurement version and evaluation |
| Metric definition | Evaluation artifact only; predictions may be reused if complete |
| Corpus content/chunking | Corpus, index, retrieval evaluation, evidence responses |
| Embedding/index configuration | Index, retrieval evaluation, evidence responses |
| Generation/prompt configuration | Evidence responses and response evaluation |
| UI presentation only | UI build; scientific package remains unchanged |
| Review action | New append-only event; nothing upstream invalidated |

## 6. Partial-failure flow

1. Stage writes to a temporary run-scoped location.
2. Stage validates schema, expected files, sizes/hashes, and domain-specific checks.
3. Stage atomically publishes the completion record.
4. Downstream stages accept only published complete artifacts.
5. On interruption, temporary output is quarantined or replaced; completed upstream artifacts are
   reused by identity.

The precise state machine belongs to the workflow-orchestration plan, but every component must honor
this boundary.
