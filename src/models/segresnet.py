"""SegResNet (MONAI) + SuPreM transfer loader.

Config matched to the SuPreM checkpoint (verified via scripts/inspect_checkpoint.py):
init_filters=16, GroupNorm, blocks_down=(1,2,2,4), blocks_up=(1,1,1), 4.70M params.
The checkpoint's 32-class head (conv_final.2.conv) is re-initialized to out_channels=3.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import torch
from monai.networks.nets import SegResNet


def sha256_file(path) -> str:
    """SHA-256 of a file — the identity we record so both EXP-26 arms provably start from the
    same weights (Codex equivalence control)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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


def load_suprem_asserting_head_only(net: SegResNet, ckpt_path) -> list:
    """load_suprem, but ASSERT the only tensors left at fresh init are the final head
    (conv_final...conv weight+bias). Any other skipped tensor means the architecture drifted
    from the checkpoint and the transfer is silently broken — abort instead. Returns the
    re-init key list."""
    ckpt_path = Path(ckpt_path)
    ckpt = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
    sd = ckpt["net"] if isinstance(ckpt, dict) and "net" in ckpt else ckpt
    sd = {(k[len("module."):] if str(k).startswith("module.") else k): v for k, v in sd.items()}
    model_sd = net.state_dict()
    to_load, reinit = {}, []
    for k, v in sd.items():
        if k in model_sd and hasattr(v, "shape") and tuple(v.shape) == tuple(model_sd[k].shape):
            to_load[k] = v
        elif k in model_sd:
            reinit.append(k)
    # tensors in the model but absent from the checkpoint entirely also stay at init
    missing = [k for k in model_sd if k not in sd]
    net.load_state_dict(to_load, strict=False)
    # The ONLY tensors allowed to remain at fresh init are the exact final-head conv weight+bias.
    # A looser "conv_final in key" rule would tolerate an unrelated missing final-block tensor.
    allowed = {"conv_final.2.conv.weight", "conv_final.2.conv.bias"}
    unexpected = [k for k in (reinit + missing) if k not in allowed]
    assert not unexpected, (f"SuPreM load left non-head tensors at init: {unexpected[:8]} — "
                            f"architecture mismatch, transfer would be silently broken.")
    head = set(reinit + missing) & allowed
    # positively assert BOTH expected head tensors are the ones re-initialized (Codex note):
    assert head == allowed, (f"expected exactly {sorted(allowed)} to be re-initialized on SuPreM load, "
                             f"got {sorted(head)} — the head is not the 32->{'?'} conv we think it is.")
    print(f"[SuPreM] loaded {len(to_load)}/{len(model_sd)} tensors; head re-init (verified): {sorted(head)}")
    return reinit + missing


def save_init_checkpoint(cfg: dict, out_path, weights_path=None) -> str:
    """Build the model, load SuPreM (head re-init to out_channels), and save the FULL model
    state_dict to out_path. Both EXP-26 arms load this exact file, so their weights are
    byte-identical at step 0. Returns the file's SHA-256. Seed the RNG before calling so the
    re-initialized head is deterministic."""
    net = build_model(cfg)
    if weights_path is not None and Path(weights_path).exists():
        load_suprem_asserting_head_only(net, weights_path)
    else:
        print(f"[init] no SuPreM weights at {weights_path} — saving a from-scratch init")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": net.state_dict(),
                "out_channels": int(cfg["model"]["out_channels"]),
                "label_mode": cfg.get("label_mode")}, str(out_path))
    sha = sha256_file(out_path)
    print(f"[init] saved {out_path}  out_channels={cfg['model']['out_channels']}  sha256={sha}")
    return sha


def load_init_weights(net: SegResNet, path) -> str:
    """Strict-load a frozen init checkpoint (from save_init_checkpoint) into net. Returns the
    file SHA-256 so train.py can record it in the run's checkpoint metadata."""
    blob = torch.load(str(path), map_location="cpu", weights_only=False)
    sd = blob["model"] if isinstance(blob, dict) and "model" in blob else blob
    net.load_state_dict(sd, strict=True)
    return sha256_file(path)


def set_encoder_requires_grad(net: SegResNet, flag: bool) -> None:
    """Freeze/unfreeze the encoder (convInit + down_layers) for warm-up fine-tuning."""
    for name, p in net.named_parameters():
        if name.startswith("convInit") or name.startswith("down_layers"):
            p.requires_grad = flag
