"""Per-class Dice evaluation (pancreas + lesion reported separately)."""
from __future__ import annotations

import torch
from monai.data import decollate_batch
from monai.metrics import DiceMetric
from monai.transforms import AsDiscrete


class DiceEvaluator:
    """Accumulate per-class Dice. With include_background=False and 3 classes,
    aggregate() returns [pancreas_dice, lesion_dice]."""

    def __init__(self, num_classes: int = 3, include_background: bool = False):
        self.num_classes = num_classes
        self.metric = DiceMetric(include_background=include_background,
                                 reduction="mean_batch", ignore_empty=True)
        self.post_pred = AsDiscrete(argmax=True, to_onehot=num_classes)
        self.post_label = AsDiscrete(to_onehot=num_classes)

    def reset(self):
        self.metric.reset()

    @torch.no_grad()
    def update(self, logits: torch.Tensor, labels: torch.Tensor):
        preds = [self.post_pred(p) for p in decollate_batch(logits)]
        gts = [self.post_label(l) for l in decollate_batch(labels)]
        self.metric(y_pred=preds, y=gts)

    def aggregate(self) -> dict:
        d = self.metric.aggregate()
        vals = [float(x) for x in d]
        # class order after dropping background: pancreas (1), lesion (2)
        names = ["pancreas", "lesion"][: len(vals)]
        # NaN = that class absent from the ground truth (ignore_empty) — drop from the mean
        clean = [(n, v) for n, v in zip(names, vals) if v == v]
        out = {n: v for n, v in clean}
        out["mean"] = sum(v for _, v in clean) / len(clean) if clean else 0.0
        return out
