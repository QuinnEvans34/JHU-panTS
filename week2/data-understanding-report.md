# Data Understanding Report

Project: 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS)
Target: Level 4.5 (background, pancreas, lesion), framed as a CADe segmentation assist, not a diagnostic tool.
Author: Quinn. Week 2. Companion notebook: `week2/eda-notebook.ipynb`.

This report moves the project from proposal assumptions to validated reality. Everything below comes from the real data on disk. I built a manifest from the actual files, cross-checked my labels against the dataset's own tumor flag, and used what I found to lock in the preprocessing and training decisions. All of the numbers here are reproducible by running the manifest scripts and the EDA notebook.

---

## 1. Data Source and Ingestion

The data is the Johns Hopkins PanTS dataset, specifically the public PanTS Mini release. Each case is one 3D abdominal CT volume stored as a compressed NIfTI file, paired with voxel-wise segmentation masks for the pancreas, the pancreatic sub-regions, and any lesion, plus a large set of surrounding abdominal organ masks. There is also a `metadata.xlsx` file with per-scan information like contrast phase, scanner, site, and a tumor flag.

I access the data as a one-time bulk download rather than a live feed. The full Mini release lives on an external drive at `/Volumes/JHU-PanTS/PanTS/data/`, which is 382 GiB used. The repo never touches the raw data. The dataset path is set in the config, not hardcoded, so nothing in the code assumes where the drive is mounted.

Update frequency: none. This is a fixed, published research dataset, so there is no scheduled ingestion, no API polling, and no scraping. That is an important framing point. The assignment describes automating ingestion with an Airflow DAG, but Airflow exists to orchestrate recurring or streaming data pulls. With a static dataset that is downloaded once and never changes, a scheduled DAG would be building infrastructure for an event that never happens. Instead, my ingestion is a reproducible, ordered pipeline of scripts: `build_manifest.py` scans the drive and pairs every CT with its masks, then `create_splits.py` produces the patient-level splits. That gives the same reproducibility and auditability an Airflow DAG would provide, without pretending the data is live. If this were ever extended to ingest new scans continuously, that is exactly where Airflow would earn its place, and I have noted it as a capstone-stage option.

Surprises versus the Week 1 proposal. Two things changed once I saw the real files. First, I had assumed the full dataset (around 35,000 scans); the public Mini release is 9,901 cases, so I scoped the project around that and treat full-scale training as a capstone follow-on. Second, there is no patient identifier in the metadata, so I cannot group multiple scans to one patient. I resolved this by treating each scan as its own case and patient, which is the safe choice for splitting (it cannot leak a patient across train and test because there is only ever one scan per patient here).

---

## 2. Data Profile

Counts and shape. The manifest has 9,901 rows and 29 columns. Each row is one case. The columns are file paths (CT and each mask), derived label facts (whether a lesion exists, its voxel count and volume), scan geometry (array shape and voxel spacing), and the joined metadata (contrast phase, sex, age, manufacturer, site, nationality, study year, and the dataset's tumor flag). The split field marks 9,000 training cases and 901 official test cases. The image data itself is 3D: after resampling to a common grid, a typical volume is on the order of 190 by 134 by 131 voxels, but the raw scans vary enormously (see below).

Class balance. Only 1,033 of 9,901 cases contain a tumor, which is 10.4 percent. Inside a tumor case the lesion is a tiny fraction of the volume. This is the single most important fact in the whole profile, and most of my training design exists to deal with it.

Tumor prevalence is not uniform across the splits. The training pool is 9.8 percent tumor-positive, while the official test set is 16.8 percent tumor-positive. The test set is deliberately enriched for tumors. This matters when reading results: healthy-case specificity has to be measured on my own held-out healthy cases, and I should not be surprised that the test set stresses tumor detection harder than training prevalence would suggest.

Lesion size. Among tumor cases, lesion volume runs from about 2 cubic millimeters up to 732,388, with a median near 4,721. The quartiles are roughly 1,655 and 11,466. Seventeen lesions are smaller than 100 cubic millimeters, which is only a few voxels. So the target spans five orders of magnitude, and a meaningful number of tumors are extremely small.

Scan geometry. This is the messy part. Slice counts run from 8 to 1,060 (median 190). In-plane voxel spacing runs from 0.42 to 5.0 millimeters (median 0.81), and slice spacing runs from 0.36 to 10.0 millimeters (median 1.25). The scans were acquired on 6 manufacturers across 20 sites and 14 nationalities, in multiple contrast phases. In other words, the raw voxels are not comparable across scans until they are standardized.

Missing values, duplicates, anomalies, and how I handled them.

- Image and mask completeness: every case has a pancreas mask and a lesion mask file, there are zero duplicate case IDs, and each case carries 27 to 28 structure masks. The image side of the data is clean and usable out of the box, essentially 100 percent.
- Demographic metadata is incomplete: roughly 49 percent of age values are missing, and a large share of sex values are missing as well. There is also a stray sex value of "M " with a trailing space. I handled this by not depending on demographic metadata for the model at all. This is a vision task whose inputs are CT voxels, so missing age or sex does not affect training. If I ever report demographics, I strip whitespace and treat the blanks as unknown.
- Label anomaly: in 44 cases the metadata tumor flag says positive but the lesion mask is empty. I found this by cross-checking my mask-derived label against the dataset flag (they agree 99.6 percent of the time). I trust the mask, because the mask is what the model actually learns from, and I flag those 44 as a known data quirk rather than silently trusting the spreadsheet.

Corrupted files. I did not hit unreadable or truncated volumes during manifest building or the single-case sanity check. The usable-out-of-the-box rate for the imaging data is effectively 100 percent for the cases exercised so far.

---

## 3. Classical ML / Tabular

Not applicable. This is a 3D deep-learning segmentation project with no tabular feature model.

---

## 4. Deep Learning / Unstructured Data

### 4.1 Ingestion pipeline: storage to compute

The path from disk to the network has three stages. First, `build_manifest.py` walks the external drive and produces one CSV row per case pairing the CT with its masks and joining the metadata. Second, `create_splits.py` writes patient-level id lists (train, val, test, and a small dev subset). Third, at training time a MONAI dataset reads those id lists, loads the NIfTI files, applies the transform pipeline, and hands patches to a DataLoader.

The dataset builder reads the split, turns each case into a record of file paths, and wraps it in a MONAI dataset with an optional in-memory cache:

```python
def get_dataset(cfg, split_name, train=True, cache=False, limit=None, ids=None):
    dp = P.data_paths(cfg)
    if ids is None:
        ids = load_split_ids(dp["splits_dir"], split_name)
    if limit:
        ids = ids[:limit]
    records = build_records(dp["manifest"], ids)   # [{"image": ct, "pancreas": ..., "lesion": ...}, ...]
    transform = build_transforms(cfg, train=train)
    if cache:
        return CacheDataset(data=records, transform=transform, cache_rate=1.0,
                            num_workers=cfg["training"]["num_workers"])
    return Dataset(data=records, transform=transform)
```

Batching and shuffling are handled by a standard MONAI DataLoader over that dataset:

```python
from monai.data import DataLoader
loader = DataLoader(get_dataset(cfg, "train", train=True, cache=True),
                    batch_size=cfg["training"]["batch_size"],
                    shuffle=True, num_workers=cfg["training"]["num_workers"])
```

Two details matter here. Shuffling happens at the case level each epoch, and because the training transform crops several patches per case, each step sees a fresh mix of patches. And I use `CacheDataset` so the expensive resample-and-window step is done once and reused, which is what makes training tolerable on the Apple Silicon MPS backend.

### 4.2 Data transformation and standardization

Because the raw scans are so inconsistent (Section 2), every volume goes through the same standardization before the network ever sees it. The steps, in order:

- Reorient to a canonical RAS orientation so anatomy is always in the same direction.
- Resample to 1.5 millimeter isotropic spacing, so one voxel means the same physical size in every scan. Images use trilinear interpolation, masks use nearest-neighbor so labels stay integer.
- Window CT intensity to the Hounsfield range [-100, 300] and scale it to [0, 1], which focuses on soft tissue and abdominal organs and clips irrelevant extremes.
- Compose the 3-class label: background 0, pancreas 1, lesion 2, with lesion taking priority where the masks overlap.
- Crop to the body region, then pad so every volume is at least the patch size (some scans are thinner than 96 voxels).
- For training, sample 96 by 96 by 96 patches with `RandCropByPosNegLabeld` biased toward lesion voxels, so the network actually sees tumors despite their rarity, plus light augmentation.

This directly reflects the EDA. The wild spacing and slice-count spread is why resampling is non-negotiable. The five-orders-of-magnitude lesion size range and the 17 tiny lesions are why patch sampling is biased toward positives and why inference later applies a small minimum-volume cleanup.

### 4.3 The overfit-a-single-batch test

Before spending real compute, the pipeline has to prove it can memorize a tiny fixed set. If the network cannot drive training loss down on a couple of cases, the data, loss, or labels are wired wrong. The figure is in the notebook (`week2/overfit_curve.png`), pulled from the actual MLflow logs.

On a fixed batch, training loss fell smoothly from 1.87 to 0.54 while pancreas Dice climbed to 0.89. On a tumor-positive overfit, lesion Dice rose from 0 to about 0.85, which proves the network can fit the hard minority class and not just the easy pancreas. The lesion curve is spiky because Dice is measured on rotating random crops, not because learning is unstable. This is the Week 2 milestone, and it passed: the pipeline learns end to end.

One real lesson came out of this test. Early runs showed lesion Dice pinned at 0.000, which looked like failure but was a measurement artifact: Dice on a tumor-free scan is undefined and was printing as zero. Once I scored lesion accuracy only on tumor-positive cases and measured specificity separately on tumor-free ones, the true picture appeared. On the validation split the model reaches pancreas Dice 0.720 and lesion Dice 0.169 on tumor-positive cases, but specificity is only 8 percent (1 of 12 healthy scans correctly not flagged), so it is badly over-predicting. Just as telling, CADe post-processing did not rescue it: keeping the largest component and dropping small blobs left specificity at 8 percent and actually lowered lesion Dice to 0.139. That means the false positives are large connected regions, not prunable specks, so the fix has to come from training the model to be less trigger-happy and from an anatomical constraint (lesions only inside the pancreas), not from more cleanup. Fixing how I measure was as important as fixing the model, and this result is what reshaped the Week 3 and Week 4 plan (see `docs/implementation-plan.md`).

---

## 5. Feature Candidates, Revised Requirements, and Schedule

### 5.1 Feature candidates and justification

This is a vision model, so the primary input feature is the preprocessed 3D CT volume itself: reoriented, resampled to 1.5 millimeter isotropic, and intensity-windowed to [-100, 300] then scaled to [0, 1]. That transformation is the feature engineering. The EDA justifies each part of it, as described in Section 4.2.

The candidate auxiliary feature is surrounding anatomy. Each case ships with 27 to 28 organ masks, and the PanTS work reports that adding richer anatomical context improves tumor Dice substantially. So a planned experiment is to feed a few neighboring structures (for example duodenum and vessels) as extra channels and measure the change in lesion Dice. Demographic metadata (age, sex, site) is explicitly not used as a model input: it is about half missing and is not needed for a voxel segmentation task, though it stays in the manifest for reporting and stratification.

### 5.2 Revised Core Requirements (granular and measurable)

- R1 Data pipeline: manifest of all 9,901 cases with paired masks, patient-level splits with no slice leakage, reproducible from scripts. Status: done and validated.
- R2 Standardization: RAS reorientation, 1.5 millimeter isotropic resampling, [-100, 300] Hounsfield windowing to [0, 1], 3-class label composition. Status: done.
- R3 Overfit gate: drive training loss down and reach high Dice on a fixed 1 to 2 case batch for both pancreas and lesion. Status: passed (loss 1.87 to 0.54, pancreas 0.89, lesion about 0.85).
- R4 Baseline training: train Level 4.5 on the dev subset with MLflow tracking and validation curves for pancreas and lesion. Target: Week 3.
- R5 Full-volume evaluation: sliding-window inference on whole volumes, reporting pancreas and lesion Dice separately, plus patient-level sensitivity and specificity for the CADe framing. Target: Week 4, with a lesion Dice target in the 0.35 to 0.50 range.
- R6 False-positive control: apply CADe post-processing (largest connected component plus a minimum-volume threshold) and report specificity before and after. Target: Week 4.
- R7 Delivery: React and NiiVue static demo that loads a precomputed case, shows three-plane and 3D views, gives the possible-tumor summary, and exports the mask, plus a final report with honest limitations. Target: Week 5.

### 5.3 Schedule

The finalized week-by-week schedule lives in `docs/schedule.md` and the living execution plan is in `docs/implementation-plan.md`. In short: Week 2 is the wired pipeline and the passed overfit gate (done), Week 3 is baseline Level 4.5 training on the dev subset with validation curves, Week 4 is lesion-focused training plus full-volume evaluation and false-positive control, and Week 5 is failure analysis, the static demo, and the final report. Level 4.5 is the line that has to hold; Level 5 is the first thing dropped if a week slips.

---

## Reproducibility

Manifest and splits: `python scripts/build_manifest.py` then `python scripts/create_splits.py`. EDA and figures: open `week2/eda-notebook.ipynb`, which reads `outputs/manifest.csv` directly. The overfit figure is generated from the MLflow run database. No raw data is committed; the dataset path is set in `configs/level45.yaml`.
