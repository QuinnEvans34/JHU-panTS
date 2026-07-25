# Deep-research prompt — how to maximize LESION Dice on pancreatic-tumor CT

Paste the block below into ChatGPT (deep-research mode). It has the full project context, the complete
experiment history with real numbers, our current honest results, the hardware available, and one hard
data constraint. The goal is a rigorous, cited, prioritized set of recommendations for driving **lesion
(tumor) Dice as high as possible** — no constraints on what you may recommend (new architectures,
nnU-Net, ensembles, losses, pretraining, cascades, data strategy, anything).

---

I am building a 3D deep-learning model to segment **pancreatic tumors (lesions)** on CT, and I want a
rigorous, cited, prioritized plan to push my **lesion Dice** as high as possible. My current honest,
leakage-free number is **0.415**; the published reference for this task is ~0.53; my stretch goal is to
approach or beat that. Please ground your answer in the pancreatic-tumor and abdominal-CT segmentation
literature (PanTS, SuPreM / AbdomenAtlas, the PANORAMA pancreatic-cancer challenge, nnU-Net pancreas
results, MedNeXt, Swin UNETR, STU-Net, and small-lesion / class-imbalance segmentation work). **Do not
constrain your recommendations to my current setup** — if switching frameworks, architectures, or
training regimes is the right call, say so and justify it. I have described everything I have already
tried so you can build on it rather than repeat it.

## The task
- 3D semantic segmentation of background / pancreas / pancreatic-lesion on the Johns Hopkins **PanTS**
  dataset. Framed as a non-diagnostic **CADe assist** (flag + outline a possible tumor for a radiologist).
- The headline metric I want to raise is **lesion Dice on tumor-positive cases** (per-patient,
  full-volume sliding-window inference). Secondary metrics I track: detection sensitivity (~95% now),
  and mask-negative specificity (currently weak, ~15–40%) — but **this request is specifically about Dice.**

## Current model + pipeline
- **Architecture:** MONAI **SegResNet** (init_filters=16, GroupNorm, ~4.7M params), fine-tuned from
  **SuPreM** supervised pretrained weights (AbdomenAtlas, same JHU lab); the final head is re-initialized
  to 3 classes. From-scratch is my control.
- **Input ("whole-box ROI"):** crop each CT to the pancreas bounding box (+16-voxel margin), resample the
  *entire box* into one fixed **128³ cube at 1.5 mm** isotropic, fed as a single sample per step. HU
  windowed to [-100,300] → [0,1].
- **Loss:** DiceFocal (include_background=False). I have also tried Tversky and Focal-Tversky.
- **ROI:** currently "provided" (from a GT or a predicted pancreas box via a localize-then-segment
  cascade I built). The 0.415 is provided-ROI, held-out validation.
- **Training:** AdamW, warmup→cosine LR, 24k steps to convergence, seed-fixed, single-GPU.

## The data — and the ONE hard constraint
- PanTS Mini: ~9,900 cases, **~10.4% tumor prevalence** (~1,033 tumor cases total). Patient-level,
  tumor-stratified splits: ~7,200 train / 1,800 val / 901 official test (untouched).
- **CONSTRAINT: my clean training fold contains only ~706 tumor cases, and I already train on all of
  them.** The other ~6,494 training cases are tumor-FREE. So I cannot add more *tumor* examples from this
  dataset — the tumor-data lever is essentially exhausted. (This matters: my biggest past gains came from
  scaling *tumor* data, which I can no longer do. Adding more *healthy* data raises specificity, not Dice.)
- Extreme foreground imbalance: a lesion is ~0.04% of a full scan's voxels. Lesion volume ranges 2 –
  732,388 mm³ (median ~4,700). Metadata includes contrast phase (non-contrast / arterial / venous),
  4 scanner manufacturers, and ~20+ sites.
- Known data-quality issues (already handled): ~11–14% of cases had empty/corrupt masks; I audit and
  exclude them and rebuild the pancreas mask as head∪body∪tail.

## Everything I have already tried (build on this — don't repeat it)
**What WORKED (kept):**
- **SuPreM transfer ≫ from scratch** (controlled): transfer reaches usable accuracy; from scratch barely
  learns the pancreas (0.65) and false-alarms a tumor on every healthy scan. Pretraining is essential.
- **Whole-box ROI ≫ random sub-patches:** feeding the whole pancreas box as one cube fixed severe
  over-prediction and was my single biggest jump; specificity rose sharply and lesion Dice improved.
- **Data scale-up (tumor cases) is the dominant Dice lever:** tripling tumor data moved lesion Dice
  0.263 → 0.313; using all available tumor cases got me to the current 0.415. (Now exhausted — see constraint.)

**What DID NOT work (nulls / rejected, with the honest reason):**
- Balanced 1:1 vs aggressive positive **sampling ratio**: null on Dice.
- Loss **include_background=True**: rejected (hurt Dice + specificity).
- **Bigger patch** (96→128) for accuracy: null on lesion Dice (helped specificity slightly = a sens/spec trade).
- **Finer resolution** (1.2 mm, 160³): null on lesion Dice (helped the big pancreas, not the tiny tumor).
- Pure **Tversky (α=0.7)**: pancreas collapsed to 0 (global FP penalty made the large organ not worth
  predicting); Focal-Tversky (α=0.6) fixed the collapse and gave a modest specificity gain, small Dice cost.
- Flip **test-time augmentation**: a specificity dial (spec up, Dice slightly down), not a Dice win.
- **Anatomy-aware auxiliary supervision** (my most recent, most rigorous experiment): a 5-class model
  that also learns pancreas head/body/tail as an auxiliary task, run as a clean single-variable
  experiment (only the auxiliary weight changes), with frozen hashed cohorts, a shared initialization,
  and deterministic resume. At an intermediate 12k-step checkpoint it looked like a win (+0.041 lesion,
  bootstrap CI excluding 0), **but at convergence (24k) it was a NULL** — lesion +0.023 with a CI that
  includes 0, plus a small but significant pancreas regression (−0.014). I rejected it. (The 12k result
  was a false positive: the anatomy arm converges faster, so it only *looked* ahead at the intermediate.)

**A correctness note (for credibility):** I caught and fixed a validation-leakage bug — my scaled
training splits had overlapped the validation set, inflating earlier numbers (a contaminated 0.528 became
an honest 0.415). All numbers above are the post-fix, leakage-free values.

## Current honest results (leakage-free, held-out, n=40)
- **Lesion Dice 0.415**, pancreas 0.817, detection sensitivity 95%, specificity 15% (provided-ROI).
- **Autonomous cascade** (predicted pancreas box, not GT): lesion ~0.48 in an earlier run — but that was
  on the contaminated splits and needs a clean rerun; treat it as indicative, not final.
- **The key diagnosis (per-case analysis):** the model reliably *detects* tumors (95%) but **over-segments
  them 3–13×** (predicts far too much lesion), which both caps Dice and drives the low specificity.
  - By tumor size: **small <1 cm³ Dice 0.11** (86% detected), medium 1–8 cm³ 0.42, large >8 cm³ 0.60.
    The small-tumor cases are the biggest drag on the mean.
  - By contrast phase: venous 0.56, arterial 0.46, **non-contrast 0.25** (the hard tail).

## Hardware available (do not assume I'm limited to my Mac)
- **Primary dev machine:** MacBook Pro, Apple M-series, 64 GB unified memory, **PyTorch MPS backend (not
  CUDA)**. My pipeline was engineered to fit MPS (fp32, moderate patches), which is why CUDA-only tooling
  (e.g. stock nnU-Net) has been impractical here.
- **Also available:** a Windows/Linux laptop with an **NVIDIA CUDA GPU** (32 GB system RAM; VRAM TBD).
  This unlocks CUDA-native frameworks (nnU-Net, MedNeXt, etc.) if they're worth it.
- **Time:** a long weekend (Thursday night → Monday morning) available for a large uninterrupted run.

## What I want from you
A **prioritized, cited** plan to maximize **lesion Dice**, given that my tumor-data lever is exhausted.
For each recommendation, state: (a) expected magnitude of Dice improvement with evidence/citation,
(b) rough implementation + compute cost on my hardware, (c) the main risk or failure mode. Please cover:

1. **Is switching to / benchmarking against nnU-Net (or MedNeXt / STU-Net / Swin UNETR) the highest-Dice
   move on this data?** How much Dice would you realistically expect over a tuned custom SegResNet, and
   how much of that is the 5-fold ensemble vs the architecture vs the auto-configured cascade? Worth the
   weekend on the CUDA laptop?
2. **Attacking the small-tumor drag (Dice 0.11 on <1 cm³):** coarse-to-fine cascades, higher-resolution
   second-stage segmentation, detection-guided segmentation, deep supervision, or reframing tiny tumors
   as detection rather than fine outline — what actually moves small-lesion Dice?
3. **Losses beyond Dice/Focal/Tversky** proven for pancreatic or small-lesion segmentation
   (boundary/Hausdorff, Unified Focal, compound region+distance losses, blob/topology losses) — which
   most directly raise Dice for an over-segmenting model?
4. **Ensembling / multi-fold / multi-model** and **test-time strategies** — how many Dice points, at what
   cost, and which are worth it.
5. **Getting more out of the fixed ~706 tumor cases:** stronger data augmentation, synthetic tumor
   augmentation / copy-paste / generative tumor synthesis, self-supervised or additional pretraining,
   semi-supervised use of the ~6,494 healthy cases or unlabeled data, cross-validation to use every
   tumor case for training.
6. **Better transfer / pretraining** than supervised SuPreM (e.g. self-supervised abdominal-CT
   pretraining, larger SuPreM/STU-Net backbones) — is a bigger pretrained backbone worth it given my
   small tumor set?

**End with the top 3 highest-leverage changes** you would make first to raise lesion Dice given my exact
situation (tumor data capped at ~706, a CUDA laptop and a long weekend available, current honest Dice
0.415, reference SOTA ~0.53), and an honest assessment of whether ~0.55–0.60 is realistically reachable
on this dataset or whether ~0.45–0.50 is the practical ceiling.
