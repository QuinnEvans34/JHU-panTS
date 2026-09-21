"""Build MONAI datasets from the manifest + split id-lists.

Each record maps mask KEYS to on-disk paths; which keys are emitted depends on the
label mode + pancreas resolver (DECOUPLED from each other, per the EXP-26 spec):

  * pancreas_lesion + combined  -> {"pancreas", "lesion"}          (legacy 3-class base)
  * pancreas_lesion + hbt_union -> {"head","body","tail","lesion"} (3-class, robust resolver)
  * anatomy5        (hbt_union)  -> {"head","body","tail","lesion"} (5-class EXP-26)

transforms.py composes the target(s) from these keys.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from monai.data import CacheDataset, Dataset, PersistentDataset

from src.utils import paths as P
from src.data.transforms import build_transforms, mask_key_map, resolver_of

# Bump when the preprocessing/painting SEMANTICS change under an unchanged mode string (e.g. a
# new head/body/tail precedence), so a stale disk cache can never be silently reused (Codex #5).
CACHE_VERSION = "v2-anat"


def _cache_tag(cfg: dict, split_name: str, train: bool) -> str:
    """A folder name that uniquely identifies the preprocessing recipe, so different
    recipes (spacing / patch / crop / whole-box / label-mode / resolver) never share a
    disk cache. Within a tag, PersistentDataset still hashes each case, so changing the
    case list is safe too. label_mode + resolver are included because they change the
    number of mask inputs and the composed target — a stale cache across them would be a
    silent correctness bug (Codex cache-fingerprint requirement)."""
    pre = cfg.get("preprocessing", {})
    samp = cfg.get("sampling", {})
    patch = (samp.get("patch_size") or [96])[0]
    sp = (pre.get("target_spacing") or [1.5])[0]
    wb = int(bool(pre.get("whole_box", False)))
    cn = pre.get("crop_native_margin_vox")
    cp = pre.get("crop_to_pancreas_margin_mm")
    rs = pre.get("roi_source", "union")
    lm = cfg.get("label_mode", "pancreas_lesion")
    pr = resolver_of(cfg)
    return (f"{CACHE_VERSION}_{split_name}_lm{lm}_pr{pr}_sp{sp}_p{patch}_wb{wb}"
            f"_cn{cn}_cp{cp}_rs{rs}_{'tr' if train else 'val'}")


def load_split_ids(splits_dir, name: str) -> list[str]:
    f = Path(splits_dir) / f"{name}.txt"
    if not f.exists():
        raise FileNotFoundError(f"split file not found: {f} (run create_splits.py)")
    return [ln.strip() for ln in f.read_text().splitlines() if ln.strip()]


def build_records(manifest_csv, ids, cfg: dict | None = None) -> list[dict]:
    """Emit one record per case. cfg selects which mask keys/paths to include
    (label_mode + pancreas_resolver); cfg=None keeps the legacy pancreas/lesion behavior."""
    df = pd.read_csv(manifest_csv)
    idset = set(ids)
    df = df[df["case_id"].isin(idset)]
    key_to_col = mask_key_map(cfg or {})     # {record_key: manifest_column}
    records = []
    for _, r in df.iterrows():
        rec = {"image": r["ct_path"], "case_id": r["case_id"]}
        for key, col in key_to_col.items():
            val = r.get(col)
            if isinstance(val, str) and val:
                rec[key] = val
        records.append(rec)
    return records


def get_dataset(cfg: dict, split_name: str, train: bool = True,
                cache="none", limit: int | None = None,
                ids: list | None = None):
    """Return a MONAI dataset for a named split (or an explicit id list via `ids`).

    cache modes:
      "none"  plain Dataset — recompute every access (lowest memory, slowest).
      "ram"   CacheDataset — hold every preprocessed volume in RAM (fast; caps ~a few
              hundred whole-box cases; rebuilt every run). Legacy bool True maps here.
      "disk"  PersistentDataset — cache the deterministic preprocessing to the SSD once,
              reused across runs and resumes. Scales past RAM and survives interruption.
              Random augments still run on the fly each epoch.
    """
    dp = P.data_paths(cfg)
    if ids is None:
        ids = load_split_ids(dp["splits_dir"], split_name)
    if limit:
        ids = ids[:limit]
    records = build_records(dp["manifest"], ids, cfg)
    if not records:
        raise RuntimeError(f"no records for split '{split_name}' — check manifest/splits")
    transform = build_transforms(cfg, train=train)

    mode = ("ram" if cache else "none") if isinstance(cache, bool) else str(cache)

    if mode == "disk":
        base = cfg.get("training", {}).get("cache_dir") or (Path(dp["output_dir"]) / "cache")
        cdir = Path(base) / _cache_tag(cfg, split_name, train)
        cdir.mkdir(parents=True, exist_ok=True)
        # PersistentDataset caches the non-random prefix; it fills lazily on first access,
        # so the first epoch pays the preprocessing cost and every epoch/run after is fast.
        return PersistentDataset(data=records, transform=transform, cache_dir=str(cdir))
    if mode == "ram":
        workers = cfg.get("training", {}).get("num_workers", 4)
        return CacheDataset(data=records, transform=transform, cache_rate=1.0, num_workers=workers)
    return Dataset(data=records, transform=transform)
