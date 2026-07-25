"""Training helpers used by scripts/train.py — the plumbing around the training loop.

Five pieces, each a small function the trainer calls once at setup (or per checkpoint):
  * get_device        pick the compute device — Apple-Silicon GPU ("mps"), else CUDA, else CPU.
  * build_optimizer   AdamW over ALL model params (transfer LR vs scratch LR from the config).
  * build_scheduler   the learning-rate schedule: linear warmup, then cosine decay to a floor.
  * save_checkpoint   ATOMIC write (temp file + os.replace) of weights+optimizer+scheduler+step+meta.
  * load_checkpoint   restore a checkpoint to resume; strict mode (EXP-26) fails closed on any
                      missing/mismatched optimizer or scheduler state so a resume can't change the run.

The model's learned weights + this optimizer/scheduler state are what a checkpoint (.pt) contains.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import torch


def get_device(cfg: dict) -> torch.device:
    d = cfg.get("device", "cpu")
    if d == "mps" and torch.backends.mps.is_available():
        return torch.device("mps")
    if d == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_optimizer(cfg: dict, model, transfer: bool):
    o = cfg["optimizer"]
    lr = float(o["lr_transfer"]) if transfer else float(o["lr_scratch"])
    wd = float(o.get("weight_decay", 1e-5))
    # Include ALL params (not just currently-trainable ones) so the optimizer's shape does
    # not change when the encoder unfreezes. Frozen params have requires_grad=False, so their
    # grad stays None and AdamW skips them; when unfrozen they simply start getting updates.
    # This keeps checkpoints resume-compatible AND ensures the encoder actually trains after
    # the warm-up freeze (it previously never entered the optimizer).
    return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd), lr


def build_scheduler(optimizer, warmup_iters: int, total_iters: int, min_lr_ratio: float):
    def fn(step):
        if step < warmup_iters:
            return (step + 1) / max(1, warmup_iters)
        p = (step - warmup_iters) / max(1, total_iters - warmup_iters)
        return min_lr_ratio + (1 - min_lr_ratio) * 0.5 * (1 + math.cos(math.pi * min(1.0, p)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, fn)


def save_checkpoint(path, model, optimizer, scheduler, step, best, extra=None):
    """ATOMIC save: write to a temp file then os.replace() into place. A Ctrl-C (or crash)
    mid-write can only ever corrupt the throwaway temp file, never the real checkpoint — so a
    resume always finds a complete, valid last.pt/best.pt (the safe-to-interrupt guarantee)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    torch.save({
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler else None,
        "step": step,
        "best": best,
        "extra": extra or {},
    }, str(tmp))
    os.replace(str(tmp), str(path))   # atomic on the same filesystem


def load_checkpoint(path, model, optimizer=None, scheduler=None, map_location="cpu",
                    strict=False, expected_step=None):
    """Restore a checkpoint. With strict=False (default) optimizer/scheduler restore failures fall
    back to a fresh optimizer (fine for casual recovery). With strict=True (EXP-26) any missing or
    unloadable optimizer/scheduler state — or a scheduler step that disagrees with the checkpoint
    step — RAISES, because a fresh optimizer or mis-stepped schedule after a pause would change the
    training trajectory and break the lambda-only comparison."""
    ck = torch.load(str(path), map_location=map_location, weights_only=False)
    model.load_state_dict(ck["model"])
    step = ck.get("step", 0)

    if optimizer is not None:
        osd = ck.get("optimizer")
        if osd:
            try:
                optimizer.load_state_dict(osd)
            except (ValueError, KeyError) as e:
                if strict:
                    raise RuntimeError(f"[resume] strict: optimizer state failed to load ({e})")
                print(f"[resume] optimizer state not loaded ({e}); continuing with a fresh optimizer")
        elif strict:
            raise RuntimeError("[resume] strict: checkpoint has no optimizer state")

    if scheduler is not None:
        ssd = ck.get("scheduler")
        if ssd:
            try:
                scheduler.load_state_dict(ssd)
            except (ValueError, KeyError) as e:
                if strict:
                    raise RuntimeError(f"[resume] strict: scheduler state failed to load ({e})")
                print(f"[resume] scheduler state not loaded ({e}); continuing")
            else:
                sched_step = ssd.get("last_epoch")
                if strict and sched_step is not None and int(sched_step) != int(step):
                    raise RuntimeError(f"[resume] strict: scheduler step {sched_step} != checkpoint step {step}")
        elif strict:
            raise RuntimeError("[resume] strict: checkpoint has no scheduler state")

    if strict and expected_step is not None and int(step) != int(expected_step):
        raise RuntimeError(f"[resume] strict: checkpoint step {step} != expected {expected_step}")
    return step, ck.get("best", None)
