"""Per-class Dice evaluation (pancreas + lesion reported separately).

Supports two class spaces:
  * 3-class (bg/pancreas/lesion) — the legacy base; aggregate() -> [pancreas, lesion].
  * 5-class anatomy (bg/head/body/tail/lesion) via collapse="anatomy5" — both the argmax
    prediction and the GT are collapsed {head,body,tail}->pancreas, lesion->lesion BEFORE the
    Dice, so the reported numbers stay 3-class and comparable, and best.pt is selected on the
    same collapsed lesion Dice regardless of class space.
"""
from __future__ import annotations

import torch
from monai.data import decollate_batch
from monai.metrics import DiceMetric
from monai.transforms import AsDiscrete


def _collapse_idx(x: torch.Tensor) -> torch.Tensor:
    """Map a 5-class integer index map [1,*] (0..4) to 3-class [1,*]: {1,2,3}->1, 4->2, 0->0."""
    out = torch.zeros_like(x)
    out[(x >= 1) & (x <= 3)] = 1
    out[x == 4] = 2
    return out


class DiceEvaluator:
    """Accumulate per-class Dice. With include_background=False the foreground classes are
    pancreas then lesion, so aggregate() returns [pancreas_dice, lesion_dice]."""

    def __init__(self, num_classes: int = 3, include_background: bool = False,
                 collapse: str | None = None):
        self.num_classes = num_classes
        self.collapse = collapse
        self.eff_classes = 3 if collapse else num_classes
        self.metric = DiceMetric(include_background=include_background,
                                 reduction="mean_batch", ignore_empty=True)
        self.post_pred = AsDiscrete(argmax=True, to_onehot=num_classes)
        self.post_label = AsDiscrete(to_onehot=num_classes)
        self._onehot3 = AsDiscrete(to_onehot=3)

    def reset(self):
        self.metric.reset()

    @torch.no_grad()
    def update(self, logits: torch.Tensor, labels: torch.Tensor):
        preds, gts = [], []
        for lg, lb in zip(decollate_batch(logits), decollate_batch(labels)):
            if self.collapse:
                pi = _collapse_idx(torch.argmax(lg, dim=0, keepdim=True))   # [1,*] pred, collapsed
                gi = _collapse_idx(lb.long())                                # [1,*] GT, collapsed
                preds.append(self._onehot3(pi))
                gts.append(self._onehot3(gi))
            else:
                preds.append(self.post_pred(lg))
                gts.append(self.post_label(lb))
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
