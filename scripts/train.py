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
    ap.add_argument("--run-name", default=None, help="MLflow run name (auto-built from the config if omitted)")
    ap.add_argument("--positive", action="store_true", help="draw overfit cases from tumor-positive cases only")
    ap.add_argument("--no-cache", action="store_true", help="disable caching (plain Dataset, slowest)")
    ap.add_argument("--cache", choices=["ram", "disk", "none"], default=None,
                    help="dataset cache mode (overrides config training.cache): "
                         "ram=RAM CacheDataset, disk=persistent SSD cache (scales past RAM, survives resume), none")
    ap.add_argument("--val-split", default="val")
    ap.add_argument("--val-limit", type=int, default=0, help=">0 enables validation on N held-out cases")
    ap.add_argument("--val-every", type=int, default=500)
    ap.add_argument("--val-positive", action="store_true",
                    help="validate on tumor-positive cases only (meaningful lesion Dice)")
    ap.add_argument("--resume", default=None)
    ap.add_argument("--patch", type=int, default=None,
                    help="override cube patch size for training AND sliding-window eval (e.g. 128)")
    ap.add_argument("--num-samples", type=int, default=None,
                    help="override crops per volume per step (lower this if a bigger --patch runs out of memory)")
    ap.add_argument("--spacing", type=float, default=None,
                    help="override isotropic target spacing in mm (e.g. 1.0 for finer resolution)")
    ap.add_argument("--crop-pancreas", type=float, default=None,
                    help="oracle ROI: crop to the ground-truth pancreas + this many mm of margin (e.g. 20)")
    ap.add_argument("--crop-native", type=int, default=None,
                    help="CLARITY: crop to pancreas in NATIVE space (before resample) + this many native-voxel margin (e.g. 24)")
    ap.add_argument("--whole-box", action="store_true",
                    help="EXP-12: feed the WHOLE pancreas box (padded/cropped to one --patch cube) instead of random sub-patches; use with --crop-native/--crop-pancreas")
    ap.add_argument("--roi-source", choices=["union", "pancreas"], default=None,
                    help="what the ROI crop is built from: union (pancreas+lesion, legacy) or pancreas (organ only, no lesion leak)")
    ap.add_argument("--loss", choices=["dice_focal", "dice_ce", "tversky", "tversky_focal"], default=None,
                    help="EXP-18: override the loss. tversky/tversky_focal penalize false positives to fight over-segmentation")
    ap.add_argument("--tversky-alpha", type=float, default=None, help="Tversky FALSE-POSITIVE weight (raise to fight over-segmentation, e.g. 0.7)")
    ap.add_argument("--tversky-beta", type=float, default=None, help="Tversky false-negative weight (e.g. 0.3)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    # experiment overrides: change field of view without editing the config file.
    # patch drives both the training crop and the inference window so they always match.
    if args.patch:
        cfg["sampling"]["patch_size"] = [args.patch, args.patch, args.patch]
        cfg["inference"]["sw_roi_size"] = [args.patch, args.patch, args.patch]
        print(f"[override] patch/roi -> {args.patch}^3")
    if args.num_samples:
        cfg["sampling"]["num_samples"] = args.num_samples
        print(f"[override] num_samples -> {args.num_samples}")
    if args.spacing:
        cfg["preprocessing"]["target_spacing"] = [args.spacing, args.spacing, args.spacing]
        print(f"[override] target_spacing -> {args.spacing}mm")
    if args.crop_pancreas is not None:
        cfg["preprocessing"]["crop_to_pancreas_margin_mm"] = args.crop_pancreas
        print(f"[override] crop to pancreas ROI + {args.crop_pancreas}mm margin (oracle ROI)")
    if args.crop_native is not None:
        cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
        print(f"[override] CLARITY crop-native: pancreas ROI in native space + {args.crop_native}-voxel margin, then resample")
    if args.whole_box:
        cfg["preprocessing"]["whole_box"] = True
        print(f"[override] WHOLE-BOX: feeding the entire pancreas box as one {get(cfg, 'sampling.patch_size')} cube (no random sub-patch)")
    if args.roi_source:
        cfg["preprocessing"]["roi_source"] = args.roi_source
        print(f"[override] ROI source = {args.roi_source} ({'pancreas organ only, no lesion leak' if args.roi_source=='pancreas' else 'pancreas+lesion, legacy'})")
    if args.loss:
        cfg.setdefault("loss", {})["name"] = args.loss
        print(f"[override] loss -> {args.loss}")
    if args.tversky_alpha is not None:
        cfg.setdefault("loss", {})["tversky_alpha"] = args.tversky_alpha
        print(f"[override] tversky alpha (false-positive weight) -> {args.tversky_alpha}")
    if args.tversky_beta is not None:
        cfg.setdefault("loss", {})["tversky_beta"] = args.tversky_beta
        print(f"[override] tversky beta (false-negative weight) -> {args.tversky_beta}")
    set_seed(int(get(cfg, "seed", 42)))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)

    # SAFETY GUARD (Codex audit 2026-07-19): a TRAINING split must never intersect val/test.
    # This is the assertion that would have caught the make_scaled_split leakage before it ever trained.
    def _read_ids(name):
        f = Path(dp["splits_dir"]) / f"{name}.txt"
        return {x.strip() for x in f.read_text().split() if x.strip()} if f.exists() else set()
    if args.split not in ("val", "test"):
        _train_ids = _read_ids(args.split)
        _leak = _train_ids & (_read_ids("val") | _read_ids("test"))
        assert not _leak, (f"LEAKAGE ABORT: training split '{args.split}' shares {len(_leak)} case(s) with "
                           f"val/test (e.g. {sorted(_leak)[:5]}). Rebuild it from train.txt (make_scaled_split.py).")
        print(f"[split-check] '{args.split}' is disjoint from val+test ({len(_train_ids)} train cases)  OK")

    epoch_iters = int(get(cfg, "training.epoch_iters", 250))
    total_iters = args.max_iters or (args.epochs or int(get(cfg, "training.max_epochs", 100))) * epoch_iters

    # --- cache mode: --no-cache > --cache > config training.cache (default ram) ---
    if args.no_cache:
        cache_mode = "none"
    elif args.cache:
        cache_mode = args.cache
    else:
        cache_mode = str(get(cfg, "training.cache", "ram"))
        if cache_mode not in ("ram", "disk", "none"):
            cache_mode = "ram"
    if cache_mode == "disk":
        cdir = get(cfg, "training.cache_dir", None) or str(dp["output_dir"] / "cache")
        print(f"[cache] mode=disk -> {cdir} (first epoch fills it, then fast + resume-safe)")
    else:
        print(f"[cache] mode={cache_mode}")

    # --- data ---
    override_ids = None
    if args.positive:
        import pandas as pd
        m = pd.read_csv(dp["manifest"])
        override_ids = m[(m["split"] == "train") & (m["has_lesion"].astype(bool))]["case_id"].tolist()
        print(f"[positive] {len(override_ids)} tumor-positive train cases available")
    ds = get_dataset(cfg, args.split, train=True, cache=cache_mode,
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
        val_ds = get_dataset(cfg, args.val_split, train=False, cache=cache_mode, limit=args.val_limit, ids=val_ids)
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
        if freeze_iters and start >= freeze_iters:
            set_encoder_requires_grad(model, True)
        print(f"resumed from {args.resume} at step {start}")

    # --- run identity (computed ONCE, used for BOTH MLflow and the on-disk archive) ---
    # This is deliberately independent of MLflow: EXP-12 was lost because it ran without
    # MLflow AND its best.pt was overwritten by later runs. The per-run archive below now
    # preserves every keeper checkpoint even when MLflow is unavailable.
    import datetime
    loss_cfg = cfg.get("loss", {})
    samp_cfg = cfg.get("sampling", {})
    patch_sz = (samp_cfg.get("patch_size") or [96])[0]
    box_tag = "_wholebox" if get(cfg, "preprocessing.whole_box", False) else ""
    run_name = args.run_name or (
        f"{'transfer' if use_pretrained else 'scratch'}_{loss_cfg.get('name', 'dice_ce')}"
        f"_bg{int(bool(loss_cfg.get('include_background', False)))}"
        f"_p{patch_sz}{box_tag}_{samp_cfg.get('strategy', 'posneg')}_{total_iters}i"
    )
    run_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- MLflow ---
    ml = None
    if not args.no_mlflow:
        try:
            import mlflow
            mlflow.set_tracking_uri(get(cfg, "mlflow.tracking_uri", "sqlite:///outputs/mlflow.db"))
            mlflow.set_experiment(get(cfg, "mlflow.experiment", "pants-level45"))
            mlflow.start_run(run_name=run_name)
            mlflow.log_params({
                "mode": "transfer" if use_pretrained else "scratch",
                "split": args.split, "overfit": args.overfit, "total_iters": total_iters,
                "lr": base_lr, "patch": get(cfg, "sampling.patch_size"),
                "loss": loss_cfg.get("name"),
                "loss.include_background": loss_cfg.get("include_background", True),
                "loss.focal_gamma": loss_cfg.get("focal_gamma", 2.0),
                "loss.lambda_dice": loss_cfg.get("lambda_dice", 1.0),
                "loss.lambda_focal": loss_cfg.get("lambda_focal", 1.0),
                "loss.class_weights": loss_cfg.get("class_weights"),
                "sampling.strategy": samp_cfg.get("strategy", "posneg"),
                "sampling.pos": samp_cfg.get("pos"), "sampling.neg": samp_cfg.get("neg"),
            })
            print(f"[mlflow] run '{run_name}' -> {get(cfg, 'mlflow.tracking_uri')}")
            ml = mlflow
        except Exception as e:
            # EXP-12 ran in a venv without mlflow and its metrics were lost. Make that
            # impossible to miss now: a loud banner instead of a quiet one-liner. The
            # on-disk archive + run_ledger.csv below still capture the run regardless.
            print("\n" + "!" * 70)
            print(f"[MLflow NOT logging]  {e}")
            print("  This run will NOT appear in the MLflow UI. If you want live tracking,")
            print("  stop now and launch from .venv312 (which has mlflow installed).")
            print("  The per-run checkpoint archive + run_ledger.csv WILL still record it.")
            print("!" * 70 + "\n")
    else:
        print("[MLflow] skipped (--no-mlflow). Run still recorded in the on-disk archive + run_ledger.csv.")

    ckpt_dir = dp["output_dir"] / "checkpoints" / get(cfg, "mlflow.experiment", "run")

    # --- per-run checkpoint archive (the fix for the EXP-12 loss) ---
    # Every run still writes the shared best.pt/last.pt (so existing eval/resume runbooks
    # keep working), but it ALSO writes immutable copies into a unique, timestamped folder
    # that no later run can touch. run_info.txt makes each archived checkpoint self-documenting,
    # so a checkpoint can never again become an orphan whose provenance is unknown.
    run_dir = ckpt_dir / "runs" / f"{run_name}__{run_stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_info.txt").write_text(
        f"run_name: {run_name}\n"
        f"timestamp: {run_stamp}\n"
        f"split: {args.split}\n"
        f"mode: {'transfer' if use_pretrained else 'scratch'}\n"
        f"total_iters: {total_iters}\n"
        f"config: {args.config}\n"
        f"patch: {get(cfg, 'sampling.patch_size')}\n"
        f"spacing: {get(cfg, 'preprocessing.target_spacing')}\n"
        f"whole_box: {get(cfg, 'preprocessing.whole_box', False)}\n"
        f"crop_native_margin_vox: {get(cfg, 'preprocessing.crop_native_margin_vox')}\n"
        f"crop_to_pancreas_margin_mm: {get(cfg, 'preprocessing.crop_to_pancreas_margin_mm')}\n"
        f"loss: {loss_cfg.get('name')} include_background={loss_cfg.get('include_background')}\n"
        f"seed: {get(cfg, 'seed', 42)}\n"
    )
    print(f"[archive] keeper checkpoints for this run -> {run_dir}")

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
                T.save_checkpoint(run_dir / "best.pt", model, optimizer, scheduler, step + 1, best)  # immutable archive copy

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
                T.save_checkpoint(run_dir / "best.pt", model, optimizer, scheduler, step + 1, best_val)  # immutable archive copy
                print(f"  [val] new best (lesion {score:.3f}) -> saved best.pt (+ archive)")

        if (step + 1) % args.ckpt_every == 0:
            T.save_checkpoint(ckpt_dir / "last.pt", model, optimizer, scheduler, step + 1, best)

    T.save_checkpoint(ckpt_dir / "last.pt", model, optimizer, scheduler, total_iters, best)
    T.save_checkpoint(run_dir / "last.pt", model, optimizer, scheduler, total_iters, best)  # immutable archive copy

    # persistent, MLflow-independent record of every run (one row per run, never overwritten)
    ledger = ckpt_dir / "run_ledger.csv"
    new_ledger = not ledger.exists()
    with open(ledger, "a") as f:
        if new_ledger:
            f.write("timestamp,run_name,split,mode,total_iters,best_val_lesion,archive_dir\n")
        bv = f"{best_val:.4f}" if best_val >= 0 else ""
        f.write(f"{run_stamp},{run_name},{args.split},"
                f"{'transfer' if use_pretrained else 'scratch'},{total_iters},{bv},{run_dir.name}\n")

    print(f"\nDone. shared checkpoints in {ckpt_dir}")
    print(f"[archive] keeper copies safe in {run_dir}  (best.pt + last.pt + run_info.txt)")
    print(f"[ledger]  run appended to {ledger}")
    if best_val >= 0:
        print(f"best VAL lesion-Dice {best_val:.3f}")
    if args.overfit:
        print("Stage 0 gate: PASS (pancreas overfit)" if best_panc > 0.90 else
              f"Stage 0 gate: not yet (best pancreas {best_panc:.3f}) — train longer")
    if ml:
        ml.end_run()


if __name__ == "__main__":
    main()
