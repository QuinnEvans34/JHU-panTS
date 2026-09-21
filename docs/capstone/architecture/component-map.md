# Component architecture

**Status:** Approved architecture baseline  
**Style:** File-first components connected through versioned contracts

## Component view

```mermaid
flowchart LR
    subgraph Sources
        PS[PanTS adapter]
        PA[PANORAMA adapter]
        PL[Literature collector]
    end

    subgraph Control[Identity and control plane]
        CAT[Source catalog]
        ID[Identity + provenance resolver]
        CO[Protected cohort builder]
        OR[Workflow runner]
    end

    subgraph Imaging
        PRE[Preprocess/cache builder]
        LOC[Pancreas localizer]
        SEG[Pancreas/lesion segmenter]
        MEAS[Post-process + measurements]
        EV[Evaluation]
    end

    subgraph Evidence
        COR[Corpus normalizer]
        IDX[Retrieval index]
        RET[Retriever]
        GEN[Cited response / refusal]
        REV[Retrieval evaluation]
    end

    subgraph Review
        PKG[Case-package assembler]
        API[File/FastAPI adapter]
        UI[React + NiiVue workspace]
        RR[Review event writer]
    end

    subgraph Artifacts
        FS[(Versioned artifact store)]
    end

    PS --> CAT
    PA --> CAT
    CAT --> ID --> CO
    CO --> PRE
    PRE --> LOC --> SEG --> MEAS --> EV
    PL --> COR --> IDX --> RET --> GEN
    IDX --> REV
    GEN --> REV
    MEAS --> PKG
    EV --> PKG
    GEN --> PKG
    PKG --> API --> UI --> RR
    OR -. coordinates .-> CAT
    OR -. coordinates .-> PRE
    OR -. coordinates .-> LOC
    OR -. coordinates .-> SEG
    OR -. coordinates .-> EV
    OR -. coordinates .-> COR
    OR -. coordinates .-> REV
    CAT --> FS
    CO --> FS
    PRE --> FS
    LOC --> FS
    SEG --> FS
    MEAS --> FS
    EV --> FS
    COR --> FS
    IDX --> FS
    REV --> FS
    PKG --> FS
    RR --> FS
```

## Ownership table

| Component | Owns | Consumes | Produces |
|---|---|---|---|
| Source adapters | Source-specific parsing and validation | Immutable source snapshot | Source records, annotations, reconciliation issues |
| Identity/provenance resolver | Canonical subject/study/annotation identity | Source records | Unified manifest records |
| Protected cohort builder | Membership, ancestry, disjointness, freeze | Unified manifest + cohort definition | Frozen cohort package |
| Workflow runner | Stage order, state, retries, lineage | Stage definitions + configuration | Run manifest, logs, completion/failure state |
| Preprocess/cache builder | Shared deterministic imaging preparation | Study/annotation + preprocessing config | Versioned prepared arrays and transform record |
| Pancreas localizer | Autonomous region proposal | Full CT/preprocessed full-volume representation | Predicted pancreas region and confidence |
| Segmenter | Pancreas/lesion probability and label output | Predicted region + image | Prediction volumes |
| Post-process/measure | Multi-lesion-safe cleanup and measurements | Prediction volumes + spacing/affine | Components, volume, diameter, score inputs, warnings |
| Evaluation | Metric definitions and matched comparisons | Frozen cohort + prediction set + labels | Versioned evaluation report/data |
| Corpus normalizer | Allowed text/source identity and chunking | PubMed/PMC records/text | Corpus and passage records |
| Retrieval index | Embedding/index construction | Corpus + index config | Rebuildable versioned index |
| Retriever | Query construction and ranking | Structured finding/question + index | Ranked passage records |
| Response/refusal | Evidence-limited wording | Ranked passages | Cited response or refusal |
| Retrieval evaluation | Recall/rank/grounding/refusal measurement | Frozen question set + retrieval/responses | Evaluation report |
| Case-package assembler | UI-facing scientific package | Prediction, measurement, optional reference/evidence | Case package conforming to one schema |
| File/FastAPI adapter | Transport only | Case package/review event | Identical JSON payload over disk or HTTP |
| Review workspace | Inspection and human action | Case package, evidence response | Review-event request |
| Review event writer | Append-only review history | Validated review event | Durable immutable event plus snapshot/index |

## Separation rules

- The workflow runner coordinates components but does not contain scientific logic.
- FastAPI validates/transmits contracts but does not create a second prediction schema.
- The UI renders measurements and evidence but does not recompute scientific metrics.
- Evaluation may use reference labels; autonomous inference may not.
- Review events reference predictions; they never modify prediction artifacts.
- File storage is the baseline. Any database later implements the same logical records rather than
  redefining them.
