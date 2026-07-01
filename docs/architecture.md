# Architecture & Design

**Project:** 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS)
**Status:** Living design doc — Week 1 planning. Expect revision as experiments run.
**Owner:** Quinn (solo). Compute: MacBook Pro M5 Pro, 64 GB unified memory, PyTorch **MPS**.

> This document is the technical contract the code scaffold follows. It records *what* we're building and *why*, the decisions made, and the open questions still to resolve.

**Companion design docs:** [`data-pipeline.md`](data-pipeline.md) *(planned — finalize after first download)* · [`training.md`](training.md) · [`experiment-tracking.md`](experiment-tracking.md) (MLflow) · [`ui.md`](ui.md).

---

## 1. Scope: the four-task ladder

"Find pancreatic tumors" is really a ladder of four increasingly hard ML tasks. We are deliberate about which rungs are in scope.

| # | Task | In scope? | Notes |
|---|------|-----------|-------|
| 1 | **Segmentation** — label every voxel: background / pancreas / lesion | ✅ **Core** | The project. Level 4.5. |
| 2 | **Detection** — per scan: is a lesion present, where, how big? | ✅ **Core (derived)** | A CADe wrapper on the segmentation output. This is the "could there be a tumor?" deliverable. |
| 3 | **Classification** — benign vs malignant / tumor subtype | ⚠️ **Research stretch only** | PanTS ships diagnosis metadata, so it's data-feasible as an experiment. Not deployable. |
| 4 | **Diagnosis** — a clinical determination a doctor acts on | ❌ **Out of scope** | Documented as a roadmap (Section 11). Requires pathology ground truth, external validation, FDA pathway. |

**The key insight:** segmentation gives detection essentially for free — connected-component analysis on the lesion mask yields "lesion present / location / volume / confidence." We build task 1 and *report* task 2.

**Decision (locked):** Output is "**there could be a tumor here**," never a tumor *type* or a diagnosis. Tumor-type classification (rung 3) is attempted only if the core finishes early.

---

## 2. Business framing (recap)

**User:** a medical-imaging annotator / radiologist who must outline the pancreas and any lesion on CT. **Action supported:** accept / edit / reject the model's proposed contour and "possible tumor" flag, instead of drawing from scratch. **Not** a diagnostic device — a human makes every clinical call. License is CC-BY-NC-SA-4.0 (non-commercial), consistent with this academic, workflow-tool framing.

---

## 3. Data

- **Dataset:** PanTS (JHU, NeurIPS 2025). 36,390 CT volumes; voxel-wise masks for pancreatic tumor, pancreas head/body/tail, + 24 surrounding structures; per-scan metadata (age, sex, diagnosis, contrast phase, spacing, slice thickness).
- **Splits we use:** PanTS-tr (n=9,000) for train/val, PanTS-te (n=901) as held-out test. Full Mini release ≈ 346 GB.
- **Format:** 3D CT volumes + masks as NIfTI. Each volume carries an **affine** (orientation + voxel spacing in mm). Intensities are **Hounsfield Units** (calibrated radiodensity).
- **Access:** `git clone` the PanTS repo → `download_PanTS_data.sh` / `download_PanTS_label.sh`.
- **Storage:** lives on an **external drive** (~340 GB). Never on the laptop SSD, never committed to the repo. Path supplied via config, never hardcoded.
- **Dev subset:** download ~50–150 cases locally first (with a healthy lesion-positive fraction) for fast iteration before any larger run.

---

## 4. Handling the 3D images (preprocessing pipeline)

A CT scan is a 3D volume, not an image. Two scans differ in orientation, spacing, and intensity range, so we canonicalize before training. Implemented with MONAI transforms.

1. **Load** NIfTI (image + label), ensure **channel-first**.
2. **Orientation** → canonical **RAS** (`Orientationd`).
3. **Resample spacing** to a common target, e.g. ~`1.5 × 1.5 × 2.0 mm` (`Spacingd`). **Critical:** images use trilinear interpolation, **masks use nearest-neighbor** — otherwise labels get corrupted.
4. **Intensity windowing** — clip HU to an abdominal soft-tissue window (`[-100, 300]`, tune vs `[-150, 250]`), then normalize to `[0, 1]` (`ScaleIntensityRanged`). Bone/air are discarded as noise.
5. **Patch-based training** — random 3D crops (start `96 × 128 × 128`, tune to MPS memory). Whole volumes don't fit in memory with a deep 3D net.
6. **Sliding-window inference** at eval time — slide the patch window across the full volume and stitch predictions. **Eval is always full-volume, never patch-only.**

**Training augmentations:** `RandCropByPosNegLabeld` (the imbalance fix, Section 6), `RandFlipd`, `RandRotate90d`, `RandScaleIntensityd`, `RandShiftIntensityd`.

---

## 5. Model architecture

**Primary:** **SegResNet** (MONAI) — a residual 3D encoder–decoder U-Net variant. Chosen for reliability, MPS-friendliness, and strong medical-segmentation track record. 3D U-Net is the interchangeable fallback. The U-Net shape (encoder compresses → decoder reconstructs → skip connections carry fine spatial detail) is what lets it trace small, soft-edged structures.

**Config-driven levels (one codebase):**

| Level | Output classes | Status |
|-------|----------------|--------|
| 4 | 2 (background, lesion) | Built, not primary |
| **4.5** | **3 (background, pancreas, lesion)** | **Primary target** |
| 5 | ~28 (subregions + surrounding structures) | Stretch, swap YAML only |

**Comparison model (stretch):** **Swin UNETR** (transformer) — doubles as both the "model comparison" stretch goal and the transfer-learning vehicle (Section 6). Heavier on MPS; only after the U-Net works.

**Architecture details that matter more than the model choice** (full detail in [`training.md`](training.md)): **InstanceNorm/GroupNorm, never BatchNorm** (batch size ~1–2 in 3D); **deep supervision** (auxiliary decoder-level losses); **AdamW** + cosine/warmup, with **differential LR** for fine-tuning.

### Anatomy context helps the tumor (evidence-backed)

The PanTS paper reports tumor Dice jumping **57.4% → 67.7%** just by training with **richer surrounding-anatomy labels** instead of a bare pancreas/tumor setup — a larger gain than any backbone swap would give. This is the same "pancreas-aware" logic behind choosing Level 4.5 over Level 4, extended further. **Planned ablation (high priority if the core works):** an intermediate level between 4.5 and 5 that adds a *handful* of neighboring structures (e.g. duodenum, key vessels) rather than jumping to ~28 classes. This is more likely to move lesion performance than a bigger encoder. Runs as a Track-B experiment (see [`training.md`](training.md) §2).

### Whole-body scans → ROI strategy

PanTS volumes are large abdominal (often chest-to-pelvis) scans; the pancreas is a tiny fraction, the tumor smaller still. This is why label-aware sampling (`RandCropByPosNegLabeld`) + `CropForegroundd` are mandatory, not optional. The SOTA answer is a **coarse-to-fine cascade** (localize the pancreas → segment at full res in that ROI). **Decision:** the course uses **single-stage** (foreground crop + pos/neg sampling); the **localize→segment cascade is the capstone upgrade**, and the pipeline is built to accept it (the manifest carries the pancreas mask). See [`training.md`](training.md) §5.

---

## 6. Training strategy — transfer learning (the core decision)

**Decision: fine-tune a pretrained CT encoder as the real model, with a from-scratch SegResNet as the baseline we compare against.** Not training blindly from scratch; not just running someone else's checkpoint.

### Pretrained options, by closeness to our task

| Tier | Source | Closeness | Use for us |
|------|--------|-----------|-----------|
| 1 | Self-supervised CT encoders: **Swin UNETR** (MONAI, ~5,050 CT), **SuPreM**, **Models Genesis** (both JHU, built for abdominal-CT transfer) | Generic CT | **Best for our own fine-tuning** — inherit encoder, train fresh head |
| 2 | **PanTS-trained checkpoints**: `MedFormer`, `R-Super` (Hugging Face) | Exact dataset/task | **Reference oracle only** — see "what SOTA looks like"; wrong architecture/hardware fit to submit as ours |
| 3 | From scratch (random init) | None | **Baseline / control** |

### The layered plan — locked on SuPreM SegResNet

1. **From-scratch SegResNet baseline.** Stages 0–2 (overfit one case → pancreas-only → pancreas+lesion). Proves the pipeline, gives a clean control, MPS-cheap.
2. **Fine-tune SuPreM's SegResNet** (`supervised_suprem_segresnet_2100.pth`, ~4.7M params) → the transfer model. Same architecture as the baseline, tiny (MPS-friendly), pretrained on abdominal CT incl. pancreas by the PanTS lab. *Verified by an independent deep-research second opinion (2026-06-30), which agreed this is the right choice over Swin UNETR / nnU-Net.*
3. **Compare scratch vs transfer** → the ablation answering "did pretraining help?" — a stretch goal for free.
4. Run a Tier-2 PanTS checkpoint on a few test cases as a **measuring stick**, not a submission.

**Two-track rule (clean ablation):** the scratch-vs-transfer study uses **plain, checkpoint-compatible `SegResNet` with identical config** on both arms — *no deep supervision or norm swap*, since SuPreM's checkpoint is plain `SegResNet` (≠ `SegResNetDS`) and mixing them confounds the comparison. A separate **Track B** "best practical model" is free to add deep supervision etc. Details + loading recipe in [`training.md`](training.md) §2, §9.

**Fallback** if SuPreM integration stalls: SuPreM **U-Net** or plain MONAI 3D U-Net — *not* Swin UNETR, *not* nnU-Net on MPS.

### Fine-tuning mechanics ("fitting it to our scenario")

- Pretrained model outputs a different class count → **load all shape-matching layers** (encoder, most of decoder), **re-initialize the final segmentation head** to `out_channels=3`.
- **Match the pretrained model's preprocessing** (voxel spacing, intensity normalization) or transfer benefit evaporates.
- **Low learning rate** (~`1e-4`); optionally **freeze encoder for a few warm-up epochs**, then unfreeze.
- With self-supervised encoders you inherit only the encoder; the decoder trains fresh (normal).

---

## 7. Class imbalance (non-negotiable)

Lesion voxels can be ~0.01% of a volume; a model that predicts "all background" scores ~99.99% accuracy and is useless. Mitigations, both required:

- **Dice-based loss:** `DiceCELoss` (Dice + cross-entropy) or `DiceFocalLoss` — insensitive to background size.
- **Positive-biased patch sampling:** `RandCropByPosNegLabeld` with ~**70% lesion-positive** / 30% background crops, so the network actually sees tumor voxels.

---

## 8. Evaluation & metrics

**Report pancreas and lesion SEPARATELY** — a high average hides tumor failure.

**Segmentation metrics:** per-class **Dice** (pancreas, lesion), lesion **IoU**, and lesion **NSD / surface distance** (PanTS reports NSD). Use `ignore_empty=True` on the Dice metric since many scans are lesion-negative.

**Detection / CADe metrics (the business story):**

- **Patient-wise sensitivity** — of patients with a tumor, the fraction we flag (any detection counts).
- **Tumor-wise sensitivity** — of tumors, the fraction correctly localized.
- **Per-case connected-component lesion sensitivity** — matches the CADe "did we find the blob?" story.
- **Specificity** — of healthy patients, the fraction we correctly leave unflagged.
- **AUC**, false-positives per scan, false-negative case list.

**SOTA reference (PanTS benchmark table on the repo — verified, sets realistic targets):** best listed models reach **tumor Dice ≈ 0.53** (MedFormer 52.9%, R-Super 53.4%), **patient-wise sensitivity ≈ 80%** (80.8% / 80.1%), **specificity ≈ 90%** (90.0% / 93.2%), **AUC ≈ 0.90–0.92**. So **lesion Dice ~0.35–0.50 is a respectable student result** and should be framed against these numbers, not against an unrealistic 0.9. The headline business sentence: *"Of patients who had a tumor, we flagged X%; of healthy patients, we correctly stayed quiet Y%."*

---

## 9. Inference & the CADe wrapper

Full-volume **sliding-window inference** → lesion probability map → threshold → **connected-component analysis** → per-lesion report: present (y/n), location (pancreas region), volume (mm³), confidence. This wrapper is what turns segmentation into the "could there be a tumor?" output and is only a few days on top of segmentation.

---

## 10. Front-end (business layer)

**Streamlit viewer** (full design in [`ui.md`](ui.md)). One-page story: **CADe summary** (possible lesion · location · volume · confidence) → **rotatable 3D mesh** of pancreas (translucent) + lesion (red), built by marching-cubes on the *masks* → **tri-planar slice viewer** with green/red overlays, scroll, toggle. Plus **mask export (NIfTI)** so the user accepts/edits/rejects in a real tool (e.g. 3D Slicer). Demo uses **pre-computed predictions** for showcase cases (MPS inference is slow), with optional live upload. Stretch: NiiVue/stpyvista volumetric render, confidence heatmap.

---

## Experiment tracking (MLflow — required)

MLflow is the primary experiment tracker and a hard project requirement. Local SQLite/file backend, artifact store on the external drive, viewed with `mlflow ui`. Logs params (resolved config), per-epoch metrics (losses, pancreas/lesion Dice separately, sensitivity/specificity/AUC), and artifacts (best checkpoint, config + git hash, overlay PNGs). Runs tagged `model=scratch|transfer` so the comparison is a side-by-side in the UI. Full plan in [`experiment-tracking.md`](experiment-tracking.md).

---

## 11. Roadmap to a real diagnostic tool (out of scope — documented)

What stands between this and something a clinician relies on, rung by rung: **pathology ground truth** (biopsy-confirmed, not just radiologist contours) · **external validation** on independent cohorts/scanners (PanTS itself tests on UCSF, Polish, Peking, RSNA out-of-distribution sets) · ideally **prospective** validation · rigorous **specificity / normal-case** handling · and **regulatory clearance** as Software as a Medical Device (FDA 510(k)/De Novo — years, clinical evidence, significant cost). Documenting this gap is itself a deliverable; it shows we understand the distance between a good model and a trustworthy device.

---

## 12. Hardware / MPS notes

- Apple Silicon → **PyTorch MPS**, not CUDA. `device = "mps"`; set `PYTORCH_ENABLE_MPS_FALLBACK=1` (some MONAI ops fall back to CPU).
- 64 GB **unified** memory (shared CPU/GPU) → no fixed VRAM ceiling; patch size bounded by total memory + MPS stability. Start `96×128×128`, tune.
- Mixed precision (`autocast`) on MPS is partial — validate before relying on it; may keep fp32.
- Avoid **nnU-Net** as primary (CUDA-oriented). Stick to MONAI SegResNet / Swin UNETR.
- Transfer learning reduces epochs needed → a real advantage on a laptop.

---

## 13. Hard constraints (guardrails)

Never commit raw data · split by **patient**, never slice · full-volume sliding-window eval, never patch-only · report pancreas & lesion Dice separately · tumor-positive sampling required · no clinical/diagnostic claims · don't start Level 5 before 4.5 works · keep pipeline config-driven · data path via config, never hardcoded.

---

## 14. Course vs capstone scope

This project is built once and harvested twice. The **5-week course** delivers: Level 4.5 single-stage segmentation + CADe wrapper, transfer-vs-scratch comparison, MLflow tracking, Streamlit UI (slices + 3D mesh). The **10-week capstone** extends the *same* codebase: the **localize→segment ROI cascade**, scaling to the full 9,000 cases, Level 5 multi-structure, and possibly the tumor-type classification research experiment. Every design decision here is made so the capstone is a config/module addition, not a rewrite.

## 15. Open questions / next planning topics

Detailed per-area open questions now live in the companion docs ([`training.md`](training.md) §10, [`experiment-tracking.md`](experiment-tracking.md) §7, [`ui.md`](ui.md) §8). Cross-cutting items still open:

- Exact target **voxel spacing** and **HU window** (validate `[-100,300]` vs `[-150,250]` on real cases).
- Which Tier-1 pretrained backbone to commit to (Swin UNETR vs SuPreM) and confirm its expected preprocessing.
- Dev **subset selection** strategy (how many cases, lesion-positive fraction, how chosen) — settle after the first download.
- Whether to attempt the tumor-type **classification** stretch, and which metadata field labels it.
- Confirm on download: exact label filenames (one tumor mask vs subtypes) and whether **case == patient** in `metadata.xlsx`.

---

## Pretrained model & resource links

- PanTS (data, benchmark, checkpoints): <https://github.com/MrGiovanni/PanTS>
- PanTS paper: <https://arxiv.org/abs/2507.01291>
- MedFormer (PanTS checkpoint): <https://huggingface.co/AbdomenAtlas/MedFormerPanTS>
- R-Super (PanTS checkpoint): <https://huggingface.co/AbdomenAtlas/R-SuperPanTSMerlin>
- SuPreM (JHU pretrained abdominal-CT models): <https://github.com/MrGiovanni/SuPreM>
- Models Genesis: <https://github.com/MrGiovanni/ModelsGenesis>
- MONAI Swin UNETR tutorial: <https://github.com/Project-MONAI/tutorials/blob/main/3d_segmentation/swin_unetr_btcv_segmentation_3d.ipynb>
