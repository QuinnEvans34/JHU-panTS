"""SegResNet (MONAI) + SuPreM transfer loader.

Config matched to the SuPreM checkpoint (verified via scripts/inspect_checkpoint.py):
init_filters=16, GroupNorm, blocks_down=(1,2,2,4), blocks_up=(1,1,1), 4.70M params.
The checkpoint's 32-class head (conv_final.2.conv) is re-initialized to out_channels=3.
"""
from __future__ import annotations

from pathlib import Path

import torch
from monai.networks.nets import SegResNet


def build_model(cfg: dict) -> SegResNet:
    m = cfg["model"]
    dropout = m.get("dropout_prob", 0.0)
    norm = m.get("norm", "group")
    # GroupNorm needs num_groups; MONAI wants it as a tuple (matches SuPreM: 8 groups)
    if isinstance(norm, str) and norm.lower() == "group":
        norm = ("GROUP", {"num_groups": int(m.get("num_groups", 8))})
    return SegResNet(
        spatial_dims=3,
        init_filters=int(m.get("init_filters", 16)),
        in_channels=int(m.get("in_channels", 1)),
        out_channels=int(m.get("out_channels", 3)),
        blocks_down=tuple(m.get("blocks_down", (1, 2, 2, 4))),
        blocks_up=tuple(m.get("blocks_up", (1, 1, 1))),
        norm=norm,
        dropout_prob=(dropout if dropout else None),
    )


def load_suprem(net: SegResNet, ckpt_path, verbose: bool = True) -> SegResNet:
    """Load SuPreM weights into a checkpoint-compatible SegResNet.

    Loads every shape-matching tensor; the mismatched head (32 -> 3 classes) is left
    at its fresh initialization. Strips the 'module.' prefix and unwraps the 'net' key.
    """
    ckpt_path = Path(ckpt_path)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"pretrained weights not found: {ckpt_path}")
    ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    sd = ckpt["net"] if isinstance(ckpt, dict) and "net" in ckpt else ckpt
    sd = {(k[len("module."):] if str(k).startswith("module.") else k): v for k, v in sd.items()}

    model_sd = net.state_dict()
    to_load, reinit = {}, []
    for k, v in sd.items():
        if k in model_sd and hasattr(v, "shape") and tuple(v.shape) == tuple(model_sd[k].shape):
            to_load[k] = v
        elif k in model_sd:
            reinit.append(k)  # present but wrong shape (the head)
    net.load_state_dict(to_load, strict=False)
    if verbose:
        print(f"[SuPreM] loaded {len(to_load)}/{len(model_sd)} tensors; "
              f"re-initialized head/mismatch: {reinit or 'none'}")
    return net


def set_encoder_requires_grad(net: SegResNet, flag: bool) -> None:
    """Freeze/unfreeze the encoder (convInit + down_layers) for warm-up fine-tuning."""
    for name, p in net.named_parameters():
        if name.startswith("convInit") or name.startswith("down_layers"):
            p.requires_grad = flag
