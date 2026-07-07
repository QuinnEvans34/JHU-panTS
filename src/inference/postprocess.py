"""CADe post-processing: clean a predicted label map to cut false positives.

Three levers, each independently toggleable:
  1. Keep the largest connected component of the pancreas and of the lesion.
  2. Drop a lesion prediction whose volume is below a threshold (scattered specks
     are almost always false alarms).
  3. Anatomical constraint: a pancreatic lesion must sit inside or right next to the
     predicted pancreas. Lesion components that float away from the pancreas are
     demoted, since a pancreatic tumor cannot live out in unrelated tissue.

Operates on a (H, W, D) integer map: 0 = background, 1 = pancreas, 2 = lesion.
"""
from __future__ import annotations

import numpy as np
from skimage import measure


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    """Return a boolean mask with only the largest connected component."""
    mask = mask.astype(bool)
    labeled = measure.label(mask)
    if labeled.max() == 0:
        return mask
    counts = np.bincount(labeled.ravel())
    counts[0] = 0  # ignore background
    return labeled == counts.argmax()


def _dilate(mask: np.ndarray, iterations: int) -> np.ndarray:
    """Binary dilation by `iterations` voxels. Falls back to the input if scipy
    is unavailable or iterations <= 0."""
    if iterations <= 0:
        return mask.astype(bool)
    try:
        from scipy import ndimage
        return ndimage.binary_dilation(mask, iterations=iterations)
    except Exception:
        return mask.astype(bool)


def constrain_lesion_to_pancreas(pred: np.ndarray, spacing,
                                 margin_mm: float = 10.0) -> np.ndarray:
    """Demote lesion voxels whose connected component does not touch the pancreas
    (within `margin_mm`). Removed lesion voxels go to background, because a lesion
    far from the pancreas is a spurious blob, not part of the organ.

    If the model predicted no pancreas at all, the constraint is skipped (there is
    nothing to anchor to, so we do not want to erase every lesion)."""
    out = pred.copy()
    panc = out == 1
    les = out == 2
    if not les.any() or not panc.any():
        return out

    vox = float(min(spacing))
    iters = int(np.ceil(margin_mm / vox)) if vox > 0 else 0
    near_pancreas = _dilate(panc, iters)

    labeled = measure.label(les)
    for cc in range(1, labeled.max() + 1):
        comp = labeled == cc
        if not (comp & near_pancreas).any():
            out[comp] = 0  # lesion component floats away from pancreas -> false positive
    return out


def postprocess(pred: np.ndarray, spacing, lesion_min_mm3: float = 50.0,
                largest_lesion: bool = True, largest_pancreas: bool = True,
                lesion_within_pancreas_mm: float | None = None) -> np.ndarray:
    """Clean a predicted label map.

    Order: pancreas largest-CC, then the anatomical lesion constraint (if enabled),
    then lesion largest-CC and the volume threshold. Removed lesion voxels are demoted
    to pancreas when they sit inside it (largest-CC/threshold steps) or to background
    when they float away from it (anatomical step)."""
    out = pred.copy()
    vox_mm3 = float(np.prod(spacing))

    if largest_pancreas:
        panc = out == 1
        if panc.any():
            keep = keep_largest_component(panc)
            out[panc & ~keep] = 0

    if lesion_within_pancreas_mm is not None:
        out = constrain_lesion_to_pancreas(out, spacing, margin_mm=lesion_within_pancreas_mm)

    les = out == 2
    if les.any():
        keep = keep_largest_component(les) if largest_lesion else les.astype(bool)
        if int(keep.sum()) * vox_mm3 < lesion_min_mm3:
            keep = np.zeros_like(keep)  # too small to be a real tumor
        out[les & ~keep] = 1  # demote dropped lesion voxels to pancreas
    return out
