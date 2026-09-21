"""MONAI transform pipelines for Level 4.5 (bg / pancreas / lesion).

Composes the 3-class label from separate binary masks (pancreas -> 1, lesion -> 2,
lesion wins on overlap), then applies the locked preprocessing + patch sampling from
configs/level45.yaml.
"""
from __future__ import annotations

import torch
from monai.transforms import (
    Compose,
    LoadImaged,
    EnsureChannelFirstd,
    Orientationd,
    Spacingd,
    ScaleIntensityRanged,
    CropForegroundd,
    SpatialPadd,
    ResizeWithPadOrCropd,
    DeleteItemsd,
    RandCropByPosNegLabeld,
    RandCropByLabelClassesd,
    RandSpatialCropSamplesd,
    RandFlipd,
    RandRotate90d,
    RandScaleIntensityd,
    RandShiftIntensityd,
    EnsureTyped,
    MapTransform,
)

IMAGE_MASK_KEYS = ["image", "pancreas", "lesion"]   # legacy default (pancreas_lesion + combined)


def resolver_of(cfg: dict) -> str:
    """The pancreas-organ resolver, DECOUPLED from label_mode. anatomy5 is always hbt_union
    (its classes ARE the subregions); pancreas_lesion honors pancreas_resolver (default combined)."""
    if cfg.get("label_mode", "pancreas_lesion") == "anatomy5":
        return "hbt_union"
    return cfg.get("pancreas_resolver", "combined")


def mask_key_map(cfg: dict) -> dict:
    """{record_key: manifest_column} for the mask inputs this recipe needs.
    anatomy5 and the hbt_union resolver both consume head/body/tail (+lesion); the legacy
    combined resolver consumes the single pancreas mask (+lesion)."""
    lm = cfg.get("label_mode", "pancreas_lesion")
    if lm == "anatomy5" or resolver_of(cfg) == "hbt_union":
        return {"head": "head_path", "body": "body_path", "tail": "tail_path", "lesion": "lesion_path"}
    return {"pancreas": "pancreas_path", "lesion": "lesion_path"}


def mask_keys(cfg: dict) -> list:
    return list(mask_key_map(cfg).keys())


def load_keys(cfg: dict) -> list:
    return ["image"] + mask_keys(cfg)


def _foreground_label(x):
    """Select pancreas+lesion voxels (label > 0) for the pancreas ROI crop.
    Module-level (not a lambda) so it pickles for the cache workers."""
    return x > 0


class ComposeLabeld(MapTransform):
    """Merge separate binary masks into one integer label map.

    pancreas -> 1, lesion -> 2 (lesion painted last, so it wins on overlap).
    Consumes the mask keys and produces a single `label` key on the image grid.
    """

    def __init__(self, pancreas_key="pancreas", lesion_key="lesion", label_key="label",
                 keep_pancreas_roi=False):
        super().__init__(keys=[pancreas_key, lesion_key], allow_missing_keys=True)
        self.pancreas_key = pancreas_key
        self.lesion_key = lesion_key
        self.label_key = label_key
        # keep the ORIGINAL pancreas organ mask as a separate `panc_roi` key, so the ROI crop
        # can be built from pancreas ALONE (not pancreas union lesion, which leaks lesion extent
        # into the field of view). See the metrics audit (2026-07-17) and roi_source in the config.
        self.keep_pancreas_roi = keep_pancreas_roi

    def __call__(self, data):
        d = dict(data)
        panc = d.get(self.pancreas_key)
        les = d.get(self.lesion_key)
        base = panc if panc is not None else les
        if base is None:
            raise KeyError("ComposeLabeld needs at least one of pancreas/lesion")
        lab = torch.zeros_like(base)  # MetaTensor -> inherits affine/meta from the mask
        if panc is not None:
            lab[panc > 0] = 1
        if les is not None:
            lab[les > 0] = 2
        d[self.label_key] = lab
        if self.keep_pancreas_roi:
            src = panc if panc is not None else les
            d["panc_roi"] = (src > 0).to(lab.dtype)
        for k in (self.pancreas_key, self.lesion_key):
            d.pop(k, None)
        return d


class ResolveLabeld(MapTransform):
    """Compose the integer target from source masks with a configurable pancreas resolver.

    Design note (EXP-26, flagged for Codex code review): both the primary-collapse target
    and the auxiliary head/body/tail targets are derived downstream from this SINGLE
    mutually-exclusive integer `label` map (which passes through every spatial transform with
    nearest-neighbor interpolation), rather than from four separately-carried boolean masks.
    This is lossless for the auxiliary domain M = (non-lesion pancreas voxels) whenever
    head/body/tail MUTUAL overlap is negligible — which scripts/audit_subregions.py gates —
    and it is strictly better-defined than overlapping booleans (softmax cannot satisfy
    p_head=p_body=1 at a shared voxel). One label map also minimizes the alignment surface.

    anatomy5:                    head->1, body->2, tail->3, lesion->4 (lesion painted last, wins).
    pancreas_lesion + hbt_union: pancreas=(head∪body∪tail)->1, lesion->2 (lesion wins).
    panc_roi (crop source) = head∪body∪tail computed BEFORE lesion painting (organ extent, no leak).
    """

    def __init__(self, label_mode: str, keep_pancreas_roi: bool = False):
        super().__init__(keys=["head", "body", "tail", "lesion"], allow_missing_keys=True)
        self.label_mode = label_mode
        self.keep_pancreas_roi = keep_pancreas_roi

    def __call__(self, data):
        d = dict(data)
        head, body, tail, les = d.get("head"), d.get("body"), d.get("tail"), d.get("lesion")
        base = next((m for m in (head, body, tail, les) if m is not None), None)
        if base is None:
            raise KeyError("ResolveLabeld needs at least one of head/body/tail/lesion")
        lab = torch.zeros_like(base)     # MetaTensor -> inherits affine/meta
        union = torch.zeros_like(base)
        for m in (head, body, tail):
            if m is not None:
                union[m > 0] = 1
        if self.label_mode == "anatomy5":
            if head is not None:
                lab[head > 0] = 1
            if body is not None:
                lab[body > 0] = 2
            if tail is not None:
                lab[tail > 0] = 3
            if les is not None:
                lab[les > 0] = 4         # lesion wins on overlap (painted last)
        else:  # pancreas_lesion + hbt_union
            lab[union > 0] = 1
            if les is not None:
                lab[les > 0] = 2
        d["label"] = lab
        if self.keep_pancreas_roi:
            d["panc_roi"] = (union > 0).to(lab.dtype)
        for k in ("head", "body", "tail", "lesion"):
            d.pop(k, None)
        return d


class PadEmptyCropd(MapTransform):
    """Pad only a degenerate crop so Spacingd never receives a zero-size axis."""

    def __init__(self, keys, source_key, spatial_size):
        super().__init__(keys)
        self.source_key = source_key
        self.pad = SpatialPadd(keys=keys, spatial_size=spatial_size)

    def __call__(self, data):
        d = dict(data)
        if any(size == 0 for size in d[self.source_key].shape[-3:]):
            return self.pad(d)
        return d


def build_transforms(cfg: dict, train: bool = True) -> Compose:
    pre = cfg["preprocessing"]
    samp = cfg["sampling"]
    aug = cfg.get("augment", {})

    spacing = tuple(pre["target_spacing"])
    hu_lo, hu_hi = pre["hu_window"]
    patch = tuple(samp["patch_size"])
    axcodes = pre.get("orientation", "RAS")

    crop_native_vox = pre.get("crop_native_margin_vox")   # CLARITY: crop in native space, pre-resample
    crop_panc_mm = pre.get("crop_to_pancreas_margin_mm")   # EXP-10 style: crop after resample
    crop_pancreas = (crop_native_vox is not None) or (crop_panc_mm is not None)
    whole_box = bool(pre.get("whole_box", False))          # EXP-12: feed the entire pancreas box as one cube

    # roi_source: what the pancreas crop is built from.
    #   "union"    = pancreas union lesion (label>0). Legacy default. LEAKS lesion extent into
    #                the ROI when a lesion protrudes past the pancreas mask (metrics audit).
    #   "pancreas" = the pancreas organ mask ALONE (no lesion), the honest provided-ROI setting.
    roi_source = pre.get("roi_source", "union")
    use_panc_roi = crop_pancreas and roi_source == "pancreas"
    crop_src = "panc_roi" if use_panc_roi else "label"
    extra = ["panc_roi"] if use_panc_roi else []

    # mode-derived input keys + composer (legacy pancreas_lesion+combined is untouched)
    lkeys = load_keys(cfg)                                   # ["image", <mask keys for this recipe>]
    label_mode = cfg.get("label_mode", "pancreas_lesion")
    if label_mode == "anatomy5" or resolver_of(cfg) == "hbt_union":
        composer = ResolveLabeld(label_mode, keep_pancreas_roi=use_panc_roi)
    else:
        composer = ComposeLabeld("pancreas", "lesion", "label", keep_pancreas_roi=use_panc_roi)

    tfs = [
        LoadImaged(keys=lkeys, allow_missing_keys=True),
        EnsureChannelFirstd(keys=lkeys, allow_missing_keys=True),
        composer,
        Orientationd(keys=["image", "label"] + extra, axcodes=axcodes),
    ]
    # CLARITY: crop to the pancreas in NATIVE resolution BEFORE resampling, so only the small
    # ROI gets resampled (fine spacing becomes affordable) and detail is not averaged away
    # before the crop. Margin is in native voxels. Crop source is pancreas-only or union per roi_source.
    if crop_native_vox is not None:
        tfs.append(CropForegroundd(keys=["image", "label"] + extra, source_key=crop_src,
                                   select_fn=_foreground_label, margin=int(crop_native_vox),
                                   allow_smaller=True))
        # Empty foreground crops are 0-size in MONAI and cannot enter Spacingd.
        # Do not pad normal crops here: patch-sized padding in native voxel space
        # changes their physical field of view before resampling.
        tfs.append(PadEmptyCropd(keys=["image", "label"] + extra, source_key="label",
                                 spatial_size=patch))
    sp_modes = ("bilinear", "nearest") + (("nearest",) if use_panc_roi else ())
    tfs.append(Spacingd(keys=["image", "label"] + extra, pixdim=spacing, mode=sp_modes))
    tfs.append(ScaleIntensityRanged(keys="image", a_min=hu_lo, a_max=hu_hi, b_min=0.0, b_max=1.0, clip=True))

    if crop_panc_mm is not None:
        # EXP-10 style oracle ROI: crop to the pancreas AFTER resampling (margin mm -> voxels).
        margin_vox = max(1, int(round(float(crop_panc_mm) / float(spacing[0]))))
        tfs.append(CropForegroundd(keys=["image", "label"] + extra, source_key=crop_src,
                                   select_fn=_foreground_label, margin=margin_vox, allow_smaller=True))
    elif not crop_pancreas and samp.get("crop_foreground", True):
        # no pancreas crop -> trim air/table (body crop); after scaling air maps to 0
        tfs.append(CropForegroundd(keys=["image", "label"], source_key="image", allow_smaller=True))

    if use_panc_roi:
        tfs.append(DeleteItemsd(keys=["panc_roi"]))   # done its job as the crop source

    # guarantee every volume is at least one patch in size
    tfs.append(SpatialPadd(keys=["image", "label"], spatial_size=patch))

    if whole_box:
        # WHOLE-BOX (EXP-12): after cropping to the pancreas bounding box + buffer, fit the
        # ENTIRE box into one fixed cube and feed that as the model input, instead of taking
        # random sub-patches out of it. ResizeWithPadOrCropd centers the box: it PADS the
        # smaller boxes (whole organ preserved) and center-CROPS the rare box larger than the
        # cube. The model then sees the whole pancreas + its surrounding context every step,
        # which fixes the field-of-view starvation that hurt the random-sub-patch runs.
        # Applied in BOTH train and val so the eval input matches training exactly.
        # NOTE: pick spacing so 'patch * spacing' spans the largest pancreas (~200mm),
        # e.g. patch 128 @ 1.5mm = 192mm, so almost no case gets center-cropped.
        tfs.append(ResizeWithPadOrCropd(keys=["image", "label"], spatial_size=patch))

    if train:
        strategy = samp.get("strategy", "posneg")
        if whole_box:
            # the fixed-cube box IS the training sample; no random sub-crop needed
            pass
        elif crop_pancreas:
            # After cropping to the pancreas ROI the organ and tumor already fill most of the
            # volume, so plain random crops still hit the tumor often. Crucially this sampler
            # cannot raise "No sampling location available" the way the pos/neg sampler does on
            # a case whose cropped label comes out empty (tiny/edge pancreas at fine spacing).
            tfs.append(
                RandSpatialCropSamplesd(
                    keys=["image", "label"], roi_size=patch,
                    num_samples=samp["num_samples"], random_center=True, random_size=False,
                )
            )
        elif strategy == "classes":
            # Harder negatives near the pancreas: sample patches CENTERED on each label
            # class by an explicit ratio [bg, pancreas, lesion]. This guarantees
            # pancreas-centered patches (the model must learn normal pancreas, not paint
            # tumor on it) and lesion-centered patches (the rare tumor is actually seen),
            # instead of the binary foreground/background split of RandCropByPosNegLabeld.
            # On tumor-free scans the lesion class is absent and MONAI redistributes to the
            # available classes, so those scans contribute pure hard negatives.
            ratios = samp.get("class_ratios", [1, 1, 2])
            tfs.append(
                RandCropByLabelClassesd(
                    keys=["image", "label"], label_key="label", spatial_size=patch,
                    ratios=ratios, num_classes=3, num_samples=samp["num_samples"],
                    image_key="image", image_threshold=0.0, warn=False,
                )
            )
        else:
            tfs.append(
                RandCropByPosNegLabeld(
                    keys=["image", "label"], label_key="label", spatial_size=patch,
                    pos=samp["pos"], neg=samp["neg"], num_samples=samp["num_samples"],
                    image_key="image", image_threshold=0.0,
                )
            )
        tfs += [
            RandFlipd(keys=["image", "label"], prob=aug.get("flip_prob", 0.2), spatial_axis=0),
            RandFlipd(keys=["image", "label"], prob=aug.get("flip_prob", 0.2), spatial_axis=1),
            RandFlipd(keys=["image", "label"], prob=aug.get("flip_prob", 0.2), spatial_axis=2),
            RandRotate90d(keys=["image", "label"], prob=aug.get("rot90_prob", 0.2), max_k=3),
            RandScaleIntensityd(keys="image", factors=aug.get("scale_intensity_factor", 0.1),
                                prob=aug.get("scale_intensity_prob", 0.15)),
            RandShiftIntensityd(keys="image", offsets=aug.get("shift_intensity_offset", 0.1),
                                prob=aug.get("shift_intensity_prob", 0.15)),
        ]

    tfs.append(EnsureTyped(keys=["image", "label"]))
    return Compose(tfs)
