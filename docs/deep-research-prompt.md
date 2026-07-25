# Deep-research prompt — improving our 3D pancreatic-tumor segmentation model

Paste the block below into ChatGPT (deep-research mode). It has the full project context, every experiment we've run, our real held-out metrics, our constraints, and our three named weaknesses, so the recommendations are specific to this model.

---

I'm building a 3D deep-learning model to segment **pancreatic tumors (lesions)** on CT and I want a rigorous, cited, prioritized set of techniques to improve it. Please be concrete and specific to my setup below — not a generic segmentation survey. Ground your answer in the pancreatic-tumor and abdominal-CT literature (PanTS, SuPreM / AbdomenAtlas, the PANORAMA pancreatic-cancer challenge, nnU-Net pancreas results, and small-lesion / class-imbalance segmentation work).

## The project
- **Task:** 3D semantic segmentation of background / pancreas / pancreatic-lesion on the Johns Hopkins **PanTS** dataset. Framed as a non-diagnostic **CADe assist** — flag and outline possible tumors for a radiologist to accept/edit/reject. Detection (do we flag the tumor at all) matters as much as outline quality.
- **Architecture:** MONAI **SegResNet** (init_filters=16, GroupNorm, ~4.7M params), **fine-tuned from SuPreM** supervised pretrained weights (AbdomenAtlas, same JHU lab). From-scratch SegResNet is our control.
- **Input construction ("whole-box ROI"):** we crop each CT to the pancreas bounding box (+ margin) and resample the *entire box* into one fixed **128³ cube at 1.5mm** isotropic, fed as a single input each step (no random sub-patches). HU windowed to [-100,300] -> [0,1].
- **Loss:** DiceFocal with `include_background=False`. We've also tested Tversky and Focal-Tversky.
- **Autonomy:** the pancreas ROI is currently "provided" (from a ground-truth or a predicted pancreas box via a localize-then-segment cascade we're building). Numbers below are provided-ROI, held-out validation.

## Data
- PanTS Mini release. ~10% tumor prevalence. Our carved training fold has **706 tumor + ~6,494 healthy** cases; we have been training on a **balanced 1:1** ratio (706 tumor + 706 healthy).
- A lesion is a tiny fraction of the volume (~0.04%): extreme foreground-background imbalance.
- Known data-quality issues: ~6-9% of cases have an empty/corrupt combined pancreas mask (some recoverable from head/body/tail subregion masks).
- **Metrics:** lesion Dice on tumor-positive cases; **specificity** = fraction of tumor-free scans with predicted lesion below 50 mm³ ("mask-negative specificity"); **detection sensitivity** = fraction of tumors flagged at all; all per-patient, full-volume sliding-window inference. Reference SOTA for this task is tumor Dice ~0.53.

## Current honest results (held-out validation, n=40, AFTER fixing a validation-leakage bug)
Best model (whole-box, SuPreM transfer, DiceFocal, on ~1,412 clean cases):
- **lesion Dice 0.415, pancreas Dice 0.817, detection 95% (38/40), specificity 15%.**

By tumor size: small <1cm³ Dice **0.11** (86% detected), medium 1-8cm³ **0.42** (100%), large >8cm³ **0.55** (100%).
By contrast phase: venous **0.56**, arterial **0.39**, **non-contrast 0.26** (the hard tail).

## What we've tried — WHAT WORKED
- **SuPreM transfer ≫ from scratch:** transfer reaches pancreas 0.78 / lesion 0.26 / spec 55% (small-data era); from scratch barely learns (pancreas 0.65, lesion 0.12, specificity 0%). Pretraining is essential.
- **Whole-box ROI ≫ random patches:** feeding the whole pancreas box as one cube fixed severe over-prediction — specificity jumped 8% -> 55% (small-data era) — because the model can see the whole organ in context.
- **Data scaling is the dominant accuracy lever:** more tumor training data is the only thing that moved lesion Dice (recipe knobs did not).
- **Tversky-Focal loss (α=0.7 FP weight, β=0.3), mild version (α=0.6):** modest but real win — vs DiceFocal it moved specificity 15%->20% (raw) / 18%->22% (cleaned), detection 95%->98%, whole threshold sweep up ~4pp (spec 32% at threshold 0.90), for a lesion-Dice cost of only 0.016 (within noise). It reduced tumor over-segmentation.

## What we've tried — WHAT DID NOT WORK (nulls / failures)
- Balanced 1:1 patch sampling vs aggressive positive sampling: **null** (no specificity change).
- Loss with `include_background=True`: **rejected** (hurt specificity and Dice).
- Bigger patch / more context (96->128) for accuracy: **null** on lesion Dice (helped specificity slightly = a sens/spec trade).
- Finer resolution (1.2mm, 160³): **null** on lesion Dice (helped the big pancreas, not the tiny tumor).
- **Pure Tversky α=0.7 (no focal term): the pancreas collapsed to Dice 0.000** — a global false-positive penalty made the large organ not worth predicting. Adding the focal term (Tversky-Focal) fixed the collapse.
- Flip test-time augmentation: a specificity dial (spec up, Dice down), not a free win.

## The three weaknesses I most want to fix
1. **Low specificity (~15-20%)** — the model over-calls tumors on *healthy* scans (fires a false lesion on ~80% of tumor-free cases). This is our #1 problem for a CADe tool.
2. **Small-tumor Dice (0.11 on <1cm³)** — near the resolution/detection limit.
3. **Non-contrast phase (Dice 0.26)** — much worse than venous (0.56); contrast conspicuity drives it.

## Hard constraints (recommendations MUST be feasible here)
- **Apple Silicon MPS backend, NOT CUDA.** fp32 (autocast unreliable on MPS). So CUDA-only nnU-Net defaults and very heavy transformers are impractical.
- **Single GPU, ~14 hours per training run**, MONAI ecosystem, dataset on an external drive.
- **SuPreM weight-load compatibility** limits architecture edits (fixed init_filters; adding deep supervision / changing norm breaks the pretrained-weight load on the transfer arm).

## What I want from you
A **prioritized, cited** set of techniques for each of the following, and for each one state: (a) which weakness it targets, (b) expected magnitude of improvement with evidence, (c) rough implementation + compute cost on my constraints, (d) a citation.
1. **Raising specificity / cutting false positives** in extreme-imbalance 3D tumor segmentation — loss functions, hard-negative mining, healthy:tumor ratio, a tumor-presence classification gate / two-stage CADe, calibration/thresholding. What moves specificity *most*?
2. **Improving small-tumor (<1cm³) segmentation** — cascades/finer resolution, deep supervision, loss weighting, or reframing tiny tumors as detection rather than fine outline.
3. **Handling contrast-phase variability** (non-contrast worst) — phase-conditioning, normalization, oversampling, or phase-specific models.
4. **Loss functions beyond Dice/Focal/Tversky** proven for pancreatic or small-lesion segmentation (boundary/Hausdorff, Unified Focal, compound losses, region+distance combos).
5. **Architectures** competitive on pancreatic tumor segmentation that are realistically trainable on Apple MPS in ~14h (SegResNet variants, Swin UNETR, MedNeXt, etc.) — with trade-offs vs my current SegResNet+SuPreM.

**End with the top 3 highest-leverage changes** you would try first given my exact constraints and weaknesses, and why.
