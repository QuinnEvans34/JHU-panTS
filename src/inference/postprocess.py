"""CADe post-processing: clean a predicted label map to cut false positives.

Keeps the largest connected component of the pancreas and of the lesion, and drops a
lesion prediction whose volume is below a threshold (scattered specks are almost always
false alarms). Operates on a (H, W, D) integer map: 0 = background, 1 = pancreas, 2 = lesion.
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


def postprocess(pred: np.ndarray, spacing, lesion_min_mm3: float = 50.0,
                largest_lesion: bool = True, largest_pancreas: bool = True) -> np.ndarray:
    """Clean a predicted label map. Removed lesion voxels are demoted to pancreas
    (they sit inside it); removed pancreas voxels are demoted to background."""
    out = pred.copy()
    vox_mm3 = float(np.prod(spacing))

    if largest_pancreas:
        panc = out == 1
        if panc.any():
            keep = keep_largest_component(panc)
            out[panc & ~keep] = 0

    les = out == 2
    if les.any():
        keep = keep_largest_component(les) if largest_lesion else les.astype(bool)
        if int(keep.sum()) * vox_mm3 < lesion_min_mm3:
            keep = np.zeros_like(keep)  # too small to be a real tumor
        out[les & ~keep] = 1  # demote dropped lesion voxels to pancreas
    return out
