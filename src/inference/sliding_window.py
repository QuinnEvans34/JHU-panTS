"""Full-volume sliding-window inference + a validation pass.

Eval is always over the whole volume (never patch-only). Patches run on the compute
device (MPS); the stitched output lives on CPU to relieve MPS memory.
"""
from __future__ import annotations

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
