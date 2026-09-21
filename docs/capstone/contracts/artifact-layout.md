# File-first artifact layout

**Status:** Architecture baseline  
**Version:** 1.0.0  
**Local root:** `outputs/prowl/` by default; configurable as `PROWL_ARTIFACT_ROOT`

File-first does not mean informal. The artifact root behaves as a versioned scientific record through
schemas, derivation hashes, content hashes, immutable published directories, and append-only review
events.

## Layout

```text
outputs/prowl/
├── sources/
│   └── <source>/<source_snapshot_id>/
│       ├── source.json
│       ├── file-inventory.jsonl
│       ├── reconciliation.json
│       └── checksums.sha256
├── manifests/
│   └── <manifest_id>/
│       ├── manifest.json
│       ├── subjects.jsonl
│       ├── studies.jsonl
│       ├── annotations.jsonl
│       ├── issues.jsonl
│       └── checksums.sha256
├── cohorts/
│   └── <cohort_id-safe>/
│       ├── cohort.json
│       ├── members.jsonl
│       ├── profile.json
│       └── checksums.sha256
├── cache/
│   └── <preprocessing-derivation-sha256>/
│       ├── cache.json
│       └── cases/<study-token>/...
├── workflows/
│   └── <run_id-safe>/
│       ├── run.json
│       ├── resolved-config.yaml
│       ├── logs/
│       ├── state/
│       └── COMPLETE.json | FAILED.json
├── models/
│   └── <model_version_id-safe>/
│       ├── model.json
│       ├── checkpoints/
│       ├── resolved-config.yaml
│       ├── environment.json
│       └── checksums.sha256
├── predictions/
│   └── <prediction_set_id>/
│       ├── prediction-set.json
│       └── studies/<study-token>/
│           ├── prediction.json
│           ├── pancreas.nii.gz
│           ├── lesion.nii.gz
│           ├── probabilities/...
│           └── checksums.sha256
├── evaluations/
│   └── <evaluation_id-safe>/
│       ├── evaluation.json
│       ├── summary.json
│       ├── per-study.jsonl
│       ├── per-lesion.jsonl
│       ├── operating-points.jsonl
│       └── checksums.sha256
├── retrieval/
│   ├── corpora/<corpus_id-safe>/...
│   ├── indexes/<index_id-safe>/...
│   ├── retrieval-runs/<run_id-safe>/...
│   └── evaluations/<evaluation_id-safe>/...
├── case-packages/
│   └── <case_package_id-safe>/
│       ├── case-package.json
│       ├── files/...
│       └── checksums.sha256
├── reviews/
│   ├── events/review-events.jsonl
│   ├── snapshots/<snapshot-sha256>/review-events.jsonl
│   └── indexes/current-by-case.json
└── releases/
    └── <release_id>/
        ├── release.json
        ├── checksums.sha256
        └── permitted-artifacts/...
```

Colons and other unsafe ID characters are replaced only in directory tokens. The canonical ID remains
inside the controlling JSON record.

## Format policy

| Need | Baseline format | Reason |
|---|---|---|
| Typed control/single record | JSON validated by schema | Portable across Python, FastAPI, and React |
| Record collection/event stream | JSONL with per-record schema | Streamable, appendable, diffable in small samples |
| Human spreadsheet export | CSV generated from canonical records | Convenient inspection; not authoritative when types/nesting matter |
| Configuration | YAML plus resolved hash/JSON-compatible interpretation | Matches current project while preserving exact resolved values |
| Volumetric image/label | NIfTI (`.nii.gz`) | Preserves medical-image affine and spacing |
| Local prepared array/cache | Implementation selected by Plan 10 | Performance choice; controlled by cache manifest |
| Model checkpoint | Framework-native binary plus model manifest/checksum | Required for loading while keeping lineage outside opaque bytes |
| UI package | JSON control record plus relative file references | Same package can be read from disk or HTTP |

## Publication protocol

1. Resolve input artifact IDs/hashes and configuration.
2. Compute derivation key and choose the run-scoped temporary directory.
3. Write all output beneath that temporary directory.
4. Validate schema and domain constraints.
5. Compute content hashes and `checksums.sha256`.
6. Atomically publish the completed directory or completion record.
7. Downstream components consume only published complete artifacts.

A failed/interrupted attempt remains under workflow state or quarantine. It is never discovered as a
valid artifact by scanning for filenames alone.

## Immutability rules

- Published source, manifest, cohort, cache-version, model, prediction, evaluation, corpus, index,
  case-package, and release directories are immutable.
- `workflows/<run>/run.json` may be atomically replaced while the run is active. At a terminal state it
  is frozen and accompanied by `COMPLETE.json` or `FAILED.json`.
- `reviews/events/review-events.jsonl` is an append-only container. Individual event records are
  immutable. Release or analysis uses a content-hashed snapshot.
- Convenience pointers such as `latest` or `current-by-case.json` are never authoritative and never
  appear as scientific lineage inputs.

## Relative references

Contract fields use one of:

- an artifact ID resolved through the artifact root;
- a URI below a declared base: artifact references are relative to the artifact root, while package
  payload and run-support files are relative to their controlling directory;
- a `root_alias` plus source-relative path for immutable external data.

No contract stores `/Users/...`, `/Volumes/...`, a Windows drive letter, or another machine-specific
absolute path as scientific identity. Contract URIs cannot contain `..` path segments.

## Retention classes

- **Source/keeper:** retain and back up with checksum.
- **Release evidence:** retain with the release manifest.
- **Reproducible derived:** may be removed after its recipe and upstream keepers are verified.
- **Exploratory:** retain until experiment decision and documentation are complete.
- **Partial/quarantined:** retain briefly for debugging, then remove through an explicit cleanup list.
- **Review events:** retain append-only; create periodic snapshots.

## Database migration boundary

If D-211 is triggered, a database may index or persist the same logical records. The file contracts
remain export/import and release formats. Voxel arrays remain file/object artifacts. A database is an
implementation of the contract, not a new source of meaning.

## Transition from current outputs

- Existing `outputs/manifest.csv`, split files, checkpoints, evaluations, and UI case files remain
  historical artifacts.
- They are not moved or relabeled as conforming.
- New adapters may ingest them into a capstone artifact version after validation.
- No historical artifact is overwritten during transition.
