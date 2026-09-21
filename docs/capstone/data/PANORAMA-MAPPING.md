# PANORAMA mapping and annotation-use specification

**Status:** Approved Plan 03 design baseline  
**Version:** 0.1 planning draft  
**Owner:** Quinton Evans  
**Governing plan:** [`../implementation/03-panorama-integration.md`](../implementation/03-panorama-integration.md)

This specification defines what the PANORAMA adapter is allowed to infer. It deliberately separates
source diagnosis, voxel class, annotation method, and permitted downstream use.

## Identity mapping

| Source field | Canonical field | Rule |
|---|---|---|
| `PANORAMA_patient_id` | `subject_id` | `panorama:subject:<exact-source-value>` |
| `PANORAMA_study_id` | `study_id` | `panorama:study:<exact-source-value>` |
| `PANORAMA_study_id` | image/label join key | Exact string match only; no fuzzy identity join |
| workbook row | study membership | Exactly one row per source study; duplicates fail |

Age, sex, scanner, and study date never participate in identity. They may support descriptive
profiles or candidate review but may not merge subjects across sources.

## Target-status mapping

| Source evidence | Canonical target | Status | Method | Reason |
|---|---|---|---|---|
| `label=PDAC` | `pdac` | positive | `reference_standard` | Direct source classification with `level` retained as evidence |
| `label=PDAC` | `pancreatic_lesion` | positive | `explicit_mapping` | PDAC is a pancreatic lesion subtype |
| `label=non-PDAC` | `pdac` | negative | `reference_standard` | Direct source classification with `level` retained as evidence |
| `label=non-PDAC` | `pancreatic_lesion` | unknown | `unavailable` | Absence of PDAC does not establish absence of every lesion type |

The mapping is intentionally asymmetric. Code must not implement it as `has_lesion = label ==
"PDAC"`, because that expression falsely converts every other row to a generic negative.

For a `pancreatic_lesion=unknown` record, the schema requires `method=unavailable` and a null
reference. The source `non-PDAC` evidence remains separately present under the `pdac` target.

## Raw voxel mapping

Historical real-file evidence supplies the following source legend; the complete pinned archive must
confirm that no other values occur.

| Raw value | Source meaning | Canonical three-class target | Structure-level record |
|---:|---|---:|---|
| 0 | Background | 0 background | None |
| 1 | PDAC lesion | 2 lesion | `structure=lesion`, `source_structure=PDAC` |
| 2 | Veins | 0 background for v1 target | Preserve only in raw-source provenance |
| 3 | Arteries | 0 background for v1 target | Preserve only in raw-source provenance |
| 4 | Pancreas parenchyma | 1 pancreas | `structure=pancreas`, `source_structure=pancreas_parenchyma` |
| 5 | Pancreatic duct | 0 background for v1 target | Preserve only in raw-source provenance |
| 6 | Common bile duct | 0 background for v1 target | Preserve only in raw-source provenance |

The initial derived mapping ID should be semantic and versioned, for example
`panorama-level45-v1`. Its canonical configuration includes source values, output values, paint
order, interpolation, crop-source values, and transform version; the full canonical configuration
hash is recorded in every derived artifact.

### Paint and crop rules

- Build binary pancreas from raw value 4 and binary lesion from raw value 1.
- Compose pancreas first and lesion second. Lesion therefore wins if future source/repair layers
  overlap even though the original source mask is mutually exclusive.
- Build the training crop from the physical bounding box of raw values `{1,4}` plus the configured
  margin. Using value 4 alone could omit tumor tissue that replaces parenchyma.
- An import-clean PDAC study with no value 1 is quarantined as an outcome/mask conflict.
- A non-PDAC study containing value 1 is also quarantined as an outcome/mask conflict; the adapter
  does not decide whether the metadata, directory, or voxel content is correct.
- A pancreas annotation allowed as a crop/training target must contain value 4 or have an explicit
  adjudicated repair. Empty structures never silently become background.
- Derived labels use integer storage and nearest-neighbor spatial interpolation.
- Source files remain immutable and independently hashable.

## Metadata preservation

| Source field | Treatment |
|---|---|
| `anonymized_study_date` | Parse when valid; preserve null; derive year only from valid date |
| `patient_age` | Preserve source string and optionally derive integer years through a versioned parser |
| `patient_sex` | Preserve source value; normalize only into a separate derived field |
| `scanner` | Preserve raw string; derive manufacturer separately; null and `0` remain named issues |
| `label` | Preserve verbatim and map only through the target-status table above |
| `level` | Preserve verbatim as evidence; `MSD_dataset`/`NIH_dataset` also trigger exclusion |

Missing demographic/acquisition fields do not affect subject identity or turn outcomes negative.

## Annotation provenance

PANORAMA stores several semantic structures in one physical file. The adapter emits separate logical
annotation records that may reference the same source bytes.

### Lesion record

- `method=human_manual` only when the study appears in the pinned archive's manual directory and the
  source evidence supports a lesion delineation.
- `method=machine_generated` when it appears in the automatic directory.
- Manual/automatic classification comes from the pinned archive inventory, not the current derived
  text file.
- The three clean manual/non-PDAC records begin quarantined because directory placement and source
  diagnosis conflict with the expected rule.

### Pancreas record

- `method=machine_generated` for all PANORAMA pancreas masks unless a later source-specific record
  proves otherwise.
- It never inherits the lesion record's manual method merely because both values share one NIfTI.
- Under approved P03-04, project verification may authorize `crop_reference` and `training_target`;
  it never authorizes headline `evaluation_reference`.

## Machine-pancreas quality audit

Machine masks cannot become expert ground truth through visual inspection. The audit answers the
narrower operational question: are they internally valid enough to define a training crop and be
used as disclosed silver-standard supervision?

### Automated checks on every candidate study

- NIfTI decodes and contains only the permitted value set.
- CT and mask shapes/affines/orientations reconcile under the source contract.
- Image intensities are finite and geometry values are physically valid.
- Pancreas value 4 is nonempty.
- PDAC-positive studies contain lesion value 1.
- The `{1,4}` union crop contains every lesion voxel and the configured physical margin.
- Pancreas/lesion volumes, crop dimensions, and boundary contact are reported; outliers are flagged,
  not silently deleted.

### Visual audit

Review at least 30 CT/mask overlays, including:

- at least 10 expert-PDAC studies;
- at least 10 automatic-PDAC studies;
- at least 10 non-PDAC studies;
- every clean manual/non-PDAC anomaly;
- at least one study from each of the 11 repeated-subject families;
- representation across observed scanner/manufacturer groups where available.

The categories may overlap. Record reviewer, snapshot IDs, study IDs, overlay artifact IDs, visible
coverage/cropping defects, and disposition. Any systematic defect expands the audit to the affected
stratum and blocks allowed-use promotion until resolved.

### Promotion rule

Promote only annotations that pass automated validation and do not belong to a failed/unresolved
quality stratum. Promotion creates a new annotation/manifest version; it does not mutate earlier
records. A failed mask is quarantined or assigned a narrower allowed-use set.

## Eligibility matrix

| Study/annotation state | Source pool | Primary expert arm | Optional machine arm | Pancreas-only work |
|---|:---:|:---:|:---:|:---:|
| Declared NIH/MSD import | Recorded/excluded | No | No | No |
| Clean manual PDAC, checks pass | Yes | Yes | Not needed | Yes |
| Clean automatic PDAC, checks pass | Yes | No | Yes, explicitly named | Yes |
| Clean non-PDAC | Yes | No generic-lesion negative use | No generic-lesion negative use | Yes, only where lesion loss is not inferred negative |
| Manual/non-PDAC anomaly | Quarantined | No | No | Only after adjudication |
| Missing/mismatched/invalid file | Quarantined | No | No | No |
| Unresolved cross-source duplicate | Quarantined | No | No | No |

Because clean non-PDAC rows remain generic-lesion unknown, they cannot be passed through a standard
three-class loss that interprets absent lesion voxels as confirmed negatives. A future PDAC-specific
auxiliary task or partial-label loss requires its own Plan 06 decision and test.

## Required fixtures

- Synthetic mask containing every value 0–6.
- Synthetic overlap composition proving lesion paint precedence.
- PDAC metadata with expert lesion/machine pancreas provenance.
- non-PDAC metadata proving `pdac=negative` and `pancreatic_lesion=unknown` coexist.
- Unknown raw value causing a blocking failure.
- PDAC-positive metadata with no lesion voxels causing quarantine.
- non-PDAC metadata with lesion voxels causing quarantine.
- Empty pancreas and crop-edge lesions causing quarantine/flagging.
- Manual/non-PDAC anomaly requiring adjudication.
- Two studies under one subject proving identity is not study-derived.

Real-file checks are local/licensed and must record snapshot IDs. Synthetic/golden metadata fixtures
may be committed if they contain no source voxel data or identifying information.
