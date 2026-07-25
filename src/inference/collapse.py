"""Shared 5-class -> 3-class collapse helpers for the anatomy model.

Every eval/analysis/export path that assumes a 3-class (bg/pancreas/lesion) output must run
predictions through these first when the model is 5-class (anatomy5), so `probs[2]` / `pred==2`
keep meaning "lesion". Keeping the mapping in ONE place avoids the class-id-literal drift Codex
warned about (head=1 would otherwise be mistaken for pancreas).

Collapse: bg=0, pancreas={head,body,tail}, lesion. For 5-class probabilities the pancreas
probability is the SUM p_head+p_body+p_tail (the correct marginal pancreas probability).
"""
from __future__ import annotations

import numpy as np


def is_anatomy5(cfg: dict) -> bool:
    return cfg.get("label_mode") == "anatomy5"


def collapse_probs_np(probs: np.ndarray) -> np.ndarray:
    """(C,*) softmax probs -> (3,*) [bg, pancreas, lesion]. Pass-through if already 3-class."""
    c = probs.shape[0]
    if c == 3:
        return probs
    if c == 5:
        bg = probs[0:1]
        panc = probs[1:4].sum(axis=0, keepdims=True)
        les = probs[4:5]
        return np.concatenate([bg, panc, les], axis=0)
    raise ValueError(f"collapse_probs_np expects 3 or 5 channels, got {c}")


def collapse_label_np(lab: np.ndarray, label_mode: str = "anatomy5") -> np.ndarray:
    """Integer label map -> collapsed {0=bg, 1=pancreas, 2=lesion}.

    The mode is DECLARED by the caller, never inferred from observed values: an anatomy5 case
    with no lesion and no tail voxels has max label 2 (body), which must map to pancreas, not
    lesion — inferring from `max<=2` would silently mislabel it (Codex blocking issue #2).
      anatomy5:        {1,2,3}->1 (pancreas), 4->2 (lesion).
      pancreas_lesion: already 3-class -> pass through unchanged.
    """
    lab = np.asarray(lab)
    if label_mode == "anatomy5":
        out = np.zeros_like(lab)
        out[(lab >= 1) & (lab <= 3)] = 1
        out[lab == 4] = 2
        return out
    return lab
