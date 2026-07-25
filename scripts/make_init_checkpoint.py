#!/usr/bin/env python3
"""Build the ONE frozen 5-class SuPreM-initialized checkpoint that BOTH EXP-26 arms load.

This is the equivalence control: 26A and 26B must start from byte-identical weights so the
only difference between them is lambda_anat. Run this once; then launch both arms with
`--init-weights <this file>`. train.py records the file's SHA-256 in each run's checkpoint
metadata, so you can prove after the fact that both arms used the same init.

Usage:
  python scripts/make_init_checkpoint.py --out outputs/checkpoints/exp26_init_5ch.pt
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config
from src.utils.seed import set_seed
from src.utils import paths as P
from src.models.segresnet import save_init_checkpoint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--out", default="outputs/checkpoints/exp26_init_5ch.pt")
    ap.add_argument("--out-channels", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    cfg = load_config(args.config)
    cfg["model"]["out_channels"] = args.out_channels
    cfg["label_mode"] = "anatomy5"
    set_seed(args.seed)   # deterministic head re-init
    dp = P.data_paths(cfg)
    sha = save_init_checkpoint(cfg, args.out, dp["pretrained_weights"])
    print(f"\nInit checkpoint ready.\n  path : {args.out}\n  sha256: {sha}\n"
          f"Launch BOTH arms with --init-weights {args.out} (same file = identical start).")


if __name__ == "__main__":
    main()
