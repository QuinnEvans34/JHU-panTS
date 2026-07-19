"""Loss builder: DiceCE (default) or DiceFocal, from config.

Knobs (all optional, defaults preserve prior behavior):
  loss.name                 "dice_focal" | "dice_ce"
  loss.include_background    include the background class in the loss. Default is
                             FALSE (bg0), the project's locked best base: excluding
                             background keeps gradient on the tiny lesion. Flipping it
                             TRUE was tested (EXP-07) as an over-prediction fix and
                             REJECTED — it left raw specificity at 8% and cost lesion
                             Dice — so leave it False unless re-running that ablation.
  loss.focal_gamma           focal focusing parameter (DiceFocal only, default 2.0).
  loss.lambda_dice           weight on the Dice term (default 1.0).
  loss.lambda_focal          weight on the focal term (DiceFocal only, default 1.0).
  loss.lambda_ce             weight on the cross-entropy term (DiceCE only, default 1.0).
  loss.class_weights         optional per-class weights [bg, pancreas, lesion]; if the
                             include-background run swings toward under-predicting the
                             lesion, up-weight the lesion here to pull it back.
"""
from __future__ import annotations

import torch
from monai.losses import DiceCELoss, DiceFocalLoss, TverskyLoss, FocalLoss


class TverskyFocalLoss(torch.nn.Module):
    """Tversky (penalize FALSE POSITIVES to stop over-segmentation) + a Focal term
    (keeps the tiny/rare lesion in focus). EXP-18: the clean model DETECTS tumors (95%)
    but OVER-SEGMENTS them 3-13x, which caps Dice and drives low specificity. Tversky with
    alpha>beta punishes over-painting; the focal term guards the small-tumor recall Tversky
    alone might trade away."""

    def __init__(self, common: dict, alpha: float, beta: float, gamma: float,
                 lambda_tversky: float, lambda_focal: float, weight=None):
        super().__init__()
        self.tversky = TverskyLoss(alpha=alpha, beta=beta, **common)  # no class-weight arg on TverskyLoss
        fk = dict(gamma=gamma, include_background=common["include_background"],
                  to_onehot_y=common["to_onehot_y"], use_softmax=common["softmax"])
        if weight is not None:
            fk["weight"] = weight
        self.focal = FocalLoss(**fk)
        self.lt, self.lf = lambda_tversky, lambda_focal

    def forward(self, pred, target):
        return self.lt * self.tversky(pred, target) + self.lf * self.focal(pred, target)


def build_loss(cfg: dict):
    l = cfg.get("loss", {})
    weights = l.get("class_weights")
    weight = torch.tensor(weights, dtype=torch.float32) if weights else None
    common = dict(
        softmax=l.get("softmax", True),
        to_onehot_y=l.get("to_onehot_y", True),
        include_background=l.get("include_background", False),  # bg0 = locked best base (EXP-07 rejected bg1)
    )

    # EXP-18: Tversky family — alpha weights FALSE POSITIVES, beta weights false negatives.
    # For OVER-segmentation (our problem), raise alpha (e.g. 0.7) so painting extra lesion is punished.
    if l.get("name") in ("tversky", "tversky_focal"):
        alpha = float(l.get("tversky_alpha", 0.7))
        beta = float(l.get("tversky_beta", 0.3))
        if l.get("name") == "tversky":
            return TverskyLoss(alpha=alpha, beta=beta, **common)   # pure Tversky (no class-weight arg)
        return TverskyFocalLoss(common, alpha, beta,
                                gamma=l.get("focal_gamma", 2.0),
                                lambda_tversky=l.get("lambda_dice", 1.0),
                                lambda_focal=l.get("lambda_focal", 1.0),
                                weight=weight)

    if l.get("name") == "dice_focal":
        kwargs = dict(
            gamma=l.get("focal_gamma", 2.0),
            lambda_dice=l.get("lambda_dice", 1.0),
            lambda_focal=l.get("lambda_focal", 1.0),
            **common,
        )
        if weight is not None:          # only pass when set, keeps default path untouched
            kwargs["weight"] = weight
        return DiceFocalLoss(**kwargs)

    kwargs = dict(
        lambda_dice=l.get("lambda_dice", 1.0),
        lambda_ce=l.get("lambda_ce", 1.0),
        **common,
    )
    if weight is not None:
        kwargs["weight"] = weight
    return DiceCELoss(**kwargs)
