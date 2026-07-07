# AI Usage Log

**What this file is.** A weekly record of how I actually used AI tools on this project — the tasks it helped with, the prompts/context that worked well, and where its output needed correction. This is the *record* of what happened; `agent-plan.md` is the plan/rules for how the agent should work, and `Claude.md` is the higher-level usage plan. Append a new section each week; do not edit past weeks.

---

## Week 1 — Jun 29 – Jul 5

**Tasks I used AI assistance for:**
- Verifying the PanTS dataset facts before writing the proposal — that it's an open-source Johns Hopkins benchmark (NeurIPS 2025), the license (CC-BY-NC-SA), the ~346 GB size, that it is a static (not real-time) dataset, and that downloadable pretrained checkpoints exist.
- Pressure-testing the project idea against the grading rubric, which surfaced that I needed to name a concrete business user and the decision the model supports.
- Drafting the planning/design documents (architecture, data-pipeline, training recipe, experiment tracking, and UI docs).
- Getting a second opinion on the model choice — I had ChatGPT's deep-research mode review the decision to fine-tune SuPreM's SegResNet; it agreed and suggested refinements I adopted (keeping the scratch-vs-transfer comparison clean, matching SuPreM's preprocessing, and adding surface-distance and per-lesion sensitivity metrics).
- Writing the pipeline code with me directing each step: the config/utility layer, the manifest builder, the patient-level splits, the MONAI transforms and dataset, the sanity-check script, the SegResNet model and SuPreM transfer loader, the loss/metrics/trainer, and the training entrypoint.
- Debugging real errors during the first training runs (details below).

**Prompts / context that worked well:**
- Loading the assignment rubrics into the repo first, then giving the project idea, so the drafts mapped directly onto how the work is graded.
- Asking pointed, verifiable questions like "transfer learning vs. from scratch — what pretrained models actually exist for this exact task right now?", which pushed the AI to verify current resources instead of answering from memory.
- Pasting full error tracebacks and the exact training output, which let the AI localize each fix quickly.
- Keeping a `CLAUDE.md` context file and a `HANDOFF.md` so a fresh AI session could pick up the entire plan in a single message.

**Cases where AI output needed correction or specific instruction:**
- The model would not build until GroupNorm was passed as a tuple with `num_groups`; the first attempt used a bare string and errored.
- Some scans are thinner than the 96-voxel patch, which crashed the random crop until we added padding (`SpatialPadd`) to guarantee a minimum size.
- Training was slow until we enabled dataset caching, and the overfit test needed a flat learning rate (instead of decaying it) before it would actually memorize the cases.
- The lesion score kept reading `0.000` and looked like a failure, but it was actually the metric reporting "not applicable" for tumor-free cases; we fixed the logging to say `n/a` and forced the overfit onto tumor-positive cases, after which the lesion learned (reaching ~0.7 Dice).
- MLflow would not install on Python 3.14 (too new for its dependencies), so we recreated the environment on a Python 3.12 virtual environment.
- Adjusted the loss to exclude the background class so the tiny lesion (~0.04% of the volume) received enough gradient to be learned.

---

## Week 2 — Jul 6 – Jul 12

Tasks I used AI assistance for:

- Building the Week 2 EDA notebook from the real manifest. I directed what to profile; the AI wrote the notebook cells, executed them against the actual 9,901-case manifest, and embedded the real charts, so every number in it is reproducible rather than made up.
- Writing the data understanding report around those real numbers, including the honest Airflow framing (a static dataset does not need a scheduled ingestion DAG) and the real Dataset and DataLoader code snippet.
- Generating the overfit-a-single-batch figure by pulling the actual training curves out of the MLflow run database instead of drawing a fake one.
- Setting up the evaluation properly and interpreting the results. This was the important one: the AI helped me build evaluate.py so it scores lesion accuracy only on tumor-positive cases and measures specificity separately on tumor-free cases, which is what exposed the real behavior of the model.
- Turning the evaluation numbers into a concrete tuning plan for Weeks 3 and 4, then coding the first three levers of that plan ahead of time: a lesion probability-threshold sweep in evaluate.py, an anatomical constraint that demotes lesion predictions floating away from the pancreas, and a harder-negatives patch sampler. I had each one's logic unit-tested on synthetic volumes in a sandbox before trusting it, since I could not run the real model there.

Prompts and context that worked well:

- Asking the AI to locate the manifest by walking up the folder tree rather than hardcoding a path, so the notebook runs no matter where it is opened from.
- Pasting the raw terminal output of the evaluation run and asking what it actually means for the model, instead of asking for a generic interpretation.
- Keeping the CLAUDE.md context file current so a fresh session picks up the exact state, including the latest metrics.

Cases where AI output needed correction or specific instruction:

- The first overfit figure it generated was the noisy full dev-subset run, not the clean single-batch overfit. I had it go back into the MLflow database, find the actual Stage 0 run (loss 1.87 to 0.54), and build a two-panel figure that also shows the tumor-positive overfit where the lesion reaches about 0.85.
- It initially left em dashes in the notebook headers. I have it strip every em dash and asterisk from anything written in my voice, and I verify that before accepting a draft.
- I directed the interpretation of the specificity result. The model scores 8 percent specificity and post-processing did not improve it, and the takeaway (that the false positives are large connected regions, not prunable specks, so the fix is retraining with balanced sampling and an anatomical constraint, not more cleanup) is my read of the data, not something I accepted blindly.

<!-- Add Week 3, 4, 5 sections below as the project progresses. -->
