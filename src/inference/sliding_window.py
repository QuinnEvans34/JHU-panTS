"""Full-volume sliding-window inference + a validation pass.

Eval is always over the whole volume (never patch-only). Patches run on the compute
device (MPS); the stitched output lives on CPU to relieve MPS memory.
"""
from __future__ import annotations

import itertools

import numpy as np
import torch
from monai.inferers import sliding_window_inference


def predict_volume(model, image, cfg: dict, device):
    inf = cfg["inference"]
    return sliding_window_inference(
        inputs=image,
        roi_size=tuple(inf["sw_roi_size"]),
        sw_batch_size=int(inf.get("sw_batch_size", 2)),
        predictor=model,
        overlap=float(inf.get("overlap", 0.5)),
        mode=inf.get("blend_mode", "gaussian"),
        sw_device=device,
        device=torch.device(inf.get("stitch_device", "cpu")),
    )


@torch.no_grad()
def predict_probs_tta(model, image, cfg: dict, device, flip_axes=(0, 1, 2)) -> np.ndarray:
    """Test-time augmentation over flips. Runs sliding-window inference on every flip
    combination of the spatial axes, un-flips each prediction back to the original
    orientation, and averages the SOFTMAX PROBABILITIES (not logits, which is the more
    principled average). Returns a (C, H, W, D) numpy array of averaged probabilities.

    Flips are label-preserving for segmentation, so this needs no retraining and only
    costs extra forward passes. With all three axes there are 2**3 = 8 views (including
    the identity). The volume tensor is (1, C, H, W, D), so spatial axis a maps to tensor
    dim a + 2.
    """
    combos = []
    for r in range(len(flip_axes) + 1):
        combos.extend(itertools.combinations(flip_axes, r))  # includes the empty (identity) view

    acc = None
    for c in combos:
        dims = [ax + 2 for ax in c]
        img_v = torch.flip(image, dims=dims) if dims else image
        logits = predict_volume(model, img_v, cfg, device)      # stitched on CPU
        probs = torch.softmax(logits, dim=1)
        if dims:
            probs = torch.flip(probs, dims=dims)                # un-flip back to original frame
        acc = probs if acc is None else acc + probs
    acc = acc / len(combos)
    return acc[0].cpu().numpy()


@torch.no_grad()
def validate(model, val_loader, evaluator, cfg: dict, device) -> dict:
    """Run sliding-window inference over the val set and return per-class Dice."""
    model.eval()
    evaluator.reset()
    for batch in val_loader:
        img = batch["image"].to(device)
        logits = predict_volume(model, img, cfg, device)  # stitched on CPU
        evaluator.update(logits, batch["label"])          # label stays on CPU
    model.train()
    return evaluator.aggregate()
