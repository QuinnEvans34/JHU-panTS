# Interview prep — understand & walk through the system

For the "do you understand what you built" check. Three parts: (1) the system in 1–2 sentences,
(2) a file-by-file walkthrough that follows one scan through the pipeline, (3) what the model is
doing and why it was chosen. Ends with likely Q&A. Using AI is allowed — the point is that I can
explain how it works, not recite syntax.

---

## 1. What this system is (say one of these first)

**Technical:** "It's a 3D deep-learning pipeline that segments the pancreas and pancreatic tumors on
CT scans — it takes a CT volume and labels every voxel as background, pancreas, or lesion — built by
fine-tuning a medical pretrained model (SuPreM) on the Johns Hopkins PanTS dataset."

**Product framing (lead with this if they ask 'what's it for'):** "It's a CADe — computer-aided
*detection* — assist: it flags and outlines a possible tumor for a radiologist to accept, edit, or
reject. It deliberately does **not** diagnose or classify the tumor; that keeps the scope honest."

One-line mental model: **"the model" is a `.pt` file of learned weights; training is the search for
good weights; everything else loads that file and runs it on new scans.**

---

## 2. The walkthrough — follow one CT scan through the repo

Tour it in pipeline order. For each file: what it is, and the one thing to say.

### A. Data prep (run once, up front)
- **`scripts/build_manifest.py`** → scans the dataset on the external drive and writes
  `outputs/manifest.csv`, one row per case with its file paths + metadata + a `has_lesion` flag.
  *Say:* "This is the index of the dataset — it pairs each CT with its label masks."
- **`scripts/create_splits.py`** → carves **patient-level, tumor-stratified** train/val/test lists
  (uses scikit-learn's `StratifiedGroupKFold`). *Say:* "Split by patient, not by slice, so the same
  patient can't be in both train and test — that's the first leakage guard."
- **`scripts/make_scaled_split.py` / `build_exp26_cohorts.py`** → build specific experiment cohorts
  drawn **only from `train.txt`**, with a disjointness assert. *Say:* "This is where I fixed the
  leakage bug — the split builder now samples only from the training fold and asserts it never
  touches val or test."

### B. The recipe
- **`configs/level45.yaml`** → one YAML with every setting: paths, label mapping, preprocessing
  (1.5 mm spacing, HU window, whole-box), the SegResNet architecture, transfer settings, the loss,
  the AdamW optimizer + schedule, training length, validation, inference/post-processing.
  *Say:* "The pipeline is config-driven — I change behavior with a flag or a YAML edit, never by
  editing code, so every experiment is one knob turned."

### C. Training — `scripts/train.py` drives everything in `src/`
Walk the data flow (this is the core of the interview):
- **`src/utils/config.py`, `paths.py`, `seed.py`** → load the recipe, resolve concrete file paths,
  seed everything (seed 42) for reproducibility.
- **`src/data/dataset.py`** (`build_records`, `get_dataset`) → reads the manifest and, for each case
  in the chosen split, gathers its CT + mask paths and wraps them in a cached MONAI dataset.
- **`src/data/transforms.py`** → the **preprocessing pipeline**: load CT + masks → compose one label
  map (pancreas = 1, lesion = 2, lesion wins on overlap) → reorient to RAS → **crop to the pancreas
  bounding box** → resample to 1.5 mm → window HU to [0,1] → **resize the whole box into one 128³
  cube** (the "whole-box" idea) → light augmentation. *Say:* "This turns a raw CT into a standardized
  128³ cube centered on the pancreas — same size, same scale, every time."
- **`src/models/segresnet.py`** (`build_model`, `load_suprem`) → build the SegResNet and load the
  SuPreM pretrained weights, **re-initializing the final layer** from SuPreM's 32 classes to our 3.
- **`src/training/losses.py`** (`build_loss`) → the loss. Default **DiceFocal**: Dice rewards overlap
  with the true region, Focal forces attention onto the rare tumor voxels.
- **`src/training/trainer.py`** → AdamW optimizer, warmup→cosine LR schedule, and atomic checkpoint
  save/load.
- **The loop in `train.py`** → for 24,000 steps: **forward** (predict) → **loss** (how wrong) →
  **backprop** (which way to nudge each weight) → **optimizer step** (nudge) → advance the LR →
  log to MLflow. Every 500 steps it validates and saves `best.pt` if it improved.
- **`src/inference/sliding_window.py`** (`validate`, `predict_volume`) → validation runs the model
  over held-out cases with **full-volume sliding-window inference** (never patch-only at eval).
- **`src/training/metrics.py`** (`DiceEvaluator`) → reports **pancreas and lesion Dice separately**.
- Output: `best.pt` (best-on-validation weights) + an immutable per-run archive so a good model can
  never be silently overwritten (the fix after I lost a checkpoint earlier).

### D. Evaluation & analysis
- **`scripts/evaluate.py`** → lesion + pancreas Dice on tumor-positive cases, **specificity** on
  tumor-free cases, and a probability-threshold sweep (the operating-point dial).
- **`scripts/analyze_cases.py`** → per-case breakdown: detection sensitivity, Dice by tumor size and
  by contrast phase (venous / arterial / non-contrast).
- **`scripts/cascade_eval.py`** → the **autonomous** localize-then-segment pipeline: a first model
  finds the pancreas on the full scan, and its *predicted* box feeds the segmenter — no ground-truth
  hand-holding — plus a millimeter containment audit.
- **`scripts/paired_bootstrap.py`** → the paired statistics (e.g. 26B − 26A mean difference +
  bootstrap confidence interval) for the anatomy experiment.

### E. Output & the viewer
- **`scripts/export_case.py`** → turns a prediction into the files the UI reads (NIfTI + 3D meshes +
  a `results.json`).
- **`ui/`** → a static React + **NiiVue** web viewer: tri-planar CT with pancreas/lesion overlays, a
  rotatable 3D mesh, a prediction-vs-ground-truth toggle, and a plain-language "possible lesion"
  summary. Static-first: the pipeline pre-computes predictions, the UI just displays saved files.

*(One-off / superseded scripts now live in `scripts/legacy/` — exploration helpers and finished
experiment-split builders, kept out of the main folder.)*

---

## 3. What the model is doing, and why this model

**The model: a MONAI SegResNet — a 3D convolutional encoder-decoder (the U-Net family).**
- The **encoder** takes the 128³ CT cube and progressively compresses it — each stage shrinks the
  spatial size but captures more abstract "what tissue is this" features.
- The **decoder** expands back up to full resolution, producing a **per-voxel class** (bg / pancreas
  / lesion). **Skip connections** carry fine detail from the encoder to the decoder so edges stay sharp.
- So: input a cube of CT, output the same cube with every voxel labeled. That labeled mask is the
  prediction.

**Why SegResNet and not the famous nnU-Net?** Two honest reasons: (1) the **SuPreM pretrained weights
are built on SegResNet** (same JHU lab as the dataset), so I can transfer them; (2) I train on an
**Apple-Silicon GPU (MPS backend, not CUDA)**, and nnU-Net's defaults are CUDA-oriented, so I stay in
the MONAI/SegResNet ecosystem that runs well here.

**Why transfer from SuPreM instead of training from scratch?** SuPreM is a SegResNet already
pretrained on a large abdominal-CT dataset — it already "knows" what livers, kidneys, and the
pancreas look like. I fine-tune it to my 3-class task and swap in a fresh output head.
*Analogy:* training from scratch is teaching medicine to someone with no background; transfer is
hiring a radiology resident and teaching them one specific task. And I **proved it** (EXP-09): from
scratch the model barely learns and false-alarms a tumor on every healthy scan; with SuPreM it works.

**Why "whole-box"?** Pancreatic tumors are ~0.04% of a full scan's voxels — a needle in a haystack.
So I crop to the pancreas bounding box and resize that whole box into one 128³ cube, so the model
always sees the whole organ in context at a consistent scale. This was a real breakthrough — it fixed
severe over-prediction and raised specificity.

**What I'm working on now (anatomy-aware):** a 5-class version that also learns pancreas head/body/
tail as an auxiliary task, to teach the model *where in the pancreas* it is. Run as a clean
single-variable experiment (only the auxiliary weight changes), it gave a statistically-significant
lesion-Dice gain and better specificity.

---

## 4. Likely questions → crisp answers

- **"In one sentence, what is it?"** → A 3D CNN that segments the pancreas and pancreatic tumors on
  CT and flags a possible tumor for a radiologist — a detection assist, not a diagnosis.
- **"Where does training happen?"** → Locally, on the MacBook's Apple-Silicon GPU (MPS), by running
  `scripts/train.py`. It produces a `.pt` checkpoint.
- **"What actually *is* the model?"** → A MONAI SegResNet (a 3D U-Net-style CNN); its learned weights
  live in a `.pt` file. I fine-tune it from SuPreM pretrained weights.
- **"How does a scan become a prediction?"** → Load CT → crop to the pancreas box → resize to a 128³
  cube at 1.5 mm → the network labels every voxel bg/pancreas/lesion → post-process → that mask is
  the prediction.
- **"What is Dice?"** → An overlap score between the predicted mask and the true mask, 0 to 1; 1 is
  perfect overlap. Good for imbalanced targets like a tiny tumor.
- **"Why 3D and not 2D slices?"** → A tumor is a 3D structure; 3D convolutions see context across
  slices, which 2D would miss. It's why classic tabular ML (scikit-learn) doesn't fit — this is
  volumetric deep learning.
- **"How do you avoid data leakage?"** → Patient-level, stratified splits; the trainer asserts the
  training split is disjoint from val/test at startup; the official test set is untouched until the
  end. I also *caught and fixed* a real leakage bug, which is why the guard exists.
- **"How do you track experiments?"** → MLflow (local SQLite) logs metrics/params for every run, and
  `docs/experiments.md` records each run as hypothesis → result → accept/reject.
- **"What are your metrics and why?"** → Lesion Dice (outline quality), detection sensitivity (did we
  flag it at all — the CADe headline, ~95%), and specificity (false alarms on healthy scans), all
  per-patient with full-volume inference. Reference SOTA lesion Dice is ~0.53.
- **"What's the training stack?"** → PyTorch + MONAI (MONAI is the medical-imaging layer on PyTorch).
  scikit-learn is used once, only to make the stratified splits — not for the model.
- **"What was the hardest part / what did you learn?"** → The model and the discipline around it:
  single-variable experiments, catching my own leakage bug, and building a checkpoint archive after
  losing a good model. The data is imbalanced and small, so most gains came from *more data* and the
  whole-box framing, not from tuning knobs.
- **"What would you do next?"** → Finish the anatomy-aware runs to convergence, push the autonomous
  cascade, add more healthy data for specificity, and extend toward a multi-structure model (the
  capstone).

---

## 5. If asked to open a file — a safe order to narrate
`configs/level45.yaml` (the recipe) → `scripts/train.py` (the loop, top-to-bottom) →
`src/data/transforms.py` (how a CT becomes a 128³ cube) → `src/models/segresnet.py` (the network +
SuPreM load) → `src/training/losses.py` (DiceFocal) → `scripts/evaluate.py` (how I score it). Each
file's top docstring now explains its job in plain English — read that first, then the function names.
