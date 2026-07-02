"""Resolve concrete dataset / output file paths from a loaded config.

On-disk layout (PanTS, confirmed):
    <pants_root>/ImageTr/<case_id>/ct.nii.gz
    <pants_root>/ImageTe/<case_id>/ct.nii.gz
    <pants_root>/LabelAll/<case_id>/segmentations/*.nii.gz
    <pants_root>/metadata.xlsx
"""
from __future__ import annotations

from pathlib import Path


def data_paths(cfg: dict) -> dict:
    """Return the key dataset + output directories/files as Path objects."""
    p = cfg["paths"]
    root = Path(p["pants_root"])
    return {
        "root": root,
        "images_train": root / p.get("images_train", "ImageTr"),
        "images_test": root / p.get("images_test", "ImageTe"),
        "labels": root / p.get("labels", "LabelAll"),
        "metadata": root / p.get("metadata", "metadata.xlsx"),
        "manifest": Path(p["manifest"]),
        "splits_dir": Path(p["splits_dir"]),
        "output_dir": Path(p["output_dir"]),
        "pretrained_weights": Path(p["pretrained_weights"]),
    }


def case_ct_path(dp: dict, case_id: str, split: str = "train") -> Path:
    base = dp["images_train"] if split == "train" else dp["images_test"]
    return base / case_id / "ct.nii.gz"


def case_seg_dir(dp: dict, case_id: str) -> Path:
    return dp["labels"] / case_id / "segmentations"


def ensure_output_dirs(dp: dict) -> None:
    """Create the output/splits/manifest directories (idempotent)."""
    for d in (dp["output_dir"], dp["splits_dir"], dp["manifest"].parent):
        Path(d).mkdir(parents=True, exist_ok=True)
