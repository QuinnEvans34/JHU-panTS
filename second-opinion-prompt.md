# Second-Opinion Request — Pretrained Model Choice for a 3D Pancreatic Tumor Segmentation Project

**Instructions for you (the assistant):** Please **search the web** to verify the claims below, then give me a genuine second opinion. I already have a recommendation from another assistant and I want you to either confirm it or argue for a better option. **Do not just agree to be agreeable** — if you'd choose differently, say so and explain why. Focus especially on: (1) the transfer-learning / pretrained-model choice, (2) whether it's the right fit for an Apple-Silicon (MPS) laptop, and (3) anything about the overall approach you'd change. End with a clear verdict: *agree* or *choose something else*.

---

## Project context (the whole project, condensed)

**Goal.** Build a 3D deep-learning segmentation pipeline on the Johns Hopkins **PanTS** dataset (Pancreatic Tumor Segmentation, NeurIPS 2025; arXiv 2507.01291; github.com/MrGiovanni/PanTS). The primary target is **"Level 4.5"**: voxel-wise segmentation of an abdominal CT volume into 3 classes — `0 = background`, `1 = pancreas`, `2 = pancreatic lesion`. The code is config-driven so it can scale down to lesion-only (Level 4) or up to multi-structure (Level 5, ~28 classes) later.

**Scope / framing.** This is a **segmentation tool, not a diagnostic system**. On top of segmentation we add a CADe-style detection wrapper that outputs *"there could be a tumor here"* (lesion present y/n, location, volume, confidence) — never a tumor type or clinical diagnosis. Business framing: an annotation-assist tool for a radiologist / imaging annotator who accepts/edits/rejects the proposed contour. It's a 5-week solo course project, with a 10-week capstone planned to extend the same codebase (ROI cascade, full-scale training).

**Data.** PanTS Mini: PanTS-tr (n=9,000) + PanTS-te (n=901), ~346 GB total, NIfTI CT volumes + voxel masks (pancreatic tumor, pancreas head/body/tail, + 24 surrounding structures), plus `metadata.xlsx` (age, sex, diagnosis, spacing, etc.). License CC-BY-NC-SA-4.0, static (not real-time). These are whole-body/abdominal scans, so the pancreas is a tiny fraction of each volume.

**Hardware (important).** 14" MacBook Pro, **Apple M5 Pro**, 20-core GPU, **64 GB unified memory**, 1 TB SSD; dataset on an external drive. Training runs on **PyTorch MPS** (Apple Silicon), **not CUDA**. So CUDA-only / very heavy pipelines (e.g. nnU-Net's full machinery) are awkward, and lighter models that train fast on MPS are preferred.

**Planned approach.**
- **Model:** SegResNet (MONAI) as the primary architecture; 3D U-Net as fallback.
- **Training strategy (the key decision):** train a **from-scratch SegResNet** as a baseline/control, AND a **transfer-learning** model by fine-tuning a pretrained CT encoder; then compare the two as an ablation.
- **3D handling:** orientation→RAS, resample spacing (~1.5×1.5×2 mm), HU window [-100,300]→[0,1], `CropForegroundd`, patch-based training (~96×128×128) with `RandCropByPosNegLabeld` at ~70% lesion-positive (extreme class imbalance), `DiceCELoss` (or DiceFocal), **AdamW** + cosine/warmup, InstanceNorm (not BatchNorm), deep supervision.
- **Inference:** full-volume sliding-window (Gaussian, ~0.5 overlap), TTA, post-processing (largest-CC for pancreas, small-blob removal for false positives).
- **Metrics:** pancreas Dice and lesion Dice reported **separately**, plus patient-wise sensitivity / specificity / AUC (CADe). SOTA on PanTS is ~0.53 tumor Dice, ~80% patient sensitivity, ~90% specificity — so lesion Dice ~0.35–0.50 is considered a respectable target.
- **Tracking:** MLflow. **UI:** Streamlit (tri-planar slice viewer + a rotatable 3D mesh of the segmentation via marching cubes).

---

## The recommendation I want you to evaluate

For the **transfer-learning model**, the recommendation is to fine-tune **SuPreM's SegResNet** weights — file `supervised_suprem_segresnet_2100.pth` from github.com/MrGiovanni/SuPreM (HF: huggingface.co/MrGiovanni/SuPreM). SuPreM is a suite of supervised-pretrained 3D models from the same JHU lab as PanTS, pretrained on AbdomenAtlas (abdominal CT with 25 organ classes incl. pancreas).

**The reasoning given:**
1. **Same architecture as the from-scratch baseline (SegResNet)**, so the "did pretraining help?" comparison is a clean single-variable ablation (random-init vs SuPreM-init), not confounded by also changing the architecture.
2. **Very small — ~4.7M parameters** (vs ~62M for Swin UNETR), so it trains fast and fits comfortably on an MPS laptop.
3. **Domain-matched**: pretrained on abdominal CT including the pancreas, by the PanTS lab; SuPreM's own benchmark reportedly found *supervised* pretraining transfers better than *self-supervised* (e.g. the Swin UNETR self-supervised weights), and the repo ships a `pancreas_tumor_detection` fine-tuning example that closely matches this task.

**Alternatives that were considered and set aside:**
- **Swin UNETR self-supervised** (MONAI, ~5,050 CT, 62M params) — well-documented, but a transformer (heavier on MPS) and a different architecture from the baseline, which muddies the ablation. Kept as an optional later comparison.
- **PanTS-trained checkpoints** (MedFormer, R-Super on HF) — trained on the exact task, but treated as a **reference oracle only** (not fine-tuned as "ours"), because they're heavy/unusual architectures and using them would undercut the learning goal.
- **MONAI pancreas bundle** (Decathlon Task07) and **Models Genesis** — possible but smaller/older pretraining or non-matching backbone.
- **From scratch only** — fine, but transfer is expected to help with the tiny-lesion problem and converge faster on a laptop.

---

## Questions for you

1. Do you **agree** that fine-tuning **SuPreM's SegResNet** is the best transfer-learning starting point given the constraints (MPS laptop, desire for a clean scratch-vs-transfer ablation, pancreatic-tumor CT segmentation)? If not, what would you pick and why?
2. Is **SegResNet** the right primary architecture here, or would you prefer something else (3D U-Net, Swin UNETR, MedNeXt, nnU-Net) given Apple Silicon / MPS and a 5-week solo timeline?
3. Any concerns with the **SuPreM SegResNet** weights specifically (size only ~4.7M params, pretraining domain, how to load them and re-init the head for 3 classes, license)?
4. Anything in the **overall approach** (patch-based + pos/neg sampling, single-stage now vs ROI cascade later, loss, optimizer, metrics, MPS-specific gotchas) you'd change or warn me about?
5. Please **verify the factual claims** — does SuPreM actually publish SegResNet weights, is the ~4.7M param count right, and is the "supervised > self-supervised transfer" claim supported?

Give me your honest verdict at the end: **proceed with SuPreM SegResNet**, or **go with a specific alternative**.
