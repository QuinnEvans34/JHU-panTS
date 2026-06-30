# Project Proposal

**Project:** 3D Pancreas-Aware Pancreatic Lesion Segmentation in Abdominal CT
**Dataset:** PanTS — The Pancreatic Tumor Segmentation Dataset (Johns Hopkins University)
**Author:** Quinn · Solo project
**Date:** June 2026

> _Personalization note: Sections 2 (Why) and 3 (Your Takeaway) are written in first person as strong starting drafts. Replace the bracketed prompts with your own voice before submitting — these two sections are explicitly meant to sound like you._

---

## 1. What?

Radiologists and medical-imaging annotators routinely need to outline the pancreas and any pancreatic lesion on 3D CT scans — tracing the organ and tumor slice by slice through a volume that can be hundreds of images thick. Done by hand, delineating the pancreas alone takes a trained reader tens of minutes per case because the pancreas is small, soft-edged, and easy to confuse with neighboring organs; the lesion is smaller still. This project builds a tool that does the first pass automatically: it takes an abdominal CT volume and produces a 3D outline (a "segmentation mask") of the pancreas and any pancreatic lesion, which the annotator then reviews, accepts, or corrects rather than drawing from a blank screen. **In machine-learning terms, this is a supervised 3D semantic-segmentation problem solved with a patch-based 3D U-Net (MONAI/PyTorch); the business-facing output is an editable, color-coded 3D overlay of the predicted pancreas and lesion, plus a measured lesion volume, delivered through a simple slice-by-slice viewer.**

This is explicitly **not** a diagnostic system. It does not decide whether a tumor is cancerous, stage disease, or make any clinical determination. A human reader remains fully in the loop and makes every clinical call; the model only accelerates the manual contouring step that precedes that work.

**Business user.** The named user is a **medical-imaging annotator / radiologist working in a research or clinical-imaging pipeline** who must produce pancreas and lesion contours — for research dataset curation, tumor-volume measurement, or pre-review preparation. **The decision the system supports:** for each case, the user accepts, edits, or rejects the model's proposed contour. The value is reduced manual contouring time and more consistent outlines, while a qualified human retains final judgment.

---

## 2. Why?

[Write 3–5 sentences in your own voice. A strong draft to adapt:]

I chose this project because it sits exactly where I want to grow — at the intersection of deep learning and real, messy, three-dimensional data instead of clean toy datasets. Medical imaging is intimidating in a way I find motivating: the data is large, the labels are hard-won, and getting it wrong is obvious, so it forces a level of rigor I want to build into my own habits. Pancreatic cancer is also one of the deadliest and hardest cancers to catch early, and while this project is a segmentation tool and not a diagnostic one, working with data aimed at that problem makes the technical work feel like it matters. [Add your personal hook — what specifically pulled you toward this dataset or 3D imaging.]

---

## 3. Your Takeaway

[Write 3–5 sentences in your own voice. A strong draft to adapt:]

What I most want to prove to myself is that I can stand up a **complete 3D deep-learning pipeline end to end** — not just call `model.fit()` on a tutorial dataset, but handle real volumetric medical data: loading NIfTI volumes, fixing orientation and voxel spacing, windowing CT intensities, sampling 3D patches, training a memory-constrained 3D U-Net, and running sliding-window inference over full scans. The specific gap I want to close is **3D medical imaging and the MONAI framework**, which I have not used before. I also want to get genuinely comfortable with **class-imbalanced segmentation** — learning how to make a model find a tiny lesion instead of trivially predicting "all background." [Add the one capability you'd be proudest to walk away with.]

---

## 4. Tech Stack

Annotated below — each item marked **[Familiar]** or **[New]**, with a get-up-to-speed plan for new items.

| Layer | Technology | Status | Notes / ramp-up plan |
|-------|-----------|--------|----------------------|
| **Data source** | PanTS dataset (NIfTI CT volumes + masks) | **[New]** | Read the PanTS paper (arXiv 2507.01291) and GitHub README; download a small subset first via the provided scripts. |
| **Language** | Python 3.10+ | **[Familiar]** | — |
| **Medical-image I/O** | NiBabel, SimpleITK | **[New]** | Use for loading NIfTI, reading affine/spacing. Learn via MONAI tutorials + library quickstarts. |
| **3D DL framework** | MONAI | **[New]** | Core ramp-up: MONAI's official 3D segmentation tutorials and transform docs. This is my main learning target. |
| **DL backend** | PyTorch (torch, torchvision) | **[Familiar / partly New]** | Comfortable with 2D PyTorch; 3D volumes + mixed precision are new. |
| **Model** | 3D U-Net / SegResNet (via MONAI) | **[New]** | Standard volumetric architectures; instantiate from MONAI, study the reference implementations. |
| **Numerics / data** | NumPy, pandas | **[Familiar]** | Manifest building, metrics tables. |
| **Metrics / splits** | scikit-learn, MONAI metrics | **[Familiar / New]** | Dice/IoU come from MONAI; splitting logic from sklearn. |
| **Visualization** | Matplotlib | **[Familiar]** | Axial/coronal/sagittal overlays, failure cases. |
| **Experiment tracking** | TensorBoard | **[Familiar]** | Loss/Dice curves. (Optional: Weights & Biases.) |
| **Config** | PyYAML | **[Familiar]** | Config-driven Level 4 / 4.5 / 5 switching. |
| **Front-end (demo)** | Streamlit | **[New]** | Simple viewer for overlays + lesion volume. Learn via Streamlit docs; scope kept minimal. |
| **Compute** | 14" MacBook Pro, Apple **M5 Pro** (20-core GPU, 64 GB unified memory) | **[Familiar / New]** | Training runs on PyTorch's **MPS** backend (Apple Silicon, not CUDA). 64 GB unified memory is shared CPU/GPU, so patch size is bounded by total memory + MPS stability rather than a fixed VRAM number. New: MPS quirks (some ops fall back to CPU; partial mixed-precision). |
| **Storage** | External drive (~340 GB) | **[Familiar]** | Full PanTS Mini lives on an external drive — kept off the laptop SSD and out of the repo. Data path set via config, never hardcoded. |
| **Version control** | Git / GitHub | **[Familiar]** | Branch → PR → merge to main, per course workflow. |

---

## 5. Dataset Validity

- **Name:** PanTS — The Pancreatic Tumor Segmentation Dataset (Johns Hopkins University; NeurIPS 2025).
- **Open source:** Yes. License **CC-BY-NC-SA-4.0** (non-commercial, share-alike). This project is academic and non-commercial, which is compatible; no commercial product claims are made.
- **Source URLs:** GitHub `https://github.com/MrGiovanni/PanTS` · Hugging Face `https://huggingface.co/datasets/BodyMaps/PanTSMini` · Paper `https://arxiv.org/abs/2507.01291`.
- **Real-time?** **No — and confirmed as such.** PanTS is a static, versioned research benchmark, not a daily/weekly live feed. There is no real-time ingestion requirement; the dataset is downloaded once and used as a fixed corpus.
- **Scale:** Full dataset is 36,390 CT volumes from 145 centers with voxel-wise masks for pancreatic tumors, pancreas head/body/tail, and 24 surrounding structures. The public Mini release provides PanTS-tr (n=9,000) and PanTS-te (n=901), totaling ~346 GB.
- **Access method:** `git clone` the PanTS repo, then run the provided `download_PanTS_data.sh` / `download_PanTS_label.sh` scripts. Because the full Mini set is ~346 GB, this project uses **partial download + a local subset** for development, with patch-based training. Raw data is **never committed** to the repo (enforced via `.gitignore`).
- **Labels used:** CT volume → multi-class mask. Level 4.5 target uses 3 classes: `0=background`, `1=pancreas`, `2=pancreatic lesion`.

---

## 6. ML Approach & Pipeline Plan

**ML problem type.** Supervised **3D semantic segmentation** — voxel-wise multi-class classification of an abdominal CT volume into background / pancreas / lesion. (Not detection, not whole-image classification.)

**Why this approach / model family.** The 3D U-Net (and the residual SegResNet variant) is the established standard for volumetric medical segmentation: the encoder–decoder with skip connections preserves fine spatial detail needed to outline small structures, and MONAI provides battle-tested implementations, transforms, and sliding-window inference. The central difficulty is **extreme class imbalance** — lesion voxels are a tiny fraction of the volume — which is addressed with (a) a **Dice + Cross-Entropy (or Dice-Focal) loss** that is robust to imbalance, and (b) **positive/negative patch sampling** (≈70% lesion-positive patches) so the model actually sees tumor voxels during training. Training the pancreas *and* lesion jointly (Level 4.5) rather than the lesion alone gives the model anatomical context, which is why pancreas-aware segmentation is the primary target rather than tumor-only.

**End-to-end data flow:**

```
PanTS NIfTI (CT + masks)
  → build_manifest.py  (scan folders → manifest.csv: case_id, ct_path, mask paths, has_lesion)
  → MONAI preprocessing (load, channel-first, RAS orientation, spacing resample,
                          HU window [-100, 300] → normalize to [0, 1])
  → patient-level train/val/test split (never split by slice)
  → patch-based training (RandCropByPosNegLabel 70/30, flips/rotations/intensity jitter)
  → 3D U-Net / SegResNet (MONAI), mixed precision
  → DiceCE / DiceFocal loss, AdamW
  → validation via SLIDING-WINDOW inference over full volumes
  → metrics: per-class Dice + IoU, lesion sensitivity/precision (report pancreas & lesion SEPARATELY)
  → Streamlit viewer: 3-view overlays, toggle masks, predicted lesion volume, export mask
```

**Validation discipline (built into the plan):** patient-level splits, full-volume sliding-window evaluation (never patch-only scoring), pancreas and lesion Dice reported separately (a high average hides poor tumor performance), and a Stage-0 "overfit one case" check to prove the pipeline is wired correctly before real training.

**Project levels (config-driven, same codebase):**

- **Level 4** — lesion-only mask (2 classes). Higher-risk baseline; built but not the main target.
- **Level 4.5 — pancreas + lesion (3 classes). ← primary target.**
- **Level 5** — full multi-structure (pancreas subregions + 24 surrounding structures, ~28 classes). Stretch goal, enabled by swapping a YAML config — not started until 4.5 works.

---

## 7. Business-Facing Layer

The deliverable a user touches is a lightweight **Streamlit viewer** (no clinical-device claims). For a given CT case the user can:

- **See** the CT with predicted **pancreas (e.g. green)** and **lesion (e.g. red)** overlays in **axial, coronal, and sagittal** views.
- **Scroll** through slices and **toggle** each mask on/off to inspect the model's outline against the scan.
- **Read** a summary panel: predicted **lesion volume (mm³)**, whether a lesion was detected, and a confidence/uncertainty flag for low-confidence cases.
- **Export** the predicted mask (NIfTI) so it can be loaded into a real annotation tool (e.g. 3D Slicer) and **edited** — the actual "accept / correct / reject" action the user performs.

In one sentence: **the user loads a scan, sees the model's proposed pancreas-and-lesion outline from three angles with a measured lesion volume, and accepts or corrects it instead of drawing it from scratch.**

---

## Open items to confirm

- **Patch size on MPS:** start moderate (≈96×128×128) and tune against unified-memory headroom and MPS stability — no fixed VRAM ceiling on Apple Silicon, but MPS behavior is validated empirically before scaling up.
- **Subset size** to download to the external drive for development (proposed: ~50–150 cases with a healthy lesion-positive fraction).
