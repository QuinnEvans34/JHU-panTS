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


def _soft_dice_from_probs(probs, target_onehot, include_background, snr=1e-5, sdr=1e-5):
    """Soft Dice loss computed DIRECTLY on probabilities (no softmax inside — the caller
    already softmaxed once). Matches MONAI DiceLoss(reduction='mean', squared_pred=False,
    batch=False): per (sample, channel) Dice, then mean. probs/target: [B, C, *spatial]."""
    if not include_background:
        probs = probs[:, 1:]
        target_onehot = target_onehot[:, 1:]
    dims = tuple(range(2, probs.dim()))
    inter = (probs * target_onehot).sum(dims)
    denom = probs.sum(dims) + target_onehot.sum(dims)
    dice = (2.0 * inter + snr) / (denom + sdr)
    return (1.0 - dice).mean()


class AnatomyAwareLoss(torch.nn.Module):
    """EXP-26 anatomy-aware loss for the 5-class model (bg, head, body, tail, lesion).

    Deliberate probability-based reformulation (NOT MONAI DiceFocal — see
    docs/spec-exp26-anatomy-aware.md). The SAME primary loss runs in both arms, so the
    26B-vs-26A comparison is valid regardless; 26A (lambda_anat=0) is the sole baseline.

    Softmax is computed ONCE. Then:
      collapsed probs: p_bg=p0, p_panc=p1+p2+p3, p_lesion=p4  (gradients reach head/body/tail
                       logits through p_panc).
      PRIMARY (both arms):
        * soft Dice on the collapsed 3-class probs vs collapsed one-hot GT, background excluded;
        * foreground-only probability focal: at each NON-BACKGROUND target voxel, using the
          collapsed prob of that voxel's true class p_c, -(1-p_c)^gamma * log(clamp(p_c, eps, 1)),
          averaged over the count of non-background target voxels (guarded to a differentiable
          zero when a batch has none).
      AUXILIARY (weighted by lambda_anat; computed in BOTH arms, x0 in 26A):
        masked per-class soft Dice for head/body/tail over M = non-lesion pancreas voxels,
        using the RAW 5-class softmax probs (no renormalization, so leaking a pancreas voxel
        to bg/lesion is still penalized). Independent per class, then averaged EQUALLY; a
        subregion empty in a sample is excluded from that mean; all-absent -> differentiable zero.

    Target is the integer 5-class label map [B, 1, *spatial] (values 0..4).
    """

    def __init__(self, num_classes: int = 5, gamma: float = 2.0,
                 lambda_dice: float = 1.0, lambda_focal: float = 1.0,
                 lambda_anat: float = 0.0, eps: float = 1e-7,
                 snr: float = 1e-5, sdr: float = 1e-5):
        super().__init__()
        assert num_classes == 5, "AnatomyAwareLoss is defined for the 5-class anatomy model"
        self.gamma = float(gamma)
        self.lambda_dice = float(lambda_dice)
        self.lambda_focal = float(lambda_focal)
        self.lambda_anat = float(lambda_anat)
        self.eps = float(eps)
        self.snr, self.sdr = float(snr), float(sdr)
        self.last = {}   # populated each forward for the smoke-scale / gradient diagnostics

    def _collapse_probs(self, p):
        # p: [B,5,*] -> [B,3,*] = [bg, panc=head+body+tail, lesion]
        p_bg = p[:, 0:1]
        p_panc = p[:, 1:2] + p[:, 2:3] + p[:, 3:4]
        p_les = p[:, 4:5]
        return torch.cat([p_bg, p_panc, p_les], dim=1)

    def _collapse_target(self, t):
        # t: [B,1,*] integer in 0..4 -> collapsed integer in {0,1,2}
        tc = torch.zeros_like(t)
        tc[(t >= 1) & (t <= 3)] = 1
        tc[t == 4] = 2
        return tc  # [B,1,*]

    def forward(self, logits, target):
        p = torch.softmax(logits, dim=1)                      # [B,5,*] — the ONE softmax
        t = target.long()
        if t.dim() == p.dim() - 1:                            # [B,*] -> [B,1,*]
            t = t.unsqueeze(1)

        # ---- collapsed 3-class primary ----
        p3 = self._collapse_probs(p)                          # [B,3,*]
        tc = self._collapse_target(t)                         # [B,1,*] in {0,1,2}
        onehot3 = torch.zeros_like(p3).scatter_(1, tc, 1.0)   # [B,3,*]
        dice = _soft_dice_from_probs(p3, onehot3, include_background=False,
                                     snr=self.snr, sdr=self.sdr)

        # foreground-only probability focal (denominator = non-background target voxels)
        p_true = p3.gather(1, tc)                             # [B,1,*] prob of the true class
        fg = (tc != 0)                                        # non-background target voxels
        n_fg = fg.sum()
        if n_fg > 0:
            pt = p_true.clamp(self.eps, 1.0)
            focal_vox = -((1.0 - pt).clamp(min=0.0) ** self.gamma) * torch.log(pt)
            focal = (focal_vox * fg).sum() / n_fg
        else:
            focal = p.sum() * 0.0                             # differentiable zero
        primary = self.lambda_dice * dice + self.lambda_focal * focal

        # ---- auxiliary masked per-class Dice for head/body/tail ----
        M = ((t >= 1) & (t <= 3)).to(p.dtype)                 # [B,1,*] non-lesion pancreas voxels
        dims = tuple(range(2, p.dim()))
        num = p.sum() * 0.0                                   # differentiable-zero seeds
        den = p.sum() * 0.0
        for k in (1, 2, 3):
            tk = (t == k).to(p.dtype) * M                     # target for subregion k within M
            pk = p[:, k:k + 1] * M                            # RAW prob within M (no renormalization)
            inter = (pk * tk).sum(dims)                       # [B]
            denom = pk.sum(dims) + tk.sum(dims)               # [B]
            present = (tk.sum(dims) > 0).to(p.dtype)          # [B] subregion present in this sample
            dice_k = (2.0 * inter + self.snr) / (denom + self.sdr)
            loss_k = (1.0 - dice_k)                           # [B]
            num = num + (loss_k * present).sum()
            den = den + present.sum()
        aux = num / den if den.detach().item() > 0 else p.sum() * 0.0

        total = primary + self.lambda_anat * aux
        self.last = {"primary": float(primary.detach()), "dice": float(dice.detach()),
                     "focal": float(focal.detach()), "aux": float(aux.detach())}
        return total


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

    # EXP-26 anatomy-aware: 5-class model, collapsed primary + masked head/body/tail auxiliary.
    if cfg.get("label_mode") == "anatomy5" or l.get("name") == "anatomy_aware":
        return AnatomyAwareLoss(
            num_classes=int(cfg.get("model", {}).get("out_channels", 5)),
            gamma=float(l.get("focal_gamma", 2.0)),
            lambda_dice=float(l.get("lambda_dice", 1.0)),
            lambda_focal=float(l.get("lambda_focal", 1.0)),
            lambda_anat=float(l.get("lambda_anat", 0.0)),
        )

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
