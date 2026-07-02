# Standup Log

Daily check-ins (Mon–Fri), added chronologically. Brief and honest — 3–5 sentences. **Do not edit or delete past entries.** In Weeks 1, 3, and 5, one entry is a 1-on-1 retrospective instead of the standard format.

**Standard entry template:**

```
## [Week X — Day] — [Date]
**Worked on:** What I actually worked on today.
**Up next:** What I'm doing next session.
**Blockers:** Any challenges/blockers, or "None."
```

**1-on-1 retrospective template (Weeks 1, 3, 5):**

```
## [Week X — 1-on-1 Retrospective] — [Date]
**What we discussed:** ...
**Feedback received:** ...
**Action items:** ...
**Reflection:** ...
```

---

## [Week 1 — Monday] — 2026-06-29
**Worked on:** Set up the project repository and added the three assignment briefs (M1A1, M1A2, M1P1) as reference docs. Selected the PanTS dataset, verified its details (JHU, NeurIPS 2025, CC-BY-NC-SA license, ~346 GB Mini release, static/not real-time), and locked the project framing: Level 4.5 pancreas + lesion segmentation with a radiologist annotation-assist business framing. Drafted the proposal and 5-week schedule.
**Up next:** Confirm GPU VRAM, scaffold the code repo (configs/src/scripts), and download a small local PanTS subset.
**Blockers:** None.

## [Week 1 — Tuesday] — 2026-06-30
**Worked on:** Big planning day; project approved by the professor. Locked the scope — Level 4.5 segmentation (background/pancreas/lesion) plus a CADe wrapper that says "there could be a tumor here," no tumor-type or diagnostic call. Designed the full pipeline end-to-end and captured it across new design docs: `architecture.md` (master), `training.md`, `experiment-tracking.md` (MLflow), and `ui.md` (Streamlit tri-planar viewer + rotatable 3D mesh). Settled key technical decisions: 3D handling (RAS orient, resample, HU window, patch-based training with 70/30 pos-neg sampling), SegResNet with AdamW + cosine/warmup, InstanceNorm-not-BatchNorm, whole-body→single-stage ROI now with a localize→segment cascade saved for the capstone, MLflow as the tracker, and resumable checkpoints for laptop/MPS training. Chose the transfer model — fine-tune **SuPreM's SegResNet** (~4.7M params, same JHU lab, abdominal-CT pretraining) against a from-scratch SegResNet baseline — then got an independent ChatGPT deep-research **second opinion that agreed**, and adopted its refinements (two-track clean-vs-practical ablation, match SuPreM normalization, wider HU window test, harder negatives near the pancreas, NSD + per-case CC lesion sensitivity, CPU-stitched sliding window, and an evidence-backed anatomy-context ablation worth ~+10pp tumor Dice). Also finalized the Week 1 submission set: personalized the proposal's Why/Takeaway in my own voice, created `agent-plan.md` and the `audience-notes-week1.md` template, and set up the external hard drive to hold the dataset.
**Up next:** Download the PanTS data + SuPreM weights to the external drive, then (before class at 1:30) look at the real files, confirm label filenames + whether case == patient, finalize `data-pipeline.md`, and move into environment setup + a minimal scaffold. Goal for the weekend: get something training on MPS.
**Blockers:** None.

## [Week 1 — 1-on-1 Retrospective] — 2026-07-01
<!-- draft — reword in my own voice before submitting -->
**What we discussed:** Walked the instructor through the overall project outline and its feasibility — what the system will look like end-to-end, whether it's realistically achievable in the 5-week window, and how the model actually works. We also talked about why this project genuinely interests me, and the possibility of carrying it forward as my capstone project.

**Feedback received:** Mostly positive. The instructor engaged with good, probing questions — how the project will actually work, the type of model I chose (fine-tuning SuPreM's SegResNet), how large the dataset is, and how the CT scans are stored on my laptop / external drive. A highlight: he asked whether I could use **3D images in the UI**, which was exactly my own plan — I told him I'm building the GUI around 3D visualization of the pancreas and the lesion/cancer detection, so it was great to already be aligned on that.

**Action items:** Go much deeper on the model — how it works, how it learns, and the specific ins and outs of the SuPreM SegResNet I'm using — so I can clearly explain and defend *why it's the best choice* to both my classmates and the instructor. The model is the most complex part of the project and the area where I most need to level up my understanding.

**Reflection:** A couple of things surprised me. First, how good the dataset is — the quality of the pancreas annotations/labels genuinely impressed me. Second, how much storage it takes — about **410 GB** on my drive. My main takeaway is that the model itself is the hardest, most complex piece, so that's where I'll focus my learning next.

<!-- Add the next daily entry below. -->

