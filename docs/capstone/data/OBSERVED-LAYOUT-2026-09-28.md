# Observed source layout — PanTS and PANORAMA

**Status:** Provisional structural record; downstream quality conclusions require validation.

> September 28 Codex review: preserve the observations below as recorded, but do not
> treat compressed-size interpretations, inferred field of view, or the proposed lack
> of pancreatic exclusions as established findings. See
> [review corrections and integrity evidence](../operations/EXTRACTION-REVIEW-2026-09-28.md).
**Observed:** 2026-09-27 / 2026-09-28
**Scope:** Structural observation of file trees plus the PANORAMA clinical metadata. No NIfTI
header, no voxel, and no image content was read.

This is the artifact Plans 02, 03 and 05 are written against. Before it existed, the layout of
this data was an assumption inherited from the previous project and a different drive.

## What this establishes, and what it does not

**Establishes:** directory structure, identifier formats and their rules, file inventories per
case, cross-source identifier relationships, the train/test boundary, and the composition of the
PANORAMA annotation classes.

**Does not establish:** geometry, spacing, orientation, label semantics, voxel content, mask
emptiness, annotation quality, patient uniqueness, subject overlap between sources, or source
eligibility. Those belong to Plans 02, 03 and 05 and require reading image data.

Source aliases remain `null` and `scientific_runs_enabled` remains `false`.

## Evidence

| Artifact | Path |
|---|---|
| Inventory record | `outputs/prowl/inventory-2026-09-27/full-v4.json` |
| Generated digest | `outputs/prowl/inventory-2026-09-27/OBSERVED-LAYOUT-v4.md` |
| Extraction receipts | `outputs/prowl/extraction-2026-09-22/{pants,panorama,pilot-*}.jsonl` |
| Tool | `scripts/diagnostics/inventory_sources.py` @ sha256 `1010d0390c0a203f…` |

Extraction completed 15 of 16 archives: 300,608 files, 565,327,340,747 bytes, 4.68 hours. Every
PanTS archive matched its pinned SHA-256; every PANORAMA member passed CRC-32 and its declared
size. `PanTSMini_ImageTe` is deliberately unextracted.

The generated digest is tool output. **This document is the reviewed record**; where they differ,
this one is authoritative because a human read it.

## PanTS

| Source | Cases | Files | Bytes |
|---|---:|---:|---:|
| `pants-labels` | 9,901 | 287,128 | 52,020,675,883 |
| `pants-images` | 9,000 | 9,000 | 317,614,413,856 |

**Layout.** Directory per case. Images are `PanTS_########/ct.nii.gz`, one file per case, median
34,406,388 bytes. Labels are `PanTS_########/` containing `combined_labels.nii.gz` plus a
`segmentations/` directory of 28 individual structures — 29 files per case.

**The 28 structures.** `pancreas`, `pancreas_head`, `pancreas_body`, `pancreas_tail`,
`pancreatic_duct`, `pancreatic_lesion`, `common_bile_duct`, `celiac_artery`,
`superior_mesenteric_artery`, `aorta`, `postcava`, `veins`, `liver`, `spleen`, `stomach`,
`duodenum`, `colon`, `gall_bladder`, `kidney_left`, `kidney_right`, `adrenal_gland_left`,
`adrenal_gland_right`, `lung_left`, `lung_right`, `bladder`, `prostate`, `femur_left`,
`femur_right`.

This is substantially richer than the previous project consumed, which used `combined_labels`
and a head/body/tail union. In particular `pancreatic_duct` and `common_bile_duct` were not part
of the EXP-26 anatomy experiment, and duct dilation is a primary radiological sign of PDAC. That
is a new candidate lever requiring its own `CAP-EXP` entry under current cohort rules — not a
replay of EXP-26, which was rejected at convergence.

**Known gap.** `PanTS_00003188` has no `celiac_artery.nii.gz` (9,900 of 9,901). One case, one
structure.

### The train/test boundary is live and unguarded

Labels cover **9,901** cases; images cover **9,000**. The 901 extra label cases are exactly
`PanTS_00009001` through `PanTS_00009901`, a contiguous block, and the image cases are
`PanTS_00000001` through `PanTS_00009000`, also contiguous.

**The publisher test set's labels are extracted and sit in the same directory tree as the
training labels, distinguished only by ID range.** Any code that globs the label tree ingests
them silently.

The boundary is a numeric threshold, so the guard is cheap to write and cheap to test. It has to
exist before anything reads that tree. Plan 02 owns it.

## PANORAMA

| Source | Cases | Files | Bytes |
|---|---:|---:|---:|
| `panorama-labels` | 2,238 | 2,238 | 1,252,749,859 |
| `panorama-ct` | 2,238 | 2,238 | 194,439,362,617 |

**2,224 distinct patients**, IDs `100000`–`102223`, a completely contiguous range with no gaps.
2,238 studies across 2,224 patients means **14 patients have more than one study** (13 automatic,
1 manual). Splitting on study rather than patient puts those patients on both sides of a
train/validation boundary — the same leakage class that cost 0.11 lesion Dice on 2026-07-19.
`PANORAMA_patient_id` is given explicitly in the metadata, so grouping does not have to be
inferred.

### Identity rule: the CT channel suffix

CT filenames carry a trailing `_0000` channel component (nnU-Net convention); label filenames do
not.

```
label:  100000_00001.nii.gz
CT:     100000_00001_0000.nii.gz
```

A naive join on filename stem returns **zero** pairs. Stripping the final component gives a
perfect match: 2,238 paired, 0 CT-only, 0 label-only.

This is recorded because a zero-overlap result invites an invented mapping. The rule is: strip
one trailing `_NNNN` channel component from PANORAMA CT filenames before joining.

### Structural inconsistency across the CT batches

`batch_3.zip` and `batch_4.zip` wrap their contents in a `batch_N/` directory. `batch_1.zip` and
`batch_2.zip` do not. Same publisher, same release. Code assuming a uniform layout breaks on half
the batches.

### Annotation class is confounded with tumour status

Labels are partitioned, not layered: 1,756 automatic and 482 manual, with **no case in both** —
confirmed at study level and at patient level.

| | PDAC | non-PDAC | total |
|---|---:|---:|---:|
| automatic | 197 (11.2%) | 1,559 (88.8%) | 1,756 |
| manual | **479 (99.4%)** | 3 (0.6%) | 482 |

The manual labels are, in effect, the tumour cases. Operationally sensible — hand-draw lesions,
let a tool label healthy pancreases — with three consequences:

1. **Automatic-label quality cannot be validated against manual ground truth inside PANORAMA.**
   No case carries both, so there is no paired subset at any size.
2. **Any evaluation reporting both sensitivity and specificity necessarily mixes annotation
   provenance** — positives from hand-drawn labels, negatives from generated ones. This is not
   avoidable by cohort design and must be disclosed as a limitation.
3. **"Evaluate on manual only" measures nothing about specificity**: that cohort has three
   negatives.

`clinical_information.xlsx` (2,238 rows, joins perfectly on `PANORAMA_study_id`, zero unmatched
in either direction) carries `PANORAMA_patient_id`, `PANORAMA_study_id`, study date, age, sex,
scanner, `label` (PDAC / non-PDAC) and `level` (diagnostic certainty). The repository-root copy
is byte-identical to the extracted one (`2ae925de…`).

**Prevalence differs sharply between sources: PANORAMA is 30.2% PDAC (676/2,238) against PanTS's
10.4%.** Mixing sources changes the effective base rate, which changes what a specificity number
means. That requires an explicit decision, not a default.

### A concrete cross-source duplicate lead

The `level` column names other datasets: **`MSD_dataset` (194 cases)** and **`NIH_dataset` (80)**.
D-403 records that MSD Task07 "is already represented within PanTS." If MSD cases also sit in
PANORAMA, the two sources may share patients.

Identifiers will never reveal this — the numbering schemes are unrelated, and all four
cross-source overlaps are zero, which proves only that the namespaces are disjoint. 274 cases
carry an external-dataset provenance marker and are the place G2's duplicate controls should
start.

## File-size anomalies: what they mean

A compressed NIfTI's size is dominated by its **voxel grid**, not by how full the mask is. An
all-zero mask on a large grid and a filled mask on the same grid are comparable in size, while a
small field-of-view scan is small in every structure at once.

**An empty mask therefore cannot be detected from file size.** Not by a zero-byte test (there are
zero zero-byte files anywhere), not by per-case totals, not by per-structure ratios. Confirming
one requires reading voxels — Plan 05.

Comparing each file against the median for its own structure separates two populations:

| Population | Cases | Interpretation |
|---|---:|---|
| Small in ≥80% of their 29 structures | 203 | Small field of view. Not a defect. |
| Small in 1–2 structures, rest normal | 101 | The shape a per-structure defect takes. |
| In between | 117 | Explained by neither. |

**Of the 50 structure-specific cases sampled, the affected structures are:** `liver` (20),
`lung_left` (14), `colon` (12), `stomach` (1), `lung_right` (1), `combined_labels` (1),
`kidney_left` (1).

**Not one is a pancreatic structure.** No `pancreas`, `pancreatic_lesion`, `pancreatic_duct`, or
head/body/tail. Liver, lungs and colon sit at the edges of an abdominal CT's field of view; a
scan cropped toward the pancreas truncates them while pancreatic structures stay intact.

**On this evidence Plan 02 needs no exclusion rule for the structures PROWL segments.** The
caveat is real: 50 of 101 were sampled, and the pattern is inferred from sizes rather than
confirmed from voxels.

**213 of 9,000 CT images (2.4%)** are ≤0.1× the median size, consistent with the same small-scan
population. The previous project met this as *"SpatialPadd (some scans <96 deep)"*. It is now a
quantified cohort property rather than a mid-training surprise.

`combined_labels` shows **zero** oversized files. The previous project's seven corrupt-huge
combined masks do not appear by size in this acquisition. Whether they were drive-specific or
simply under a 10× threshold is not resolvable without voxels.

**PANORAMA case `100433` is large in both modalities** — 17.8× the label median and 13.0× the CT
median. Consistent across both, which reads as a genuinely large scan rather than corruption.
Five PANORAMA labels are ≤0.1× median (`100226`, `100403`, `101129`, `101576`, `101592`); with
one file per case there is no way to tell a small scan from a bad label, and the tool says so.

## What this forces

Candidates for `DECISIONS.md`, none of them decided here:

- **Test-set guard.** Enforce the 9,000/9,001 boundary before any code reads the label tree.
- **PANORAMA join rule.** Strip the trailing `_NNNN` channel component. Assert 2,238 pairs.
- **Patient-level grouping.** Group on `PANORAMA_patient_id`, never on study. 14 patients affected.
- **Annotation-provenance disclosure.** PANORAMA positives and negatives carry different label
  provenance and cannot be separated. Decide how evaluation reports it.
- **Prevalence policy.** 30.2% versus 10.4% across sources. Decide before mixing.
- **G2 duplicate controls.** Start from the 274 MSD/NIH-provenance cases.
- **Voxel-level verification.** Mask emptiness, geometry and target semantics are unanswered and
  unanswerable by this tooling. Plan 05 scope.
- **Small-scan handling.** ~213 cases at small field of view. Preprocessing must not assume a
  minimum depth.

## Process note

The tooling that produced this was written alongside the measurement, and four defects were found
by running it against real data rather than by its tests: a dead trailing-data check inherited
from the scan tool, a path-length check ordered after the syscall that made it moot, a case-level
size threshold that could not see a single bad file among 29, and a per-structure metric that
counted single-structure sources twice. Each is recorded in the extraction design document or
locked by a regression test.

The figures above come from the run after those fixes.
