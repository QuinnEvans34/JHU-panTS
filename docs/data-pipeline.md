# Data Pipeline

**Living doc — now finalized against the real files** (confirmed on disk 2026-06-30). Covers on-disk layout, the manifest, label remapping per level, splits, and the dev subset. Pairs with `architecture.md` (§3–4) and `training.md`.

---

## 1. On-disk layout (confirmed)

Data lives on the external drive, never on the laptop SSD, never committed. Root:

```
/Volumes/JHU-PanTS/PanTS/data/
├── metadata.xlsx                        # per-case: age, sex, diagnosis, spacing, contrast phase, ...
├── ImageTr/PanTS_00000001/ct.nii.gz     # CT volumes (1,000 cases downloaded so far: 00000001–00001000)
├── ImageTe/                             # (empty — test images not downloaded; not needed for dev)
└── LabelAll/PanTS_00000001/
    ├── combined_labels.nii.gz           # single integer label-map (all structures baked in)
    └── segmentations/                   # one binary mask per structure (30 files)
```

**Config var:** everything downstream reads `PANTS_ROOT=/Volumes/JHU-PanTS/PanTS/data` — never hardcoded.

**Current state:** 1,000 training images (`ImageTr/`) + labels for all ~9,901 cases (`LabelAll/`). The manifest **intersects** on cases present in *both* → **1,000 usable cases** right now. Download more image shards later to grow the set (labels are already complete).

## 2. Two label formats — we use `segmentations/`

- **`segmentations/*.nii.gz`** — one binary mask per structure. **Primary source**: transparent, glob by name, compose exactly the classes each level needs.
- **`combined_labels.nii.gz`** — one integer label-map. Handy for quick visualization; not our training source (avoids depending on an undocumented index map).

## 3. Mask inventory (30 structures, confirmed)

- **Pancreas system:** `pancreas`, `pancreas_head`, `pancreas_body`, `pancreas_tail`, `pancreatic_duct`, **`pancreatic_lesion`** (the tumor), `common_bile_duct`.
- **Vessels:** `aorta`, `postcava`, `celiac_artery`, `superior_mesenteric_artery`, `veins`.
- **Organs:** `liver`, `spleen`, `stomach`, `gall_bladder`, `duodenum`, `colon`, `kidney_left`, `kidney_right`, `adrenal_gland_left`, `adrenal_gland_right`, `bladder`, `prostate`, `lung_left`, `lung_right`.
- **Bones:** `femur_left`, `femur_right`.

## 4. Manifest schema (`build_manifest.py`)

One row per case present in both `ImageTr` and `LabelAll`. Mask paths built from known filenames (with existence checks, so it degrades gracefully):

```
case_id            # PanTS_00000001
ct_path            # ImageTr/<id>/ct.nii.gz
pancreas_path      # LabelAll/<id>/segmentations/pancreas.nii.gz
lesion_path        # .../pancreatic_lesion.nii.gz
head/body/tail_path, pancreatic_duct_path, common_bile_duct_path, ...
available_structures   # list of masks actually present
has_lesion         # from lesion mask: sum(voxels) > 0   (ground truth, not metadata)
lesion_voxel_count, lesion_volume_mm3
shape, spacing     # from NIfTI header (cheap read)
diagnosis, sex, age, contrast_phase   # left-joined from metadata.xlsx by case_id
source_split       # Tr / Te
```

- **Derive `has_lesion` from the mask** (load `pancreatic_lesion.nii.gz`, check `sum > 0`), not just metadata — ground truth, and the voxel count feeds subset selection + sampling.
- Left-join `metadata.xlsx` on `case_id`.

## 5. Label remapping per level (real filenames)

`label_mode` in the YAML composes the target from `segmentations/`:

| Level | Classes | Built from |
|-------|---------|-----------|
| **4** | `0=bg, 1=lesion` | `pancreatic_lesion` |
| **4.5** ← primary | `0=bg, 1=pancreas, 2=lesion` | `pancreas` (→1), `pancreatic_lesion` (→2) |
| **4.7** (anatomy-context ablation) | `0=bg, 1=pancreas, 2=lesion, 3..=neighbors` | + `duodenum`, `common_bile_duct`, `pancreatic_duct`, `superior_mesenteric_artery`, `celiac_artery`, `veins` |
| **5** | ~28 classes | full `segmentations/` set (or `combined_labels`) |

**Overlap precedence (critical):** when masks overlap, **lesion wins** over pancreas, and subregions/neighbors are lower priority than lesion. So a tumor voxel inside the pancreas is labeled `lesion`, not `pancreas`. Apply as an ordered paint (background → organs → pancreas → lesion last).

## 6. Patient-level splits (`create_splits.py`)

- **Confirm case == patient first** — check `metadata.xlsx` for a patient identifier distinct from `case_id`. If one exists, **group on it** so no patient leaks across splits. (Open item — verify tomorrow.)
- **`StratifiedGroupKFold`**: group by patient, **stratify by `has_lesion`** so each split has a balanced positive fraction.
- Official `Te` range held out as final test; carve train/val from `Tr` only.
- Save splits as plain `case_id` lists (`splits/train.txt`, `val.txt`, `test.txt`) — tiny, reproducible, safe to commit (IDs only, not data).

## 7. Dev subset (`splits/dev_subset.txt`)

From the 1,000 downloaded `ImageTr` cases, pick ~**80–120 at ~50% lesion-positive** (oversampled vs real prevalence) for fast iteration. Seeded + saved so every run is identical.

## 8. MONAI dataset/loader

Build `[{"image": ct_path, "label": <composed>}]` from manifest + split. `CacheDataset` in RAM for the dev subset (64 GB is plenty); `PersistentDataset` (cache to the external drive) when scaling up. Transform chain splits into cached deterministic preprocessing vs per-iteration random augmentation (see `training.md` §5).

## 9. Sanity check (`sanity_check_case.py`) — the gate

Load one case; print shape/spacing/affine/intensity range; assert the lesion & pancreas mask grids match the CT grid; save axial/coronal/sagittal overlays (CT + pancreas + lesion). Confirm the green/red outlines sit on the right anatomy before any training. **Week 1 milestone.**

## 10. Notes & resolved/open items

- **Tumor subtypes are NOT in the masks** (single `pancreatic_lesion`) → the tumor-type classification stretch, if attempted, must use `metadata.xlsx` `diagnosis`.
- **macOS `tar` gotcha:** the PanTS download scripts use GNU-tar `--checkpoint`, which macOS (BSD tar) rejects — extract with plain `tar -xzf`. Download the tarball, extract, *then* delete (and paste commands one at a time / `&&`-chained, not as a multi-line block).
- **Open:** confirm case==patient in `metadata.xlsx`; finalize target spacing + HU window (test wider vs `[-100,300]`); confirm whether `pancreas.nii.gz` already includes lesion voxels (precedence handles it either way).
