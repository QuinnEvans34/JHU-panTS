#!/usr/bin/env python3
"""Export showcase cases for the NiiVue 3D viewer (static-first UI, docs/ui.md §5).

For each case it writes, in the model's whole-box input space so everything aligns:
  <out>/<case_id>/ct.nii.gz     preprocessed CT (what the model saw)
  <out>/<case_id>/gt.nii.gz     ground-truth 3-class mask (0 bg / 1 pancreas / 2 lesion)
  <out>/<case_id>/pred.nii.gz   predicted 3-class mask
  <out>/<case_id>/mesh/*.obj    world-aligned surface meshes (pancreas + lesion, pred + gt)
  <out>/results.json            per-case CADe summary (merged across runs)

The React + NiiVue app renders the CT volume in 3D and overlays the meshes.

Pick the showcase trio first with --list (runs the model over the val set and prints
per-case flags + Dice), then export the three you choose:
  --list                                 -> table to pick healthy / tumor / wrong-prediction
  --case PanTS_XXXX [--case PanTS_YYYY]   -> export those cases

Preprocessing flags MUST match the checkpoint's training recipe (whole-box example):
  PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/export_case.py \
    --ckpt outputs/checkpoints/pants-level45/wholebox_p128_1p5_GOOD.pt \
    --case PanTS_00001234 --crop-native 16 --whole-box --roi 128 --spacing 1.5
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.dataset import get_dataset
from src.models.segresnet import build_model
from src.training import trainer as T
from src.inference.sliding_window import predict_volume

from monai.data import DataLoader


def dice(a, b) -> float:
    a, b = np.asarray(a).astype(bool), np.asarray(b).astype(bool)
    s = int(a.sum() + b.sum())
    return 1.0 if s == 0 else 2.0 * int((a & b).sum()) / s


def get_affine(meta_tensor) -> np.ndarray:
    """Pull the 4x4 world affine out of a (possibly batched) MONAI MetaTensor."""
    aff = getattr(meta_tensor, "affine", None)
    if aff is None:
        return np.eye(4)
    aff = aff.detach().cpu().numpy() if hasattr(aff, "detach") else np.asarray(aff)
    return aff.reshape(-1, 4, 4)[0]


def save_nifti(arr, affine, path):
    import nibabel as nib
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(np.asarray(arr), affine), str(path))


def write_obj(verts, faces, path):
    """Minimal OBJ writer (NiiVue reads .obj). Faces are 1-indexed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"v {v[0]:.3f} {v[1]:.3f} {v[2]:.3f}" for v in verts]
    lines += [f"f {t[0]+1} {t[1]+1} {t[2]+1}" for t in faces]
    path.write_text("\n".join(lines) + "\n")


def _taubin_smooth(verts, faces, iters=12, lam=0.53, mu=-0.53):
    """Taubin (lambda/mu) mesh smoothing: relaxes vertices toward neighbor averages to
    remove marching-cubes facets while (unlike plain Laplacian) preserving volume/shape.
    Vectorized with a sparse adjacency; fast enough for showcase meshes."""
    from scipy import sparse
    n = len(verts)
    f = np.asarray(faces)
    I = np.concatenate([f[:, 0], f[:, 1], f[:, 2], f[:, 1], f[:, 2], f[:, 0]])
    J = np.concatenate([f[:, 1], f[:, 2], f[:, 0], f[:, 0], f[:, 1], f[:, 2]])
    A = (sparse.coo_matrix((np.ones(len(I)), (I, J)), shape=(n, n)) > 0).astype(np.float64).tocsr()
    deg = np.asarray(A.sum(1)).ravel()
    deg[deg == 0] = 1.0
    L = sparse.diags(1.0 / deg) @ A          # row-normalized neighbor average
    V = verts.astype(np.float64)
    for _ in range(iters):
        V = V + lam * (L @ V - V)
        V = V + mu * (L @ V - V)
    return V.astype(np.float32)


def surface(field, affine, iso=0.5, presmooth=0.7, taubin=12):
    """A clean surface from a scalar field (a model probability channel, or a smoothed
    binary mask). Gaussian pre-smoothing turns the hard voxel steps into a smooth
    isosurface; Taubin smoothing polishes the mesh. Verts are mapped index->world (mm)
    via the affine. Returns (verts_world, faces) or None if the field never crosses `iso`.

    This is deliberately faithful, not invented detail: the model outputs a continuous
    probability, and meshing that field is closer to what it computed than a hard 0/1 mask."""
    from skimage import measure
    from scipy import ndimage
    v = np.asarray(field, dtype=np.float32)
    if presmooth and presmooth > 0:
        v = ndimage.gaussian_filter(v, sigma=presmooth)
    if float(v.max()) < iso:
        return None
    verts, faces, _, _ = measure.marching_cubes(v, level=iso)
    if taubin and taubin > 0 and len(verts):
        verts = _taubin_smooth(verts, faces, iters=int(taubin))
    world = (affine @ np.c_[verts, np.ones(len(verts))].T).T[:, :3]
    return world, faces


def load_full_ct(cfg, ct_path, downsample_mm=2.0):
    """Load the ORIGINAL full abdomen CT in RAS world space (optionally downsampled for the
    web), windowed to [0,1]. The affine is RAS-consistent with the whole-box meshes, so the
    organ surfaces land in the right place inside the full scan. Returns (array, affine)."""
    from monai.transforms import (Compose, LoadImaged, EnsureChannelFirstd,
                                   Orientationd, Spacingd, ScaleIntensityRanged)
    pre = cfg["preprocessing"]
    hu_lo, hu_hi = pre["hu_window"]
    tfs = [LoadImaged(keys="image"), EnsureChannelFirstd(keys="image"),
           Orientationd(keys="image", axcodes=pre.get("orientation", "RAS"))]
    if downsample_mm:
        tfs.append(Spacingd(keys="image", pixdim=(downsample_mm,) * 3, mode="bilinear"))
    tfs.append(ScaleIntensityRanged(keys="image", a_min=hu_lo, a_max=hu_hi, b_min=0.0, b_max=1.0, clip=True))
    img = Compose(tfs)({"image": ct_path})["image"]
    return img[0].cpu().numpy().astype(np.float32), get_affine(img)


def infer_case(cfg, model, device, split, case_id):
    ds = get_dataset(cfg, split, train=False, cache=False, ids=[case_id])
    batch = next(iter(DataLoader(ds, batch_size=1, num_workers=0)))
    img = batch["image"].to(device)
    with torch.no_grad():
        logits = predict_volume(model, img, cfg, device)
    probs = torch.softmax(logits, dim=1)[0].cpu().numpy()   # (3,H,W,D)
    pred = probs.argmax(0).astype(np.int16)
    ct = img[0, 0].cpu().numpy().astype(np.float32)
    gt = batch["label"][0, 0].cpu().numpy().astype(np.int16)
    affine = get_affine(batch["image"])
    return ct, gt, pred, probs, affine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--case", action="append", default=[], help="case_id to export (repeatable)")
    ap.add_argument("--split", default="val")
    ap.add_argument("--out", default="outputs/ui_cases")
    ap.add_argument("--list", action="store_true", help="scan the val set and print a per-case table to pick the trio")
    ap.add_argument("--list-n", type=int, default=25, help="how many val cases to scan in --list mode")
    # preprocessing overrides (MUST match the checkpoint's training recipe)
    ap.add_argument("--roi", type=int, default=None)
    ap.add_argument("--spacing", type=float, default=None)
    ap.add_argument("--crop-native", type=int, default=None)
    ap.add_argument("--crop-pancreas", type=float, default=None)
    ap.add_argument("--whole-box", action="store_true")
    ap.add_argument("--smooth-sigma", type=float, default=0.7,
                    help="Gaussian pre-smoothing of the field before marching cubes (0 = off, more = smoother)")
    ap.add_argument("--taubin", type=int, default=12,
                    help="Taubin mesh-smoothing iterations (0 = off; ~12 gives a clean organ surface)")
    ap.add_argument("--full-ct", action="store_true",
                    help="also export the full abdomen CT (fun mode); meshes land on it via world-consistent affines")
    ap.add_argument("--full-ct-mm", type=float, default=2.0,
                    help="downsample spacing for the full CT export, to keep the web volume small")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.roi:
        cfg["sampling"]["patch_size"] = [args.roi] * 3
        cfg["inference"]["sw_roi_size"] = [args.roi] * 3
    if args.spacing:
        cfg["preprocessing"]["target_spacing"] = [args.spacing] * 3
    if args.crop_native is not None:
        cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
    if args.crop_pancreas is not None:
        cfg["preprocessing"]["crop_to_pancreas_margin_mm"] = args.crop_pancreas
    if args.whole_box:
        cfg["preprocessing"]["whole_box"] = True
    set_seed(get(cfg, "seed", 42))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)
    spacing = np.array(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5]), dtype=float)
    vox_mm3 = float(spacing.prod())

    model = build_model(cfg).to(device)
    T.load_checkpoint(args.ckpt, model, map_location=device)
    model.eval()

    import pandas as pd
    man = pd.read_csv(dp["manifest"])
    vset = {x.strip() for x in (dp["splits_dir"] / f"{args.split}.txt").read_text().split() if x.strip()}

    # --- LIST mode: help pick a healthy / tumor / wrong-prediction trio ---
    if args.list:
        vdf = man[man["case_id"].isin(vset)]
        # mix of tumor-positive and healthy so all three archetypes appear
        pos = vdf[vdf["has_lesion"].astype(bool)]["case_id"].tolist()[: args.list_n // 2]
        neg = vdf[~vdf["has_lesion"].astype(bool)]["case_id"].tolist()[: args.list_n // 2]
        print(f"{'case_id':<18} {'gt_tumor':>8} {'pred_tumor':>10} {'lesion_dice':>11} {'panc_dice':>9}")
        print("-" * 60)
        for cid in pos + neg:
            ct, gt, pred, probs, aff = infer_case(cfg, model, device, args.split, cid)
            flag = int((pred == 2).sum()) * vox_mm3 >= get(cfg, "inference.postprocess.lesion_min_volume_mm3", 50)
            print(f"{cid:<18} {str(bool((gt==2).any())):>8} {str(flag):>10} "
                  f"{dice(pred==2, gt==2):>11.3f} {dice(pred==1, gt==1):>9.3f}")
        print("\nPick: a healthy case (gt_tumor False, pred_tumor False), a tumor case (both True, "
              "high lesion_dice), and a wrong case (a False/True mismatch = false alarm or a miss).")
        return

    if not args.case:
        ap.error("give --case CASE_ID (repeatable), or --list to pick the trio first")

    out = Path(args.out)
    results_path = out / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}

    for cid in args.case:
        print(f"\n=== exporting {cid} ===")
        ct, gt, pred, probs, affine = infer_case(cfg, model, device, args.split, cid)
        cdir = out / cid
        save_nifti(ct, affine, cdir / "ct.nii.gz")
        save_nifti(gt.astype(np.int16), affine, cdir / "gt.nii.gz")
        save_nifti(pred.astype(np.int16), affine, cdir / "pred.nii.gz")

        files = {"ct": f"{cid}/ct.nii.gz", "gt": f"{cid}/gt.nii.gz", "pred": f"{cid}/pred.nii.gz", "mesh": {}}

        if args.full_ct:
            ctp = man.loc[man["case_id"] == cid, "ct_path"]
            if len(ctp):
                fct, faff = load_full_ct(cfg, ctp.iloc[0], downsample_mm=args.full_ct_mm)
                save_nifti(fct, faff, cdir / "ct_full.nii.gz")
                files["ct_full"] = f"{cid}/ct_full.nii.gz"
                print(f"  + full CT {tuple(fct.shape)} @ {args.full_ct_mm}mm")
        # Smooth surfaces. Prediction meshes come from the model's PROBABILITY field
        # (smoother and more faithful than the hard argmax); the pancreas shell uses
        # pancreas+lesion probability so the tumor is not carved out of the organ.
        mesh_specs = [
            ("pancreas_pred", probs[1] + probs[2]),
            ("lesion_pred",   probs[2]),
            ("pancreas_gt",   (gt > 0).astype(np.float32)),
            ("lesion_gt",     (gt == 2).astype(np.float32)),
        ]
        for name, fld in mesh_specs:
            m = surface(fld, affine, iso=0.5, presmooth=args.smooth_sigma, taubin=args.taubin)
            if m is not None:
                rel = f"{cid}/mesh/{name}.obj"
                write_obj(m[0], m[1], out / rel)
                files["mesh"][name] = rel

        lesion_vox = int((pred == 2).sum())
        results[cid] = {
            "case_id": cid,
            "gt_has_lesion": bool((gt == 2).any()),
            "pred_has_lesion": lesion_vox > 0,
            "lesion_volume_mm3": round(lesion_vox * vox_mm3, 1),
            "dice_pancreas": round(dice(pred == 1, gt == 1), 3),
            "dice_lesion": round(dice(pred == 2, gt == 2), 3),
            "confidence": round(float(probs[2][pred == 2].mean()) if lesion_vox > 0 else 0.0, 3),
            "spacing_mm": spacing.tolist(),
            "files": files,
        }
        print(f"  saved CT/gt/pred + {len(files['mesh'])} meshes -> {cdir}")
        print(f"  lesion {results[cid]['lesion_volume_mm3']} mm3, "
              f"dice panc {results[cid]['dice_pancreas']} / lesion {results[cid]['dice_lesion']}")

    out.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {results_path} ({len(results)} case(s)). Point the NiiVue app at {out}/.")


if __name__ == "__main__":
    main()
