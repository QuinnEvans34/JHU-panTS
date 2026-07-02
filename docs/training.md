# Training Design

**Living doc.** How the model is trained: architecture details, loss, optimizer, sampling, the whole-body-scan/ROI strategy, training-time expectations, and resumable-run mechanics. Pairs with `architecture.md` (§5–6) and `experiment-tracking.md` (MLflow).

---

## 0. Locked starting recipe (Track A — clean ablation) · 2026-07-01

The disciplined baseline recipe. Plain `SegResNet`, identical on both arms (scratch vs SuPreM-init). Track B may deviate (deep supervision, focal loss, bigger patch) — separately.

| Knob | Value | Note |
|---|---|---|
| Orientation | RAS (canonical) | — |
| Target spacing | **1.5 × 1.5 × 1.5 mm** | isotropic; **match SuPreM's spacing** on transfer arm (confirm) |
| Intensity | clip HU **[-100, 300] → [0,1]** | soft-tissue window; **confirm SuPreM's normalization** on transfer arm |
| Patch / ROI | **96 × 96 × 96** | start here; try 128³ later |
| Model | SegResNet, `init_filters=16`, GroupNorm, `out_channels=3` | **match SuPreM's exact config from checkpoint keys**; re-init 3-class head |
| Sampling | `RandCropByPosNegLabeld`, `num_samples=4`, `pos:neg=2:1` | ~67% foreground patches |
| Batch | 1 volume × 4 samples = **effective 4** | raise if MPS memory allows |
| Loss | `DiceCELoss(softmax=True, to_onehot_y=True, include_background=True)` | try `include_background=False` for lesion emphasis |
| Optimizer | **AdamW**, weight_decay `1e-5` | — |
| LR (scratch) | `2e-4` | baseline arm |
| LR (transfer) | `1e-4`, freeze encoder 2–3 epochs then unfreeze (optionally encoder @ 0.3× LR) | let head settle first |
| Schedule | linear warmup (2 epochs) → cosine to `1e-6` | — |
| Precision | **fp32** (AMP off) initially | MPS autocast is partial — validate first |
| Seed | 42 | reproducibility |
| Augments | flip p=0.2/axis · rot90 p=0.2 · scale-int ±10% p=0.15 · shift-int ±10% p=0.15 | light for the clean ablation |
| Sliding window | ROI 96³ · `overlap=0.5` · `mode="gaussian"` · `sw_batch_size=2` · **stitch on CPU** | full-volume eval |

**Bookkeeping:** 1 epoch = **250 iterations**; validate every **5 epochs**; keep **best checkpoint by lesion Dice**; early-stop patience ~10 validations.

### Stage budgets & gates

| Stage | What | Budget | Target / gate |
|---|---|---|---|
| 0 | Overfit 1–2 cases | ~500 iters (2 ep) | train Dice > 0.95 — *proves the pipeline* |
| 1 | Pancreas-only, dev subset | 20–30 ep (5–7.5k iters) | pancreas Dice ~0.75–0.85 |
| 2 | Pancreas + lesion (L4.5), dev subset | 60–100 ep (15–25k iters) | the main result |
| 3 | Lesion-focused (bias sampling to lesion, tune loss) | continue from Stage 2 | lift lesion Dice |
| 4 | Full-volume sliding-window eval + CADe metrics | eval | honest numbers |

Wall-clock: **measure 50 steps on day one** — that sets all estimates. Expect single-digit minutes/epoch; transfer converges faster. Full-scale (9,000 cases) = capstone, ~50–100k iters, multi-day.

### Confirm against SuPreM at code time
1. Exact SegResNet config (`init_filters`, `blocks_down/up`, norm) — from checkpoint keys, so weights load.
2. Spacing SuPreM pretrained at — match on transfer arm.
3. Intensity normalization SuPreM expects — match, or transfer benefit drops.

### Debug signals
- Stage 0 won't overfit → pipeline bug (labels/sampling/loss), not the model. Stop and fix.
- Lesion Dice stuck at 0 while pancreas trains → sampling/imbalance; raise pos ratio or switch to DiceFocal.
- Val ≫ train → leakage (check patient-level splits) or over-aggressive aug.
- Loss NaN on MPS → lower LR, confirm fp32, guard empty patches.

---

## 1. Training stages (recap)

| Stage | Target | Purpose |
|-------|--------|---------|
| 0 | Overfit 1–2 cases | Prove the pipeline (data, labels, loss) is wired correctly. Gate before anything else. |
| 1 | CT → pancreas only | Validate the 3D pipeline on an easy target. Don't linger. |
| 2 | CT → bg / pancreas / lesion (Level 4.5) | **The main project.** |
| 3 | Lesion-focused | Positive sampling + loss tuning so the model actually finds tumors. |
| 4 | Full-volume sliding-window eval | Honest evaluation + CADe metrics. |

---

## 2. Model & architecture details

- **Primary:** SegResNet (MONAI). 3D U-Net is the interchangeable fallback; Swin UNETR is the transformer comparison.
- **Transfer model:** fine-tune **SuPreM's pretrained SegResNet** (`supervised_suprem_segresnet_2100.pth`, ~4.7M params, AbdomenAtlas pretraining). See §9.
- **Never BatchNorm** — 3D batch size is ~1–2, where BatchNorm statistics are meaningless (the most common 3D-seg footgun). Use whatever norm keeps the transfer checkpoint compatible (see two-track rule below).
- **Residual units** in the encoder/decoder blocks (SegResNet default).
- Output channels set by `label_mode`: Level 4 = 2, **Level 4.5 = 3**, Level 5 ≈ 28.

### Two-track rule (keep the ablation clean)

MONAI's `SegResNet` and `SegResNetDS` are **different classes**, and SuPreM's checkpoint is plain `SegResNet` (GroupNorm). So we run two separate tracks and never mix them:

- **Track A — clean ablation:** plain, checkpoint-compatible `SegResNet`, **scratch vs SuPreM-init**, with *identical* config, preprocessing, sampling, optimizer, and inference. The only variable is the initialization. **No deep supervision, no norm swap here** — that would confound "did pretraining help?" with architecture drift, and can break weight loading.
- **Track B — best practical model:** free to add **deep supervision**, InstanceNorm, larger patches, etc., to chase the best lesion Dice. Reported separately, not as part of the ablation.

Match Track A's `SegResNet` config (norm, channels, `use_conv_final`) to SuPreM's so the weights load.

## 3. Loss

- **Default: `DiceCELoss`** (Dice + cross-entropy) — robust to the extreme background imbalance.
- **Alternative: `DiceFocalLoss`** if the lesion class is still ignored (focal term hammers hard/rare voxels).
- Deep-supervision weighting applies to **Track B only** (see §2).
- Consider class weights up-weighting `lesion` if needed.
- **Many scans are lesion-negative** — use MONAI's `ignore_empty=True` on the Dice *metric* so empty-GT cases don't distort the average, and consider excluding background from the loss when the lesion channel is tiny (MONAI supports this).

## 4. Optimizer & schedule

- **Optimizer: AdamW** (confirmed). Base LR ~`1e-4`, weight decay ~`1e-5`. More forgiving than nnU-Net's SGD+Nesterov, and ideal for fine-tuning.
- **Schedule:** cosine (or polynomial) decay with a short **warmup**.
- **Fine-tuning trick — differential LR:** lower LR on the pretrained encoder, higher on the freshly-initialized head, so the new head catches up without wrecking pretrained weights.
- **Batch size:** 1–2 (memory/MPS). Use **gradient accumulation** to simulate a larger effective batch if updates are noisy.

## 5. Patch sampling & the whole-body-scan problem

PanTS scans are large abdominal (often chest-to-pelvis) volumes; the pancreas is a tiny fraction, the tumor smaller still. Therefore:

- **`CropForegroundd`** — trim air/table around the body so compute isn't wasted on empty space.
- **`RandCropByPosNegLabeld`** — label-aware patch sampling, **~70% lesion-positive / 30% background**. Mandatory: random patches almost always miss the pancreas entirely.
- **Hard negatives:** don't let negatives be too easy. Random whole-abdomen background teaches little; the real confusion is tissue *adjacent* to the pancreas (bowel, vessels, ducts, inflammation). Bias negative crops toward the pancreas neighborhood (e.g. sample within a dilated pancreas ROI) so the model learns the distinctions that actually cause false positives.
- **Augmentations:** `RandFlipd`, `RandRotate90d`, `RandScaleIntensityd`, `RandShiftIntensityd`.
- Patch size: start `96×128×128`, tune to MPS memory headroom.

### ROI cascade (coarse-to-fine) — capstone upgrade

The SOTA answer to the tiny-pancreas problem is a **two-stage cascade**:

1. **Stage A — localize:** fast low-res pass over the whole volume to find a pancreas bounding box.
2. **Stage B — segment:** crop to that ROI and segment at full resolution, spending all compute on relevant anatomy.

**Decision:** the 5-week course uses **single-stage** (foreground crop + pos/neg sampling); Level 4.5 segmenting the pancreas alongside the lesion is itself a soft form of anatomical context. The explicit **localize→segment cascade is the capstone headline upgrade**. The pipeline is built to accept it later — the manifest already carries the pancreas mask, so generating ROI crops is straightforward.

## 6. Inference & post-processing

- **Sliding-window inference** over full volumes, Gaussian weighting, ~0.5 overlap, for seam-free stitching. Eval is **always full-volume, never patch-only**.
- **MPS memory tip:** run the patch predictor on `mps` but set the sliding-window inferer's output `device="cpu"` so the stitched full-volume tensor lives in system RAM — MONAI supports this and it relieves GPU-memory pressure on long volumes.
- **Test-time augmentation (TTA):** average predictions over flips for a free Dice bump.
- **Post-processing (specificity levers):** keep the largest connected component for the pancreas (there's only one); delete lesion blobs below a small volume threshold to kill spurious false positives.

## 7. Training-time expectations (Apple Silicon / MPS)

- **Reframe:** patch training never passes over 346 GB. An epoch = N iterations (e.g. 250), so wall-clock scales with *iterations*, not dataset size.
- **Measure first:** time 50 steps on day one and extrapolate. Rough anchor: **single-digit minutes/epoch** on the dev subset → Stage 1 in **hours**, Stage 2 (with transfer) a **respectable model in ~1–2 days cumulative**, full 9,000-case training in **multiple days** (capstone territory).
- **Validate sparingly:** sliding-window val is expensive; run it every N epochs on a fixed small val subset.
- **Thermal:** sustained MPS load throttles a laptop — keep plugged in, on a hard cool surface; run long jobs overnight. Transfer learning = fewer epochs = less heat/time.
- **Mixed precision:** `autocast` on MPS is partial — validate before relying on it; may stay fp32.

## 8. Resumable training (required for laptop runs)

- **Checkpoint every epoch:** model + optimizer + scheduler + epoch + RNG state, so runs stop/resume across sessions instead of one uninterrupted multi-day run.
- **Best-checkpoint selection by lesion Dice**, not average Dice.
- Resume continues the same MLflow run (see `experiment-tracking.md`).
- **Reproducibility:** seed everything (`src/utils/seed.py`); log the git commit + resolved config as MLflow artifacts.

## 9. Transfer learning — SuPreM SegResNet (locked)

**Decision:** from-scratch `SegResNet` = baseline/control; **`SegResNet` initialized from SuPreM** (`supervised_suprem_segresnet_2100.pth`) = the transfer model. Chosen because it's the same architecture as the baseline (clean ablation), tiny (~4.7M params, MPS-friendly), and pretrained on abdominal CT incl. pancreas by the PanTS lab. Full rationale in `architecture.md` §6.

**Loading recipe (network surgery):**
1. Instantiate the **checkpoint-compatible plain `SegResNet`** (match SuPreM's config — norm, channels, `use_conv_final`).
2. Recreate the **final conv block to emit 3 channels** (`out_channels=3`).
3. Load the pretrained `state_dict` **non-strictly** (`strict=False`), excluding the mismatched output layer.
4. Fine-tune: low LR (~1e-4) + warmup, optional encoder freeze for a few warmup epochs, differential LR (encoder < head).
5. **Match SuPreM's expected input normalization** (spacing + intensity) or transfer benefit evaporates.

**Treat the SuPreM repo as a checkpoint source only** — its example code pins old deps (PyTorch 1.11, MONAI 0.9, CUDA 11.3) and a CUDA/JHH ROI pipeline. We load the weights into our modern MONAI/MPS code; we don't reproduce their scripts.

**Fallback if SuPreM integration becomes a time sink:** SuPreM **U-Net** (19M, also published) or a plain MONAI 3D U-Net — *not* Swin UNETR (heavier, breaks the same-architecture ablation) and *not* nnU-Net (CUDA-oriented, 3D-conv issues on MPS).

Scratch-vs-transfer is logged as an MLflow comparison (= a stretch goal for free).

> **Label-space caveat:** SuPreM's docs are ambiguous about the exact released checkpoint's classes (25-class AbdomenAtlas vs 32-class / pseudo-tumor references). It doesn't change our plan (we re-init the head anyway), but don't over-claim what the pretraining contained without inspecting the checkpoint keys.

## 10. Open questions

- Patch-size ceiling on MPS (empirical).
- **HU window:** test soft-tissue `[-100,300]` vs a **wider clip** (PanTS preprocessing uses `[-1000,1000]`); also confirm/match SuPreM's expected normalization for the transfer arm.
- `DiceCELoss` vs `DiceFocalLoss` for lesion; background-excluded loss?
- Effective batch via gradient accumulation — needed?
- TTA flip set; exact warmup length + cosine vs poly decay.
- **Anatomy-context ablation:** add a small set of neighboring structures (Track B / intermediate level) — evidence suggests a large tumor-Dice gain (see architecture.md §5).
