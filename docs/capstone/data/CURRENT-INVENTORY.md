# Current data and cohort inventory

**Audited:** 2026-09-08  
**Purpose:** Record observed inputs and hazards before Plan 02 implementation  
**Important:** These are current/historical files, not automatically conforming capstone artifacts.

## September 18 recovery update

The old `JHU-PanTS` data volume is unavailable and Quinton accepts fresh source acquisition on the new
`PROWL-Data` drive. Its recovery is optional. Rechecking the local manifest and accepted base train,
validation, and test lists produced exactly the four hashes below. These controls survive on the
laptop and provide the comparison target for a pinned replacement snapshot. Counts/IDs alone cannot
prove raw CT/label equivalence; any source change must be versioned and reconciled before training.

## PanTS manifest

Observed `outputs/manifest.csv`:

| Property | Observed value |
|---|---:|
| Rows / columns | 9,901 / 29 |
| Publisher train-folder studies | 9,000 |
| Publisher test-folder studies | 901 |
| Unique `case_id` | 9,901 |
| Unique fallback `patient_id` | 9,901 |
| Duplicate `case_id` | 0 |
| Lesion positive / negative | 1,033 / 8,868 |
| Absolute CT/pancreas/lesion paths | 9,901 / 9,901 / 9,901 |
| SHA-256 | `16bfb945a7cdd8f8296e5712f7e71fb71ad7936cd5fe4eb7bb1affaebbc31554` |

The source metadata did not provide a patient/subject/PID column when the manifest was built. The
legacy builder therefore copied `case_id` into `patient_id`. Plan 02 will preserve the usable grouping
while naming its assurance honestly: study-as-subject fallback, not confirmed biological identity.

The external PanTS drive was not mounted during this audit. Raw file presence, publisher metadata,
and raw-source checksums must be revalidated during implementation before a complete source snapshot
is published.

## Accepted base membership inputs

These current files are pairwise disjoint and their union covers all 9,901 manifest studies:

| File | Count | SHA-256 | Migration role |
|---|---:|---|---|
| `outputs/splits/train.txt` | 7,200 | `bfc827ac52346e4636ed3a58581d5f55a9f1e80983bbfd6228c928babd519fc8` | Reproduce as capstone train v1 |
| `outputs/splits/val.txt` | 1,800 | `57549ba515b4d4f3297556a12e8e7c7df43a1f06de0c2f8296b4e5f16c87d2b1` | Reproduce as capstone validation v1 |
| `outputs/splits/test.txt` | 901 | `7a323774be8c4459024f6e26113b84a4f892f52c954f42c3d033234e1e7b338e` | Reproduce as capstone test v1 |

The count/hash allowlist is a migration control. It does not make the legacy file format canonical.

## Historical child-list audit

| File | Count | Outside accepted train | Validation overlap | Treatment |
|---|---:|---:|---:|---|
| `dev_subset.txt` | 100 | 0 | 0 | Historical clean child; may be imported only through explicit registration |
| `scaled300.txt` | 300 | 54 | 54 | Contaminated historical evidence; forbidden for capstone training |
| `scaled300_clean.txt` | 300 | 0 | 0 | Historical corrected child; not canonical until explicitly migrated |
| `scaled600.txt` | 600 | 109 | 109 | Contaminated historical evidence; forbidden for capstone training |
| `scaledmax.txt` | 1,412 | 266 | 266 | Contaminated historical evidence; forbidden for capstone training |
| `scaledmax_clean.txt` | 1,412 | 0 | 0 | Historical corrected child; not canonical until explicitly migrated |

The contaminated files remain in place because old experiment results depend on them. Their presence
is why the new consumer must require a registered `cohort_id`, parent hash, and protected role rather
than accepting any list under `outputs/splits/`.

Several 20-study exploratory lists (`clarity20`, `nc20`, `pv20`, and `repr20`) also contain a mixture
of accepted train and validation membership. Their interpretation belongs to the preceding project's
experiment history. None is an eligible capstone training cohort without a new, explicit migration
and purpose review.

## PANORAMA metadata

The expanded source-specific audit, including current file hashes, annotation strata, anomalies, and
source gaps, is in [`PANORAMA-INVENTORY.md`](PANORAMA-INVENTORY.md).

Observed local `clinical_information.xlsx`:

| Property | Observed value |
|---|---:|
| Rows / columns | 2,238 / 8 |
| Unique study IDs | 2,238 |
| Unique patient IDs | 2,224 |
| Patients with multiple studies | 11 |
| Studies belonging to those patients | 25 |
| Maximum studies from one patient | 5 |
| Declared imported studies | 274 |
| Eligible after declared-import removal | 1,964 studies / 1,950 patients |
| Eligible PDAC studies | 578 |
| Patient spanning imported and eligible groups | 0 |
| SHA-256 | `2ae925de8067600db62e186a91844dec6555dab2b17cafd33b886b8c99f19ea7` |

Columns are `PANORAMA_patient_id`, `PANORAMA_study_id`, `anonymized_study_date`, `patient_age`,
`patient_sex`, `scanner`, `label`, and `level`.

Observed missingness:

- date: 194;
- age: 274;
- sex: 274;
- scanner: 276;
- patient ID, study ID, label, and reference-standard level: 0.

Most demographic missingness corresponds to the 274 declared imports, but the two additional scanner
gaps require an explicit source issue rather than imputation. Plan 03 will revalidate these counts
against pinned label/image snapshots before any training eligibility is declared.

## Source control gaps to close

- Pin PanTS source version/retrieval record and raw inventory assurance.
- Pin PANORAMA labels repository commit and imaging archive versions/checksums.
- Move local source references behind root aliases without changing their bytes.
- Record licenses, citation requirements, and non-commercial restrictions in source snapshots.
- Replace legacy absolute paths with root-alias plus source-relative paths in emitted study records.
- Separate publisher source partition from PROWL protected role.
