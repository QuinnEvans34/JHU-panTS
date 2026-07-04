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

<!-- Add Week 2, 3, 4, 5 sections below as the project progresses. -->
