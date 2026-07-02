"""Load and resolve the YAML experiment config.

Usage:
    from src.utils.config import load_config, get
    cfg = load_config("configs/level45.yaml")
    lr = get(cfg, "optimizer.lr_transfer", 1e-4)

The dataset root can be overridden without editing the YAML:
    PANTS_ROOT=/some/other/path python scripts/build_manifest.py
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

# repo root = .../Neuro-data  (this file is at src/utils/config.py)
REPO_ROOT = Path(__file__).resolve().parents[2]


def load_config(path) -> dict:
    """Read a YAML config and resolve its paths. `path` may be relative to the repo root."""
    path = Path(path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg["_config_path"] = str(path)
    cfg["_repo_root"] = str(REPO_ROOT)
    return _resolve_paths(cfg)


def _resolve_paths(cfg: dict) -> dict:
    p = cfg.get("paths", {})
    # dataset root: env var wins, else the YAML value (kept as-is; it's an absolute drive path)
    p["pants_root"] = os.environ.get("PANTS_ROOT", p.get("pants_root"))
    # output-side paths are made absolute under the repo (all git-ignored)
    for key in ("manifest", "splits_dir", "output_dir", "pretrained_weights"):
        val = p.get(key)
        if val and not os.path.isabs(val):
            p[key] = str(REPO_ROOT / val)
    cfg["paths"] = p
    return cfg


def get(cfg: dict, dotted: str, default=None):
    """Fetch a nested value with a dotted key, e.g. get(cfg, 'model.out_channels')."""
    cur = cfg
    for key in dotted.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur
