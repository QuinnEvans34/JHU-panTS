# Codex audit request: EXP-12 whole-box ROI change

Paste everything below into Codex, in the repo root, and let it read the referenced files.

---

You are auditing a change to a 3D medical-image segmentation training pipeline before I run an
overnight experiment on it. I want a careful, skeptical code review focused on correctness and on
any train/eval mismatch. Do not rewrite the architecture. Tell me if it is safe to run as-is, and if
not, give me the smallest correct fix.

## What the project is

3D semantic segmentation of the pancreas and pancreatic lesions on CT (the JHU PanTS dataset), using
MONAI + PyTorch on an Apple M5 Pro (MPS backend, not CUDA). Three classes: 0 background, 1 pancreas,
2 lesion. Model is a SegResNet initialized from SuPreM transfer weights (single input channel; the
channel count and encoder width must not change or the pretrained weights stop loading). Training is
patch-based; evaluation is full-volume sliding-window. The dataset lives on an external drive; paths
come from config.

## The pipeline, end to end

1. `src/data/transforms.py::build_transforms(cfg, train)` builds the MONAI transform Compose:
   load image + pancreas mask + lesion mask, `ComposeLabeld` merges the two binary masks into one
   integer label (pancreas=1, lesion=2, lesion wins overlap), reorient to RAS, optionally crop to the
   pancreas, resample to `target_spacing`, window HU to [0,1], pad to at least one patch, then either
   sample training patches or (val) leave the volume whole, then augment, then EnsureTyped.
2. `src/data/dataset.py::get_dataset(cfg, split, train, cache, limit, ids)` wraps that in a
   (Cache)Dataset over a split id-list.
3. `scripts/train.py` runs the loop, logs to MLflow, checkpoints best/last, supports SuPreM transfer
   with an encoder freeze/unfreeze warm-up, and has CLI overrides that mutate cfg after load.
4. `scripts/evaluate.py` scores a checkpoint: lesion + pancreas Dice on tumor-positive cases (raw and
   after CADe post-processing), specificity on tumor-free cases, and a lesion-probability sweep. It
   uses full-volume sliding-window inference via `src/inference/sliding_window.py::predict_volume`.

## The change I just made (this is what I need audited): EXP-12 "whole box"

Prior experiments cropped to the pancreas bounding box (`CropForegroundd` on label>0, plus a margin)
and then took RANDOM sub-patches out of that crop with `RandSpatialCropSamplesd`. That starved the
model: a 64-voxel patch at 0.7mm is only ~45mm across, so it saw a thin slab of a 150-200mm organ,
and the random sampler rarely centered the rare tumor.

The new "whole box" mode instead fits the ENTIRE cropped box into one fixed cube and feeds that as the
input, with no random sub-patching. Specifically, in `build_transforms`, after the crop + resample +
window + pad steps, if `cfg["preprocessing"]["whole_box"]` is true I append
`ResizeWithPadOrCropd(keys=["image","label"], spatial_size=patch)`, which pads boxes smaller than the
cube and center-crops boxes larger than it. In the `train` branch, when `whole_box` is set I SKIP the
random sampler entirely (the fixed cube is the sample) and still apply the augmentations. The
whole-box resize is applied in BOTH train and val so the eval input matches training.

New CLI: `scripts/train.py --whole-box` and `scripts/evaluate.py --whole-box` set
`cfg["preprocessing"]["whole_box"] = True`. Intended run: `--crop-native 16 --whole-box --patch 128
--spacing 1.5` (128 cube at 1.5mm spans 192mm, so almost no case is center-cropped).

Context that matters: I just found and fixed a bug where `evaluate.py` defined `--crop-native` but
never applied it to cfg, causing a silent train/eval preprocessing mismatch that made a model look
broken (pancreas Dice fell from ~0.72 to 0.22). I am paranoid about exactly this class of bug now.

## Please check specifically

1. Train/eval parity. Does the whole-box path produce the SAME preprocessing at train and eval time?
   Confirm every override (`--whole-box`, `--crop-native`, `--spacing`, `--patch`/`--roi`) is actually
   applied to cfg in BOTH `train.py` and `evaluate.py`, and that nothing is parsed-but-ignored (the
   bug class I just hit). Note that in evaluate.py the sliding-window size comes from `--roi`, and in
   train.py the training cube comes from `--patch`; both must resolve to the same 128.
2. The whole-box transform logic in `build_transforms`. Is skipping the sampler correct, i.e. does the
   dataset/DataLoader handle a single-item (non-list) sample the way it already does for the val path
   (train=False, no sampler)? Does `ResizeWithPadOrCropd` on both image and label keep them aligned
   (label uses nearest, image uses the default), and could center-cropping ever silently drop the
   pancreas/lesion for an oversized box? Is the earlier guard `SpatialPadd` now redundant or harmful?
3. Empty / degenerate crops. If a case has a tiny or empty pancreas mask, can any step here raise
   (e.g. a 0-size spatial dim into `Spacingd`, or into `ResizeWithPadOrCropd`)? The run uses the
   `dev_subset_clean` split that already excludes 5 known-empty cases, but I want the code robust
   anyway.
4. SuPreM transfer safety. Confirm nothing in this change alters the input channel count or encoder
   width (which would break the pretrained weight load). Whole-box only changes spatial size, which
   should be fine for a fully-convolutional SegResNet, but confirm 128 is a valid size for its
   downsampling (divisible enough not to hit an odd-size mismatch on the skip connections).
5. MPS / memory. A 128-cube whole volume at batch 1, fp32 on MPS. Flag if this is likely to OOM given
   prior 128-patch runs worked, and whether `num_samples` is correctly irrelevant in whole-box mode.
6. MLflow run naming and any resume path: confirm the whole-box run is distinguishable and that the
   optimizer-over-all-params fix is intact (encoder actually trains after unfreeze).

## Files to read

- `src/data/transforms.py` (the whole-box block and the crop/pad ordering)
- `scripts/train.py` (CLI overrides + run name + the loop)
- `scripts/evaluate.py` (CLI overrides + sliding-window scoring)
- `src/data/dataset.py`, `src/inference/sliding_window.py`, `src/models/segresnet.py`,
  `src/training/trainer.py` (as needed to verify the above)

## What I want back

A short verdict first: SAFE TO RUN or NEEDS FIXES. Then, if fixes are needed, the exact minimal diff
per file, and nothing more. If it is safe, say so plainly and note anything I should watch in the
smoke test (the first 50 iters). Do not restructure working code or change experiment design.
