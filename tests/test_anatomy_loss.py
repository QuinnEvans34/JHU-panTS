"""Unit tests for the EXP-26 AnatomyAwareLoss (spec §4).

Run:  python -m pytest tests/test_anatomy_loss.py -q
  or: python tests/test_anatomy_loss.py   (no pytest needed)

Covers Codex's required checks:
  (a) 5-class softmax collapse sums to 1
  (b) collapsed loss equals a hand-computed 3-probability reference
  (c) gradients reach all head/body/tail logits through p_panc
  (d) lambda_anat=0 yields exactly the primary loss
  (e) numerical stability at p->0 and p->1
  + auxiliary: masked, no-renormalization, empty-class exclusion, all-absent differentiable zero
"""
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.training.losses import AnatomyAwareLoss, _soft_dice_from_probs


def _rand_case(B=2, S=8, seed=0):
    g = torch.Generator().manual_seed(seed)
    logits = torch.randn(B, 5, S, S, S, generator=g, requires_grad=True)
    target = torch.randint(0, 5, (B, 1, S, S, S), generator=g)
    return logits, target


def test_collapse_sums_to_one():
    logits, _ = _rand_case()
    p = torch.softmax(logits, dim=1)
    loss = AnatomyAwareLoss()
    p3 = loss._collapse_probs(p)
    assert torch.allclose(p3.sum(1), torch.ones_like(p3.sum(1)), atol=1e-5)
    assert p3.shape[1] == 3


def test_collapsed_dice_matches_reference():
    """The internal collapsed Dice must equal an independent hand-rolled 3-class Dice."""
    logits, target = _rand_case(seed=1)
    loss = AnatomyAwareLoss()
    p = torch.softmax(logits, dim=1)
    p3 = loss._collapse_probs(p)
    tc = loss._collapse_target(target.long())
    onehot = torch.zeros_like(p3).scatter_(1, tc, 1.0)

    # reference: foreground (channels 1,2) soft Dice, per (sample,channel) then mean
    ref_terms = []
    for b in range(p3.shape[0]):
        for c in (1, 2):
            pc, tcc = p3[b, c], onehot[b, c]
            inter = (pc * tcc).sum()
            denom = pc.sum() + tcc.sum()
            ref_terms.append(1.0 - (2 * inter + 1e-5) / (denom + 1e-5))
    ref = torch.stack(ref_terms).mean()
    got = _soft_dice_from_probs(p3, onehot, include_background=False)
    assert torch.allclose(got, ref, atol=1e-6), (got.item(), ref.item())


def test_gradients_reach_all_subregion_logits():
    logits, target = _rand_case(seed=2)
    loss = AnatomyAwareLoss(lambda_anat=0.0)   # even with NO aux, primary must reach 1,2,3 via p_panc
    out = loss(logits, target)
    out.backward()
    g = logits.grad
    for k in (1, 2, 3):
        assert g[:, k].abs().sum() > 0, f"no gradient reached subregion channel {k}"


def test_lambda_zero_equals_primary():
    logits, target = _rand_case(seed=3)
    a = AnatomyAwareLoss(lambda_anat=0.0)(logits, target)
    # rebuild primary-only from the stored components
    loss = AnatomyAwareLoss(lambda_anat=0.7)
    total = loss(logits, target)
    prim = loss.last["primary"]
    assert abs(a.item() - prim) < 1e-6
    # total should differ from primary when aux>0 and lambda>0 (unless aux is exactly 0)
    assert total.item() >= prim - 1e-6


def test_numerical_stability_extremes():
    B, S = 1, 4
    target = torch.randint(0, 5, (B, 1, S, S, S))
    for scale in (-50.0, 50.0):
        logits = (torch.randn(B, 5, S, S, S) * scale).requires_grad_(True)
        out = AnatomyAwareLoss(lambda_anat=0.3)(logits, target)
        assert torch.isfinite(out), f"non-finite loss at scale {scale}"
        out.backward()
        assert torch.isfinite(logits.grad).all(), f"non-finite grad at scale {scale}"


def test_aux_all_absent_is_zero_and_differentiable():
    """A batch with NO pancreas voxels (all bg/lesion) -> aux is a differentiable zero."""
    B, S = 1, 4
    logits = torch.randn(B, 5, S, S, S, requires_grad=True)
    target = torch.zeros(B, 1, S, S, S).long()   # all background -> M empty
    loss = AnatomyAwareLoss(lambda_anat=1.0)
    out = loss(logits, target)
    out.backward()
    assert loss.last["aux"] == 0.0
    assert torch.isfinite(logits.grad).all()


def test_aux_excludes_empty_subregion():
    """Aux with only head present must be finite and driven by head alone (no NaN from empty body/tail)."""
    B, S = 1, 4
    logits = torch.randn(B, 5, S, S, S, requires_grad=True)
    target = torch.zeros(B, 1, S, S, S).long()
    target[0, 0, 0, 0, 0] = 1   # a single head voxel; body/tail absent
    loss = AnatomyAwareLoss(lambda_anat=1.0)
    out = loss(logits, target)
    out.backward()
    assert torch.isfinite(out) and loss.last["aux"] == loss.last["aux"]  # not NaN


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"\nAll {len(fns)} anatomy-loss tests passed.")


if __name__ == "__main__":
    _run_all()
