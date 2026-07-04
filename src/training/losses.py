"""Loss builder — DiceCE (default) or DiceFocal, from config."""
from __future__ import annotations

from monai.losses import DiceCELoss, DiceFocalLoss


def build_loss(cfg: dict):
    l = cfg.get("loss", {})
    common = dict(
        softmax=l.get("softmax", True),
        to_onehot_y=l.get("to_onehot_y", True),
        include_background=l.get("include_background", True),
    )
    if l.get("name") == "dice_focal":
        return DiceFocalLoss(**common)
    return DiceCELoss(
        lambda_dice=l.get("lambda_dice", 1.0),
        lambda_ce=l.get("lambda_ce", 1.0),
        **common,
    )
