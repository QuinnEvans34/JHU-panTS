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

<!-- Add the next daily entry below. -->

