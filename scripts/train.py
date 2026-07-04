#!/usr/bin/env python3
"""Train Level 4.5 segmentation — SegResNet (scratch or SuPreM-transfer).

Stage 0 (overfit gate) — prove the loop by memorizing 1-2 cases:
  python scripts/train.py --overfit 2 --max-iters 600 --scratch

General training on the dev subset:
  python scripts/train.py --split dev_subset --epochs 60

Logs to MLflow and checkpoints to outputs/checkpoints/. Resumable via --resume.
"""
import argparse
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.dataset import get_dataset
from src.models.segresnet import build_model, load_suprem, set_encoder_requires_grad
from src.training.losses import build_loss
from src.training.metrics import DiceEvaluator
from src.training import trainer as T

from monai.data import DataLoader


def cycle(loader):
    while True:
        for batch in loader:
            yield batch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--split", default="dev_subset")
    ap.add_argument("--overfit", type=int, default=None, help="limit to N cases (Stage 0)")
    ap.add_argument("--max-iters", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--scratch", action="store_true", help="force from-scratch (no SuPreM)")
    ap.add_argument("--transfer", action="store_true", help="force SuPreM transfer")
    ap.add_argument("--log-every", type=int, default=25)
    ap.add_argument("--ckpt-every", type=int, default=200)
    ap.add_argument("--no-mlflow", action="store_true")
    ap.add_argument("--positive", action="store_true", help="draw overfit cases from tumor-positive cases only")
    ap.add_argument("--no-cache", action="store_true", help="disable CacheDataset (slower)")
    ap.add_argument("--val-split", default="val")
    ap.add_argument("--val-limit", type=int, default=0, help=">0 enables validation on N held-out cases")
    ap.add_argument("--val-every", type=int, default=500)
    ap.add_argument("--val-positive", action="store_true",
                    help="validate on tumor-positive cases only (meaningful lesion Dice)")
    ap.add_argument("--resume", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    set_seed(int(get(cfg, "seed", 42)))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)
    epoch_iters = int(get(cfg, "training.epoch_iters", 250))
    total_iters = args.max_iters or (args.epochs or int(get(cfg, "training.max_epochs", 100))) * epoch_iters

    # --- data ---
    override_ids = None
    if args.positive:
        import pandas as pd
        m = pd.read_csv(dp["manifest"])
        override_ids = m[(m["split"] == "train") & (m["has_lesion"].astype(bool))]["case_id"].tolist()
        print(f"[positive] {len(override_ids)} tumor-positive train cases available")
    ds = get_dataset(cfg, args.split, train=True, cache=(not args.no_cache),
                     limit=args.overfit, ids=override_ids)
    loader = DataLoader(ds, batch_size=int(get(cfg, "training.batch_size", 1)),
                        shuffle=True, num_workers=0)
    print(f"device={device}  split={args.split}  cases={len(ds)}  total_iters={total_iters}")

    val_loader = None
    if args.val_limit > 0:
        val_ids = None
        if args.val_positive:
            import pandas as pd
            m = pd.read_csv(dp["manifest"])
            vset = {x.strip() for x in (dp["splits_dir"] / f"{args.val_split}.txt").read_text().split() if x.strip()}
            val_ids = m[(m["case_id"].isin(vset)) & (m["has_lesion"].astype(bool))]["case_id"].tolist()
        val_ds = get_dataset(cfg, args.val_split, train=False, cache=True, limit=args.val_limit, ids=val_ids)
        val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, num_workers=0)
        tag = "tumor-positive " if args.val_positive else ""
        print(f"validation: {len(val_ds)} {tag}cases every {args.val_every} iters (sliding-window)")

    # --- model (scratch vs transfer) ---
    use_pretrained = get(cfg, "transfer.use_pretrained", True)
    if args.scratch:
        use_pretrained = False
    if args.transfer:
        use_pretrained = True
    model = build_model(cfg).to(device)
    if use_pretrained and dp["pretrained_weights"].exists():
        load_suprem(model, dp["pretrained_weights"])
    elif use_pretrained:
        print(f"[warn] pretrained weights missing at {dp['pretrained_weights']} — training from scratch")
        use_pretrained = False

    # optional encoder freeze for transfer warm-up
    freeze_iters = 0
    if use_pretrained and int(get(cfg, "transfer.freeze_encoder_epochs", 0)) > 0:
        freeze_iters = min(int(get(cfg, "transfer.freeze_encoder_epochs")) * epoch_iters, total_iters // 4)
        set_encoder_requires_grad(model, False)
        print(f"[transfer] encoder frozen for first {freeze_iters} iters")

    optimizer, base_lr = T.build_optimizer(cfg, model, transfer=use_pretrained)
    warmup = min(int(get(cfg, "scheduler.warmup_epochs", 2)) * epoch_iters, total_iters // 5)
    min_lr_ratio = float(get(cfg, "scheduler.min_lr", 1e-6)) / base_lr
    if args.overfit:
        min_lr_ratio = 1.0  # flat LR (no decay) so it can fully memorize the overfit set
    scheduler = T.build_scheduler(optimizer, warmup, total_iters, min_lr_ratio)
    loss_fn = build_loss(cfg)
    evaluator = DiceEvaluator(num_classes=int(get(cfg, "model.out_channels", 3)))

    start = 0
    best = -1.0
    best_panc = 0.0
    best_val = -1.0
    if args.resume:
        start, best = T.load_checkpoint(args.resume, model, optimizer, scheduler, map_location=device)
        print(f"resumed from {args.resume} at step {start}")

    # --- MLflow ---
    ml = None
    if not args.no_mlflow:
        try:
            import mlflow
            mlflow.set_tracking_uri(get(cfg, "mlflow.tracking_uri", "sqlite:///outputs/mlflow.db"))
            mlflow.set_experiment(get(cfg, "mlflow.experiment", "pants-level45"))
            mlflow.start_run()
            mlflow.log_params({
                "mode": "transfer" if use_pretrained else "scratch",
                "split": args.split, "overfit": args.overfit, "total_iters": total_iters,
                "lr": base_lr, "patch": get(cfg, "sampling.patch_size"),
                "loss": get(cfg, "loss.name"),
            })
            ml = mlflow
        except Exception as e:
            print(f"[mlflow disabled] {e}")

    ckpt_dir = dp["output_dir"] / "checkpoints" / get(cfg, "mlflow.experiment", "run")
    it = cycle(loader)
    model.train()
    t0 = time.time()
    running = 0.0
    for step in range(start, total_iters):
        if freeze_iters and step == freeze_iters:
            set_encoder_requires_grad(model, True)
            print(f"[transfer] encoder unfrozen at step {step}")

        batch = next(it)
        img = batch["image"].to(device)
        lab = batch["label"].to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(img)
        loss = loss_fn(logits, lab)
        loss.backward()
        optimizer.step()
        scheduler.step()
        running += float(loss.detach())

        if (step + 1) % args.log_every == 0:
            evaluator.reset()
            evaluator.update(logits.detach(), lab)
            d = evaluator.aggregate()
            avg = running / args.log_every
            running = 0.0
            lr = optimizer.param_groups[0]["lr"]
            rate = (step + 1 - start) / (time.time() - t0)
            les = d.get("lesion")
            les_str = f"{les:.3f}" if les is not None else " n/a "  # n/a = no lesion in these patches
            print(f"step {step+1}/{total_iters}  loss {avg:.4f}  "
                  f"dice[panc {d.get('pancreas',0):.3f} | lesion {les_str}]  "
                  f"lr {lr:.2e}  {rate:.2f} it/s")
            if ml:
                metrics = {"train/loss": avg, "train/dice_pancreas": d.get("pancreas", 0), "lr": lr}
                if les is not None:
                    metrics["train/dice_lesion"] = les
                ml.log_metrics(metrics, step=step + 1)
            best_panc = max(best_panc, d.get("pancreas", 0.0))
            if val_loader is None and d["mean"] > best:  # train-dice best only when not validating
                best = d["mean"]
                T.save_checkpoint(ckpt_dir / "best.pt", model, optimizer, scheduler, step + 1, best)

        if val_loader is not None and (step + 1) % args.val_every == 0:
            from src.inference.sliding_window import validate
            vd = validate(model, val_loader, evaluator, cfg, device)
            vp, vl = vd.get("pancreas", 0.0), vd.get("lesion")
            vl_str = f"{vl:.3f}" if vl is not None else " n/a "
            print(f"  [val @ {step+1}] dice  pancreas {vp:.3f} | lesion {vl_str}  (n={args.val_limit})")
            if ml:
                vm = {"val/dice_pancreas": vp}
                if vl is not None:
                    vm["val/dice_lesion"] = vl
                ml.log_metrics(vm, step=step + 1)
            score = vl if vl is not None else vd.get("mean", 0.0)
            if score > best_val:
                best_val = score
                T.save_checkpoint(ckpt_dir / "best.pt", model, optimizer, scheduler, step + 1, best_val)
                print(f"  [val] new best (lesion {score:.3f}) -> saved best.pt")

        if (step + 1) % args.ckpt_every == 0:
            T.save_checkpoint(ckpt_dir / "last.pt", model, optimizer, scheduler, step + 1, best)

    T.save_checkpoint(ckpt_dir / "last.pt", model, optimizer, scheduler, total_iters, best)
    print(f"\nDone. checkpoints in {ckpt_dir}")
    if best_val >= 0:
        print(f"best VAL lesion-Dice {best_val:.3f}")
    if args.overfit:
        print("Stage 0 gate: PASS (pancreas overfit)" if best_panc > 0.90 else
              f"Stage 0 gate: not yet (best pancreas {best_panc:.3f}) — train longer")
    if ml:
        ml.end_run()


if __name__ == "__main__":
    main()
