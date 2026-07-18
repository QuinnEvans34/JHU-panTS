# Data Understanding Report

Project: 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS)
Target: Level 4.5 (background, pancreas, lesion), framed as a CADe segmentation assist, not a diagnostic tool.
Author: Quinn. Week 2. Companion notebook: `week2/eda-notebook.ipynb`.

This report moves the project from proposal assumptions to validated reality. Everything below comes from the real data on disk. I built a manifest from the actual files, cross-checked my labels against the dataset's own tumor flag, and used what I found to lock in the preprocessing and training decisions. All of the numbers here are reproducible by running the manifest scripts and the EDA notebook.

---

## 1. Data Source and Ingestion

The data is the Johns Hopkins PanTS dataset, specifically the public PanTS Mini release. Each case is one 3D abdominal CT volume stored as a compressed NIfTI file, paired with voxel-wise segmentation masks for the pancreas, the pancreatic sub-regions, and any lesion, plus a large set of surrounding abdominal organ masks. There is also a `metadata.xlsx` file with per-scan information like contrast phase, scanner, site, and a tumor flag.

I access the data as a one-time bulk download rather than a live feed. The full Mini release lives on an external drive at `/Volumes/JHU-PanTS/PanTS/data/`, which is 382 GiB used. The repo never touches the raw data. The dataset path is set in the config, not hardcoded, so nothing in the code assumes where the drive is mounted.

Update frequency: none. This is a fixed, published research dataset, so there is no scheduled ingestion, no API polling, and no scraping. That is an important framing point. The assignment describes automating ingestion with an Airflow DAG, but Airflow exists to orchestrate recurring or streaming data pulls. With a static dataset that is downloaded once and never changes, a scheduled DAG would be building infrastructure for an event that never happens. Instead, my ingestion is a reproducible, ordered pipeline of scripts: `build_manifest.py` scans the drive and pairs every CT with its masks, then `create_splits.py` produces the patient-level splits. That gives the same reproducibility and auditability an Airflow DAG would provide, without pretending the data is live. If this were ever extended to ingest new scans continuously, that is exactly where 
 would earn its place, and I have noted it as a capstone-stage option.

Surprises versus the Week 1 proposal. Two things changed once I saw the real files. First, I had assumed the full dataset (around 35,000 scans); the public Mini release is 9,901 cases, so I scoped the project around that and treat full-scale training as a capstone follow-on. Second, there is no patient identifier in the metadata, so I cannot group multiple scans to one patient. I resolved this by treating each scan as its own case and patient, which is the safe choice for splitting (it cannot leak a patient across train and test because there is only ever one scan per patient here).

---

## 2. Data Profile

Counts and shape. The manifest has 9,901 rows and 29 columns. Each row is one case. The columns are file paths (CT and each mask), derived label facts (whether a lesion exists, its voxel count and volume), scan geometry (array shape and voxel spacing), and the joined metadata (contrast phase, sex, age, manufacturer, site, nationality, study year, and the dataset's tumor flag). The split field marks 9,000 training cases and 901 official test cases. The image data itself is 3D: after resampling to a common grid, a typical volume is on the order of 190 by 134 by 131 voxels, but the raw scans vary enormously (see below).

Data types. The columns are a mix of strings (`case_id` and the file paths, plus the raw `shape` and `spacing` fields, which I parse into numbers), a boolean (`has_lesion`), integers (lesion voxel count and the dataset's 0/1 tumor flag), and floats (lesion volume in cubic millimeters, and age). Time range. Scans carry a study year spanning 1984 to 2021, but it is missing for about 72 percent of cases, so it is a rough provenance note rather than a usable time axis, and it is never fed to the model.

Class balance. Only 1,033 of 9,901 cases contain a tumor, which is 10.4 percent. Inside a tumor case the lesion is a tiny fraction of the volume. This is the single most important fact in the whole profile, and most of my training design exists to deal with it.

Tumor prevalence is not uniform across the splits. The training pool is 9.8 percent tumor-positive, while the official test set is 16.8 percent tumor-positive. The test set is deliberately enriched for tumors. This matters when reading results: healthy-case specificity has to be measured on my own held-out healthy cases, and I should not be surprised that the test set stresses tumor detection harder than training prevalence would suggest.

Lesion size. Among tumor cases, lesion volume runs from about 2 cubic millimeters up to 732,388, with a median near 4,721. The quartiles are roughly 1,655 and 11,466. Seventeen lesions are smaller than 100 cubic millimeters, which is only a few voxels. So the target spans five orders of magnitude, and a meaningful number of tumors are extremely small.

Scan geometry. This is the messy part. Slice counts run from 8 to 1,060 (median 190). In-plane voxel spacing runs from 0.42 to 5.0 millimeters (median 0.81), and slice spacing runs from 0.36 to 10.0 millimeters (median 1.25). The scans were acquired on four scanner manufacturers (Siemens, GE, Philips, Toshiba) across many institutions and 14 nationalities, in multiple contrast phases. Two metadata quirks are worth stating plainly: the manufacturer field holds six raw strings but only four real makers, because GE and Philips are each recorded under two spellings, and the site field mixes grouped labels like "15 Sites" with individual codes, so it encodes many more than twenty institutions rather than twenty distinct ones. In other words, the raw voxels are not comparable across scans until they are standardized.

Missing values, duplicates, anomalies, and how I handled them.

- Image and mask completeness: every case has a pancreas mask and a lesion mask file, there are zero duplicate case IDs, and each case carries 27 to 28 structure masks. The image side of the data is clean and usable out of the box, essentially 100 percent.
- Demographic metadata is incomplete: roughly 49 percent of age values are missing, and a large share of sex values are missing as well. There is also a stray sex value of "M " with a trailing space. I handled this by not depending on demographic metadata for the model at all. This is a vision task whose inputs are CT voxels, so missing age or sex does not affect training. If I ever report demographics, I strip whitespace and treat the blanks as unknown.
- Label anomaly: in 44 cases the metadata tumor flag says positive but the lesion mask is empty. I found this by cross-checking my mask-derived label against the dataset flag (they agree 99.6 percent of the time). I trust the mask, because the mask is what the model actually learns from, and I flag those 44 as a known data quirk rather than silently trusting the spreadsheet.

Corrupted files. I did not hit unreadable or truncated volumes during manifest building or the single-case sanity check. The usable-out-of-the-box rate for the imaging data is effectively 100 percent for the cases exercised so far.

### 2.1 The findings that drive the model

Three findings matter most, and they are the spine of how I present this project. First, class imbalance: only 10.4 percent of scans contain a tumor, and inside a tumor case the lesion is a tiny fraction of the volume. Second, geometry heterogeneity: slice counts run from 8 to over 1,000 and voxel spacing varies more than tenfold, so no two raw scans are comparable until they are standardized. Third, over-prediction: the first honest evaluation showed the model finds tumors but flags them almost everywhere (8 percent specificity on healthy scans), which I diagnosed and then largely fixed with the whole-box change. The first two came out of the EDA on the manifest; the third came out of the first real evaluation, and it is the one that reshaped the rest of the plan (Sections 4.3 and 4.4). Almost everything I built traces back to one of these three.

The full set of findings is below, each paired with the concrete pipeline decision it forced. This is the throughline of the project: the data told me what to build.

| EDA finding | The decision it drove |
|---|---|
| Class imbalance: only 10.4% of scans have a tumor, and the lesion is a tiny fraction of a volume. | Tumor-biased patch sampling, a Dice-based loss instead of plain accuracy, and scoring lesion Dice only on tumor cases with specificity measured separately on healthy ones. |
| Lesion size spans five orders of magnitude (2 to 732,388 mm3); 17 tumors are only a few voxels. | Positive-biased sampling so tiny tumors are actually seen, and a minimum-volume cleanup at inference to drop specks. |
| Geometry heterogeneity: slice counts 8 to 1,060, voxel spacing varying more than tenfold. | Reorient to RAS and resample to a common 1.5mm isotropic grid before the model sees anything. |
| Acquisition diversity: four scanner makers, many institutions, multiple contrast phases. | Intensity windowing to a fixed Hounsfield range, plus honesty that a 100-case subset samples only a slice of this diversity. |
| Label check: my mask label agrees with the dataset's tumor flag 99.6% of the time; the 44 mismatches are all flag-positive with an empty mask. | Train from the mask, not the spreadsheet; treat the 44 as an annotation gap rather than trusting either source blindly. |
| Over-prediction at first honest eval (8% specificity), later resolved. | Diagnosed as a field-of-view problem; feeding the whole pancreas box lifted specificity to 55% on its own (Section 4.4). |

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

This directly reflects the EDA. The wild spacing and slice-count spread is why resampling is non-negotiable. The five-orders-of-magnitude lesion size range and the 17 tiny lesions are why patch sampling is biased toward positives and why inference later applies a small minimum-volume cleanup. The steps above are the baseline patch recipe; my current best model instead feeds the whole pancreas box as one 128-voxel cube (Section 4.4), but the reorient, resample, window, and label steps are identical either way.

### 4.3 The overfit-a-single-batch test

Before spending real compute, the pipeline has to prove it can memorize a tiny fixed set. If the network cannot drive training loss down on a couple of cases, the data, loss, or labels are wired wrong. The figure is in the notebook (`week2/overfit_curve.png`), pulled from the actual MLflow logs.

On a fixed batch, training loss fell smoothly from 1.87 to 0.54 while pancreas Dice climbed to 0.89. On a tumor-positive overfit, lesion Dice rose from 0 to about 0.85, which proves the network can fit the hard minority class and not just the easy pancreas. The lesion curve is spiky because Dice is measured on rotating random crops, not because learning is unstable. This is the Week 2 milestone, and it passed: the pipeline learns end to end.

One real lesson came out of this test. Early runs showed lesion Dice pinned at 0.000, which looked like failure but was a measurement artifact: Dice on a tumor-free scan is undefined and was printing as zero. Once I scored lesion accuracy only on tumor-positive cases and measured specificity separately on tumor-free ones, the true picture appeared. On the validation split the model reaches pancreas Dice 0.720 and lesion Dice 0.169 on tumor-positive cases, but specificity is only 8 percent (1 of 12 healthy scans correctly not flagged), so it is badly over-predicting.

The interesting part is what fixed it. Simple cleanup, keeping the largest component and dropping small blobs, did nothing for specificity, because the false positives are large connected regions rather than prunable specks. But adding an anatomical constraint, that a pancreatic lesion must sit within 10mm of the predicted pancreas, lifted specificity from 8 percent to 42 percent (5 of 12 healthy scans) with no retraining at all. A probability-threshold sweep barely helped by comparison (specificity held at 8 percent until a very high 0.90 cutoff), which tells me the remaining false positives are high-confidence and near the organ, not low-confidence noise. The tradeoff is honest: buying that specificity cost a little lesion Dice on tumor cases, from 0.169 down to 0.139. Fixing how I measure was as important as fixing the model, and this pair of results, diagnosing why naive cleanup fails and finding the geometric fix that works, is what shaped the Week 3 and Week 4 plan (see `docs/implementation-plan.md`). Since drafting this section I ran the first item on that plan, and it largely resolved the over-prediction on its own; Section 4.4 records where the model now stands.

### 4.4 Update since drafting: the whole-box result and where the model stands now

Section 4.3 ended with a plan to fix the over-prediction. I ran the first structural item on that plan during Week 2, and it worked better than expected, so this section records where the model actually stands as of the end of the week.

The diagnosis pointed at how the model sees the pancreas. In the original recipe the network trained on small random 96-voxel patches cut out of the scan, so on any step it saw only a slab of the organ and had little context for deciding whether a bright region was truly a tumor. The fix was structural: crop to the pancreas region and feed the entire pancreas box to the model as one fixed cube every step, so it always sees the whole organ and its surroundings at once. This is the "radiologist provides the region of interest" setting, an honest oracle since it uses the ground-truth pancreas location to place the box, and it is the first stage of the localize-then-segment cascade I plan to build out at capstone.

The result improved every metric at once. On the tumor-positive validation cases, pancreas Dice rose from 0.72 to 0.807 and lesion Dice rose from 0.17 to 0.263, my best to date. More importantly for the central problem, specificity on healthy scans jumped from 8 percent to 55 percent, and it did so on the model's own, with the anatomical constraint from Section 4.3 now barely changing the number. Giving the model the whole organ in context is what taught it to stay quiet on healthy scans, which is a cleaner fix than the post-hoc geometric rule.

Two honesty notes travel with this result. First, it is an oracle-ROI number (a provided pancreas box), not a fully automated scan-to-result system, so it is best read as "with a provided region of interest." Second, the specificity leap is partly structural: when the model only looks inside the pancreas box there is far less healthy tissue to raise a false alarm on, so the 8 to 55 percent jump is not a like-for-like comparison against the whole-scan numbers in Section 4.3.

For outside context, published pancreas segmentation models report an organ Dice around 0.79 to 0.85, so my 0.807 pancreas result is already in that range. Dedicated pancreatic-tumor detection systems report roughly 90 percent sensitivity and 90 percent specificity, but those are fully automated, trained on thousands of scans, so my numbers are best framed as on-trajectory at a 95-case development scale, with data volume as the main remaining lever. Every run this week is logged as a formal experiment with a hypothesis and an accept-or-reject decision in `docs/experiments.md`.

---

## 5. Feature Candidates, Revised Requirements, and Schedule

### 5.1 Feature candidates and justification

This is a vision model, so the features are voxel data, not tabular columns. The planned model inputs, each with its transformation and the reason it is included:

- Primary input: the preprocessed 3D CT volume. Transformation: reorient to RAS, resample to 1.5 millimeter isotropic, window Hounsfield units to [-100, 300], scale to [0, 1]. Justification: this is the raw signal the tumor lives in, and the transformation is exactly what makes the wildly inconsistent scans of Section 2 comparable to each other. For a segmentation model this standardization is the feature engineering.
- Candidate auxiliary input: a few neighboring anatomical structures as extra input channels (for example duodenum and vessels). Transformation: each structure's binary mask added as its own channel alongside the CT. Justification: every case ships with 27 to 28 organ masks, and the PanTS work reports that richer anatomical context improves tumor Dice substantially, so this is a planned ablation, measured by the change in lesion Dice.
- Explicitly excluded: demographic and acquisition metadata (age, sex, site). Justification: it is about half missing and a voxel segmentation model does not need it. It stays in the manifest for reporting and stratification, not as a model input. One exception proved its analytic worth this week: contrast phase is not a model input, but slicing the data by it revealed that phase is a strong driver of the sensitivity-specificity balance (see `docs/experiments.md`, EXP-14).

### 5.2 Revised Core Requirements (granular and measurable)

- R1 Data pipeline: manifest of all 9,901 cases with paired masks, patient-level splits with no slice leakage, reproducible from scripts. Status: done and validated.
- R2 Standardization: RAS reorientation, 1.5 millimeter isotropic resampling, [-100, 300] Hounsfield windowing to [0, 1], 3-class label composition. Status: done.
- R3 Overfit gate: drive training loss down and reach high Dice on a fixed 1 to 2 case batch for both pancreas and lesion. Status: passed (loss 1.87 to 0.54, pancreas 0.89, lesion about 0.85).
- R4 Baseline training: train Level 4.5 on the dev subset with MLflow tracking and validation curves for pancreas and lesion. Status: done, ahead of schedule. The whole-box model trained on the dev subset with validation on tumor-positive cases; see Section 4.4.
- R5 Full-volume evaluation: sliding-window inference on whole volumes, reporting pancreas and lesion Dice separately, plus patient-level sensitivity and specificity for the CADe framing. Status: in place. Current best is lesion Dice 0.263 in the oracle-ROI setting, moving toward the 0.35 to 0.50 target as data scales. Target refinement: Week 4.
- R6 False-positive control: apply CADe post-processing (largest connected component, a minimum-volume threshold, and an anatomical lesion-within-pancreas constraint) and report specificity before and after. Status: implemented. Finding: the whole-box model largely self-corrects (specificity 55 percent on its own), so the constraint is now a near no-op rather than the main lever.
- R7 Delivery: React and NiiVue static demo that loads a precomputed case, shows three-plane and 3D views, gives the possible-tumor summary, and exports the mask, plus a final report with honest limitations. Target: Week 5.

### 5.3 Schedule

The finalized week-by-week schedule lives in `docs/schedule.md` and the living execution plan is in `docs/implementation-plan.md`. In short: Week 2 was the wired pipeline and the passed overfit gate, and it ran ahead, since the evaluation, the sensitivity-specificity work, and the whole-box improvement all landed early. That pulls the plan forward: Week 3 pivots to the main remaining lever, scaling up the tumor data (and a clarity-curriculum experiment, EXP-13, suggested by my instructor), Week 4 is full-volume evaluation and pushing lesion Dice toward the 0.35 to 0.50 target, and Week 5 is failure analysis, the static demo, and the final report. Level 4.5 is the line that has to hold; Level 5 is the first thing dropped if a week slips.

---

## 6. Context Files

Three AI-collaboration documents are maintained in the repo and updated every week:

- `docs/Claude.md`: the project's AI context file. It defines the goal, how the assistant should help, and the tone, scope, and constraints (no clinical claims, split by patient not slice, config-driven pipeline, dataset on the external drive).
- `docs/ai-usage-log.md`: a running weekly log of what I used AI for, the prompts and context that worked well, and where the output needed correction. The Week 2 entry is in place.
- `docs/agent-plan.md`: the operating guide for how the agent and I divide work, and the AI-versus-manual task split.

These are living files that grow across the five weeks, not one-time deliverables.

---

## Reproducibility

Manifest and splits: `python scripts/build_manifest.py` then `python scripts/create_splits.py`. EDA and figures: open `week2/eda-notebook.ipynb`, which reads `outputs/manifest.csv` directly. The overfit figure is generated from the MLflow run database. No raw data is committed; the dataset path is set in `configs/level45.yaml`.

---

## What changed since first drafting this report (updated 2026-07-11)

I reviewed the whole plan at the end of Week 2 to be sure it still holds, and it does. Nothing about the data understanding changed. The EDA findings in Sections 1 through 4, the class imbalance, the geometry heterogeneity, the label-validation check, and the standardization decisions they justify, are all unchanged. The project's architecture and scope are also unchanged from the Week 1 proposal: the same SuPreM SegResNet, the same Level 4.5 target, the same data pipeline, the same non-diagnostic CADe framing, and the same React and NiiVue delivery plan.

Every change this week was model-side improvement, not a redesign. I diagnosed the over-prediction problem (Section 4.3), then fixed most of it with the whole-box change (Section 4.4), and I corrected one measurement bug in my evaluation script that had briefly made a good model look broken. The revised Core Requirements and the schedule in `docs/implementation-plan.md` and `docs/schedule.md` reflect this: the structure is the same, the model results moved forward, and the main remaining lever, more tumor data, is exactly what the plan already routes to Week 4 and the capstone. The outline was solid going into the week, and the week's work was about strengthening the model inside that outline rather than changing it.
