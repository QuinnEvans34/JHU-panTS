#!/usr/bin/env python3
"""Inspect the SuPreM SegResNet checkpoint so we match its exact config.

Tells us: init_filters (from the first conv), the final/head layer name + shape
(so we know what to re-initialize for 3 classes), any 'module.' prefix, and total
params — everything needed to build a checkpoint-compatible SegResNet.

Usage:
  python scripts/inspect_checkpoint.py
  python scripts/inspect_checkpoint.py --path pretrained_weights/supervised_suprem_segresnet_2100.pth
"""
import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils import paths as P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--path", default=None)
    args = ap.parse_args()

    if args.path:
        ckpt_path = Path(args.path)
    else:
        ckpt_path = P.data_paths(load_config(args.config))["pretrained_weights"]
    if not ckpt_path.exists():
        sys.exit(f"checkpoint not found: {ckpt_path}")
    print(f"Loading {ckpt_path}\n")

    ckpt = None
    for wo in (True, False):
        try:
            ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=wo)
            break
        except Exception as e:
            last = e
    if ckpt is None:
        raise last

    # unwrap common container keys
    sd = ckpt
    if isinstance(ckpt, dict):
        for k in ("state_dict", "net", "model", "network_weights", "module"):
            if k in ckpt and isinstance(ckpt[k], dict):
                print(f"(unwrapped container key: '{k}')")
                sd = ckpt[k]
                break

    # strip a 'module.' prefix for readability
    has_prefix = any(str(k).startswith("module.") for k in sd)
    def clean(k):
        return k[len("module."):] if str(k).startswith("module.") else k

    tensors = {clean(k): v for k, v in sd.items() if hasattr(v, "shape")}
    keys = list(tensors.keys())
    total = sum(int(v.numel()) for v in tensors.values())
    print(f"tensors: {len(keys)}   total params: {total:,}   module-prefix: {has_prefix}\n")

    print("--- first 8 keys ---")
    for k in keys[:8]:
        print(f"  {k:45s} {tuple(tensors[k].shape)}")
    print("\n--- last 8 keys (the head) ---")
    for k in keys[-8:]:
        print(f"  {k:45s} {tuple(tensors[k].shape)}")

    # heuristics: init conv (in_channels=1) and final 1x1x1 conv (the head)
    print("\n--- inferred config ---")
    init = [(k, tuple(v.shape)) for k, v in tensors.items()
            if v.ndim == 5 and v.shape[1] == 1]
    if init:
        print(f"  init conv: {init[0][0]} {init[0][1]}  -> init_filters ≈ {init[0][1][0]}")
    finals = [(k, tuple(v.shape)) for k, v in tensors.items()
              if v.ndim == 5 and v.shape[2:] == (1, 1, 1)]
    if finals:
        k, s = finals[-1]
        print(f"  final 1x1x1 conv: {k} {s}  -> pretrained out_channels = {s[0]} (we re-init to 3)")
    print("\nPaste this output back and I'll set the SegResNet config + head-swap to match.")


if __name__ == "__main__":
    main()
