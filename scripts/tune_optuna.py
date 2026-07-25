#!/usr/bin/env python3
"""Bayesian hyperparameter search (Optuna) for the whole-box SegResNet+SuPreM segmenter.

This is the M4A1 "hyperparameter tuning" deliverable's formal search. It complements the
single-variable ablations in docs/experiments.md by searching the CONTINUOUS training
hyperparameters (LR, focal gamma, loss weights, weight decay) with a TPE (Bayesian) sampler.

Design for feasibility on Apple MPS (each full run is ~7 h, so we cannot search full runs):
  * SHORT PROXY TRIALS — each trial trains a fixed, small step budget (--iters, default 1500) on
    the cached whole-box data, so many configurations evaluate overnight. The winner then informs
    the final full-length run; the search itself is about the METHODOLOGY + the ranking, not about
    producing the final model.
  * The DISK CACHE is filled by the first trial and reused by all the rest (the data doesn't depend
    on the hyperparameters), so trials 2..N are much faster than trial 1.
  * COMPARABILITY — every trial uses the same seed, same data order, and same recipe; the ONLY thing
    that varies is the sampled hyperparameters. So a difference in val Dice is attributable to them.
  * PRUNING — a median pruner stops clearly-bad trials at the mid-point to save compute.
  * RESUMABLE — the study lives in a SQLite file, so an interrupted search resumes where it stopped.
  * Every trial logs its params + final val lesion Dice to MLflow (experiment `pants-level45-optuna`),
    which is the screenshot artifact the rubric asks for.

Requires: pip install optuna --break-system-packages   (in .venv312)

Recipe searched = the FINAL-MODEL recipe: whole-box, crop-native 16, 128^3 @ 1.5mm, pancreas ROI
source (no lesion leak), DiceFocal (include_background=False), 3-class (bg/pancreas/lesion).
Objective = validation LESION Dice on a frozen tumor-positive val cohort (higher is better).

Usage (launch tonight, e.g. ~15 trials overnight):
  python scripts/tune_optuna.py --n-trials 15 --iters 1500 \
    --train-split scaledmax_clean --val-ids configs/cohorts/exp26/val20.txt --cache disk
"""
import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.dataset import get_dataset
from src.models.segresnet import build_model, load_suprem
from src.training.losses import build_loss
from src.training.metrics import DiceEvaluator
from src.training import trainer as T
from src.inference.sliding_window import validate

from monai.data import DataLoader

try:
    import optuna
except ImportError:
    print("optuna required: pip install optuna --break-system-packages")
    sys.exit(1)


def cycle(loader):
    while True:
        for b in loader:
            yield b


def apply_final_recipe(cfg, args):
    """Set the whole-box final-model recipe on the config (the same recipe as the registered model),
    so the search tunes the hyperparameters of the model we actually ship — not some other setup."""
    cfg["sampling"]["patch_size"] = [args.patch, args.patch, args.patch]
    cfg["inference"]["sw_roi_size"] = [args.patch, args.patch, args.patch]
    cfg["preprocessing"]["target_spacing"] = [args.spacing, args.spacing, args.spacing]
    cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
    cfg["preprocessing"]["whole_box"] = True
    cfg["preprocessing"]["roi_source"] = "pancreas"      # organ-only crop, no lesion-extent leak
    cfg.setdefault("loss", {})["name"] = "dice_focal"
    cfg["loss"]["include_background"] = False
    cfg["model"]["out_channels"] = 3
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--n-trials", type=int, default=15)
    ap.add_argument("--iters", type=int, default=1500, help="training steps per proxy trial")
    ap.add_argument("--prune-at", type=int, default=None, help="mid-trial step to report for pruning (default iters//2)")
    ap.add_argument("--train-split", default="scaledmax_clean")
    ap.add_argument("--val-ids", default="configs/cohorts/exp26/val20.txt", help="frozen tumor-positive val cohort")
    ap.add_argument("--val-split", default="val")
    ap.add_argument("--patch", type=int, default=128)
    ap.add_argument("--spacing", type=float, default=1.5)
    ap.add_argument("--crop-native", type=int, default=16)
    ap.add_argument("--cache", choices=["disk", "ram", "none"], default="disk")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--study-name", default="wholebox_hp_search")
    ap.add_argument("--timeout", type=int, default=None, help="optional wall-clock seconds cap")
    ap.add_argument("--no-mlflow", action="store_true")
    args = ap.parse_args()

    prune_at = args.prune_at or max(1, args.iters // 2)

    cfg = load_config(args.config)
    cfg = apply_final_recipe(cfg, args)
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)

    # leakage guard: the training cohort must not touch the val cohort we score on
    train_ids = {x.strip() for x in (dp["splits_dir"] / f"{args.train_split}.txt").read_text().split() if x.strip()}
    val_ids = [x.strip() for x in Path(args.val_ids).read_text().split() if x.strip()]
    leak = train_ids & set(val_ids)
    assert not leak, f"LEAKAGE: train split shares {len(leak)} cases with the val cohort (e.g. {sorted(leak)[:5]})"
    print(f"[optuna] train '{args.train_split}' ({len(train_ids)}) disjoint from val cohort ({len(val_ids)})  OK")

    # Build datasets ONCE and reuse across trials (data is HP-independent; the disk cache is shared).
    train_ds = get_dataset(cfg, args.train_split, train=True, cache=args.cache)
    val_ds = get_dataset(cfg, args.val_split, train=False, cache=args.cache, ids=val_ids)
    val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, num_workers=0)
    print(f"[optuna] {len(train_ds)} train cases, {len(val_ds)} val cases; "
          f"{args.iters} steps/trial, prune-check @ {prune_at}, device={device}")

    epoch_iters = int(get(cfg, "training.epoch_iters", 250))
    warmup = min(2 * epoch_iters, args.iters // 5)

    evaluator = DiceEvaluator(num_classes=3)   # include_background=False -> [pancreas, lesion]

    ml = None
    if not args.no_mlflow:
        try:
            import mlflow
            mlflow.set_tracking_uri(get(cfg, "mlflow.tracking_uri", "sqlite:///outputs/mlflow.db"))
            mlflow.set_experiment("pants-level45-optuna")
            ml = mlflow
        except Exception as e:
            print(f"[optuna] MLflow unavailable ({e}); trials still recorded in the Optuna study DB.")

    def objective(trial):
        # --- sample the hyperparameters (the search space) ---
        lr = trial.suggest_float("lr", 5e-5, 5e-4, log=True)
        gamma = trial.suggest_float("focal_gamma", 1.0, 4.0)
        lam_dice = trial.suggest_float("lambda_dice", 0.5, 2.0)
        lam_focal = trial.suggest_float("lambda_focal", 0.5, 2.0)
        wd = trial.suggest_float("weight_decay", 1e-6, 1e-4, log=True)

        # every trial starts from the SAME seed + SAME recipe; only the HPs above differ
        set_seed(args.seed)
        cfg["optimizer"]["lr_transfer"] = lr
        cfg["optimizer"]["weight_decay"] = wd
        cfg["loss"].update({"focal_gamma": gamma, "lambda_dice": lam_dice, "lambda_focal": lam_focal})

        # fresh model from the SuPreM init each trial
        model = build_model(cfg).to(device)
        if dp["pretrained_weights"].exists():
            load_suprem(model, dp["pretrained_weights"], verbose=False)
        optimizer, base_lr = T.build_optimizer(cfg, model, transfer=True)
        min_lr_ratio = float(get(cfg, "scheduler.min_lr", 1e-6)) / base_lr
        scheduler = T.build_scheduler(optimizer, warmup, args.iters, min_lr_ratio)
        loss_fn = build_loss(cfg)

        gen = torch.Generator().manual_seed(args.seed)
        loader = DataLoader(train_ds, batch_size=1, shuffle=True, num_workers=0, generator=gen)
        try:
            train_ds.transform.set_random_state(seed=args.seed)
        except Exception:
            pass
        it = cycle(loader)

        run_ctx = ml.start_run(run_name=f"optuna_trial_{trial.number}") if ml else None
        if ml:
            ml.log_params({"lr": lr, "focal_gamma": gamma, "lambda_dice": lam_dice,
                           "lambda_focal": lam_focal, "weight_decay": wd, "iters": args.iters,
                           "trial": trial.number})
        try:
            model.train()
            for step in range(args.iters):
                batch = next(it)
                img, lab = batch["image"].to(device), batch["label"].to(device)
                optimizer.zero_grad(set_to_none=True)
                loss = loss_fn(model(img), lab)
                loss.backward()
                optimizer.step()
                scheduler.step()

                if (step + 1) == prune_at:      # mid-trial pruning check
                    vd = validate(model, val_loader, evaluator, cfg, device)
                    mid = vd.get("lesion") or 0.0
                    trial.report(mid, step + 1)
                    if ml:
                        ml.log_metric("val_lesion_dice_mid", mid, step=step + 1)
                    if trial.should_prune():
                        if ml:
                            ml.set_tag("pruned", "true"); ml.end_run()
                        raise optuna.TrialPruned()

            vd = validate(model, val_loader, evaluator, cfg, device)
            final = vd.get("lesion") or 0.0
            if ml:
                ml.log_metric("val_lesion_dice", final)
                ml.log_metric("val_pancreas_dice", vd.get("pancreas", 0.0))
                ml.end_run()
            print(f"  trial {trial.number}: lesion Dice {final:.4f}  "
                  f"(lr {lr:.2e}, gamma {gamma:.2f}, ld {lam_dice:.2f}, lf {lam_focal:.2f}, wd {wd:.1e})")
            return final
        except optuna.TrialPruned:
            raise
        except Exception as e:
            if ml and run_ctx:
                ml.set_tag("error", str(e)[:200]); ml.end_run()
            raise

    Path("outputs/optuna").mkdir(parents=True, exist_ok=True)
    storage = f"sqlite:///outputs/optuna/{args.study_name}.db"
    study = optuna.create_study(
        study_name=args.study_name, storage=storage, load_if_exists=True,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=args.seed),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=3),
    )
    print(f"[optuna] study '{args.study_name}' -> {storage} (resumable)")
    study.optimize(objective, n_trials=args.n_trials, timeout=args.timeout)

    print("\n" + "=" * 60)
    print(f"BEST lesion Dice: {study.best_value:.4f}")
    print(f"BEST params: {study.best_params}")
    df = study.trials_dataframe()
    out_csv = f"outputs/optuna/{args.study_name}_trials.csv"
    df.to_csv(out_csv, index=False)
    print(f"[optuna] {len(study.trials)} trials -> {out_csv}")
    print("Use the best params for the final full-length run + register that model in MLflow.")


if __name__ == "__main__":
    main()
