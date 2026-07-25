"""Register the final pancreas-lesion model in the MLflow Model Registry (M4A1 §1/§4).

Per Codex review: a bare checkpoint artifact is NOT a proper MLflow Model, so we (1) log the raw
checkpoint for reproducibility, (2) log the reconstructed network as a real `mlflow.pytorch` model
(with an MLmodel flavor, so it is conventionally loadable), and (3) register THAT as
`pancreas-lesion-segmenter`. We record full provenance (config, checkpoint SHA-256 + step, recipe,
metrics, git commit, cohort hashes) and an explicit version identity.

The registered PyTorch model is the NEURAL NETWORK component only; scripts/serve.py supplies the
preprocessing (whole-box provided-ROI) and the CADe summarization around it.

Usage:
  python scripts/register_model.py --ckpt outputs/checkpoints/pants-level45/<...>/best.pt \
    --label-mode pancreas_lesion --roi 128 --spacing 1.5 --crop-native 16 --whole-box \
    --lesion-dice 0.415 --note "whole-box SuPreM, leakage-free"
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch

from src.utils.config import load_config, get
from src.models.segresnet import build_model, sha256_file
from src.training import trainer as T
from src.inference.predict import verify_checkpoint_recipe

MODEL_NAME = "pancreas-lesion-segmenter"


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--label-mode", choices=["pancreas_lesion", "anatomy5"], default="pancreas_lesion")
    ap.add_argument("--roi", type=int, default=128)
    ap.add_argument("--spacing", type=float, default=1.5)
    ap.add_argument("--crop-native", type=int, default=16)
    ap.add_argument("--whole-box", action="store_true")
    ap.add_argument("--roi-source", default="pancreas")
    ap.add_argument("--lesion-dice", type=float, default=None, help="reported test/val lesion Dice")
    ap.add_argument("--pancreas-dice", type=float, default=None)
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    if not Path(args.ckpt).exists():
        raise SystemExit(f"checkpoint not found: {args.ckpt}")

    cfg = load_config(args.config)
    cfg["label_mode"] = args.label_mode
    cfg["model"]["out_channels"] = 5 if args.label_mode == "anatomy5" else 3
    cfg["preprocessing"]["target_spacing"] = [args.spacing] * 3
    cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
    cfg["preprocessing"]["whole_box"] = bool(args.whole_box)
    cfg["preprocessing"]["roi_source"] = args.roi_source
    cfg["sampling"]["patch_size"] = [args.roi] * 3
    cfg["inference"]["sw_roi_size"] = [args.roi] * 3

    # reconstruct the network on CPU (registry model should be device-agnostic)
    model = build_model(cfg)
    step, _ = T.load_checkpoint(args.ckpt, model, map_location="cpu")
    model.eval()

    ckpt_sha = sha256_file(args.ckpt)
    blob = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    meta = blob.get("extra", {}) if isinstance(blob, dict) else {}
    # if the checkpoint carries recipe metadata, refuse to register under a mismatched recipe
    verify_checkpoint_recipe(meta, cfg, require_meta=False)

    version, run_id = register_to_mlflow(
        model, cfg, args.ckpt, ckpt_sha, step, meta,
        params={"label_mode": args.label_mode, "out_channels": cfg["model"]["out_channels"],
                "roi": args.roi, "spacing": args.spacing, "crop_native_margin_vox": args.crop_native,
                "whole_box": bool(args.whole_box), "roi_source": args.roi_source},
        lesion_dice=args.lesion_dice, pancreas_dice=args.pancreas_dice, note=args.note)

    print(f"[register] run {run_id}")
    print(f"[register] model '{MODEL_NAME}' registered as version {version}")
    print(f"[register] IDENTITY: registry_name={MODEL_NAME} | version={version} | step={step} | sha256={ckpt_sha[:16]}")
    print("[register] check the MLflow UI (Models tab) for the version + screenshot.")


def register_to_mlflow(model, cfg, ckpt_path, ckpt_sha, step, meta, params,
                       lesion_dice=None, pancreas_dice=None, note=""):
    """Log the raw checkpoint + a proper mlflow.pytorch model and register it. Separated from CLI/model
    building so it is unit-testable with a mocked mlflow. Returns (registered_version, run_id)."""
    try:
        import mlflow
        import mlflow.pytorch
    except ImportError:
        raise SystemExit("mlflow required: pip install mlflow --break-system-packages (use .venv312)")

    mlflow.set_tracking_uri(get(cfg, "mlflow.tracking_uri", "sqlite:///outputs/mlflow.db"))
    mlflow.set_experiment(get(cfg, "mlflow.experiment", "pants-level45"))
    with mlflow.start_run(run_name=f"register_{MODEL_NAME}") as run:
        mlflow.log_params({**params, "checkpoint_step": step, "checkpoint_sha256": ckpt_sha,
                           "git_commit": git_commit()})
        if meta.get("cohort_sha256"):
            mlflow.log_dict(meta["cohort_sha256"], "cohort_sha256.json")
        if lesion_dice is not None:
            mlflow.log_metric("test_lesion_dice", lesion_dice)
        if pancreas_dice is not None:
            mlflow.log_metric("test_pancreas_dice", pancreas_dice)
        if note:
            mlflow.set_tag("note", note)
        mlflow.set_tag("component", "neural-network-only; serve.py adds preprocessing + CADe summary")

        # log the FULLY-RESOLVED config + the checkpoint recipe metadata
        mlflow.log_dict(cfg, "resolved_config.json")
        if meta:
            mlflow.log_dict(meta, "checkpoint_recipe.json")

        mlflow.log_artifact(ckpt_path, artifact_path="raw_checkpoint")
        # serialization_format="pickle": MLflow 3.x's default (PT2) requires an input_example; pickle
        # serializes the state_dict directly, so we can register without a synthetic 3D input tensor.
        info = mlflow.pytorch.log_model(model, name="model", registered_model_name=MODEL_NAME,
                                        serialization_format="pickle")
        version = getattr(info, "registered_model_version", None)
        if version is not None:
            mlflow.set_tag("registered_version", str(version))
        return version, run.info.run_id


if __name__ == "__main__":
    main()
