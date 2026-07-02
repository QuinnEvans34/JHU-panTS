# System Overview — The Whole Picture

**One-page synthesis of the entire project.** Use this to explain the system end-to-end (e.g. the Week 1 check-in). Detailed reference lives in `architecture.md`, `data-pipeline.md`, `training.md`, `experiment-tracking.md`, `ui.md`.

---

## In one sentence

A 3D deep-learning pipeline that takes an abdominal CT scan, segments the **pancreas** and any **pancreatic lesion**, and flags *"there could be a tumor here"* — an annotation-assist tool for radiologists, **not a diagnosis**.

## The 30-second version

Radiologists and imaging annotators have to hand-trace the pancreas and any tumor on CT — slow, tedious work on a hard-to-see organ. My system does the first pass automatically: it outlines the pancreas and lesion in 3D and flags cases that may contain a tumor, so the user **accepts, edits, or rejects** the outline instead of drawing from scratch. It's built on the Johns Hopkins **PanTS** dataset with MONAI/PyTorch, runs on my MacBook (Apple Silicon), and a human always makes the clinical call.

---

## The system, stage by stage

**1 · Data.** Johns Hopkins **PanTS** — 9,000 training CT volumes + 901 test, each a 3D NIfTI with voxel-wise masks for the pancreas (and head/body/tail), the `pancreatic_lesion`, and ~28 surrounding structures, plus `metadata.xlsx`. It's on my external drive now. A **manifest** joins each CT to its masks; I split **by patient** (never by slice, to avoid leakage) and preprocess with MONAI: canonical orientation, resample voxel spacing, clip CT intensities to a soft-tissue window, and sample **3D patches biased ~70% toward lesion voxels** (because the tumor is a tiny fraction of the scan).

**2 · Model & training.** A **SegResNet** (a 3D U-Net variant) in MONAI, trained on Apple's **MPS** backend. Two versions for a clean comparison: one **from scratch** (baseline) and one **fine-tuned from SuPreM** — pretrained weights from the same JHU lab on abdominal CT. Loss is Dice + cross-entropy (robust to the extreme class imbalance), optimizer is **AdamW**. Everything is logged to **MLflow** and checkpointed so training resumes across sessions.

**3 · Evaluate (the CADe flag).** At test time I run **sliding-window inference over the full volume**, then a small wrapper turns the lesion mask into a detection: *possible tumor — location — volume — confidence*. I report **pancreas and lesion Dice separately** (an average would hide tumor failure), plus the business metrics: **patient-wise sensitivity and specificity** — "of patients with a tumor, how many did we flag; of healthy patients, how many did we correctly leave alone."

**4 · Serve.** A clean **React + NiiVue** web app: a tri-planar slice viewer with the pancreas/lesion overlays, a rotatable **3D** view of the organ with the tumor inside it, the CADe summary, and a button to **export the mask** for editing in a real tool. Static-first (reads precomputed predictions — no backend needed). The radiologist accepts/edits/rejects — the actual workflow the project supports.

---

## Scope — what's in, what's out (realism)

- **Level 4.5 (primary target):** background / pancreas / lesion. This is the line that must hold.
- **Level 4:** lesion-only (built, not primary). **Level 4.7:** add a few peri-pancreatic structures (evidence says this lifts tumor accuracy). **Level 5:** full multi-structure — stretch, one config change.
- **Out of scope, on purpose:** any clinical *diagnosis*, tumor-*type* call, or claim of medical-device reliability. The system says "look here," a human decides.
- **Course vs capstone:** the 5-week course delivers Level 4.5 + the CADe flag + the UI. The 10-week capstone extends the *same codebase* — an ROI localize→segment cascade, full-scale training on all 9,000 cases, Level 5, and (optionally) submitting the model to JHU for **external out-of-distribution validation** on their proprietary cohorts.

## Dataset validity (a check-in focus)

Open-source (CC-BY-NC-SA, non-commercial — fits an academic tool), created by JHU, accepted to **NeurIPS 2025**. It's a **static** benchmark, not a live feed — confirmed. The paper's headline "36,390 scans" = 9,901 public (what I have: 9,000 train + 901 test) + 26,489 **proprietary** external-test scans held by JHU for leaderboard evaluation. So I have 100% of the downloadable data, and I understand exactly what the rest is.

## What "good" looks like (honest targets)

State-of-the-art on PanTS is ~**0.53** tumor Dice, ~**80%** patient sensitivity, ~**90%** specificity. Pancreatic lesions are notoriously hard (small, often near-invisible on CT), so a **lesion Dice of ~0.35–0.50 is a respectable result**, framed against those numbers — not against an unrealistic 0.9. Pancreas Dice should be much higher (~0.8+).

## Hardware & practical reality

MacBook Pro **M5 Pro**, 64 GB unified memory, PyTorch **MPS** (not CUDA). Patch-based training + a tiny 4.7M-param model + transfer learning = feasible on a laptop. Long runs are checkpointed and resumable.

## Risks & honest unknowns

The lesion is the hard part — if it underperforms, the fallback is a strong **pancreas-segmentation** result plus an analysis of *why* the tumor is hard (still a complete project). MPS has occasional op gaps (managed). One small data question remains: confirm whether one case = one patient in `metadata.xlsx` (for leak-free splits).

## Where we are (Week 1)

Repo + full design docs done · dataset downloaded and verified on the drive · pretrained model identified · proposal complete. **Next:** code scaffold → sanity-check one case → first 3-view overlays (the Week 1 milestone).

---

## Check-in talking points

The Week 1 check-in focuses on **scope, dataset validity, and proposal clarity**. Crisp answers:

- **Scope:** "Primary target is Level 4.5 — pancreas + lesion segmentation — plus a CADe wrapper that flags a possible tumor. Not diagnosis. Level 5 and the ROI cascade are explicitly capstone stretch, so the 5-week scope stays realistic."
- **Dataset validity:** "PanTS, open-source from JHU, NeurIPS 2025, static benchmark. I have the full public set — 9,000 train + 901 test + all labels — on an external drive and I've verified the on-disk structure. The larger '36k' figure includes proprietary external-test cohorts I can't download; they're for leaderboard evaluation."
- **Why it's feasible on a laptop:** "Patch-based 3D training, a 4.7M-param SegResNet, transfer learning from SuPreM, and resumable checkpoints on Apple's MPS backend."
- **Business framing:** "The user is a radiologist/annotator; the model proposes contours they accept, edit, or reject — saving manual tracing time. A human always makes the clinical call."
- **How I'll know it works:** "Pancreas and lesion Dice reported separately, plus patient-wise sensitivity and specificity, evaluated on full-volume inference — measured against PanTS SOTA."

**Likely questions & honest answers:**
- *"Isn't this diagnosis?"* → No — it outputs a contour and a "look here" flag; the radiologist decides.
- *"Data leakage?"* → Patient-level splits, never by slice.
- *"The tumor is tiny — won't it predict all background?"* → Pos/neg patch sampling + Dice loss + reporting lesion Dice separately so the failure can't hide.
- *"What if lesion segmentation fails?"* → Fallback to a strong pancreas result + failure analysis; still complete.
