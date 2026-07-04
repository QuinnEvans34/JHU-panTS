"""Training helpers: device, optimizer, warmup+cosine schedule, checkpoints."""
from __future__ import annotations

import math
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
    return torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()),
                             lr=lr, weight_decay=wd), lr


def build_scheduler(optimizer, warmup_iters: int, total_iters: int, min_lr_ratio: float):
    def fn(step):
        if step < warmup_iters:
            return (step + 1) / max(1, warmup_iters)
        p = (step - warmup_iters) / max(1, total_iters - warmup_iters)
        return min_lr_ratio + (1 - min_lr_ratio) * 0.5 * (1 + math.cos(math.pi * min(1.0, p)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, fn)


def save_checkpoint(path, model, optimizer, scheduler, step, best, extra=None):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler else None,
        "step": step,
        "best": best,
        "extra": extra or {},
    }, str(path))


def load_checkpoint(path, model, optimizer=None, scheduler=None, map_location="cpu"):
    ck = torch.load(str(path), map_location=map_location, weights_only=False)
    model.load_state_dict(ck["model"])
    if optimizer and ck.get("optimizer"):
        optimizer.load_state_dict(ck["optimizer"])
    if scheduler and ck.get("scheduler"):
        scheduler.load_state_dict(ck["scheduler"])
    return ck.get("step", 0), ck.get("best", None)
