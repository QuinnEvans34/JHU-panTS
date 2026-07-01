# Agent Plan

**Purpose:** the M1A1 "Agent plan" deliverable — a clear distinction between AI-assisted and manual tasks, with specific, realistic examples. (Companion to `Claude.md`, which is the living week-by-week AI-usage record, and `AI-usage.md`, the weekly log.)

> Filename note: the assignment deliverables list names `Claude.md`; the rubric criterion names `agent-plan.md`. This file exists so the rubric's named artifact is present and unambiguous. The two share content intentionally.

---

## Guiding principle

AI accelerates **boilerplate, syntax, and debugging**; the human owns **every decision that affects correctness, methodology, or interpretation**. In a medical-imaging segmentation project the dangerous failures are silent — misaligned masks, slice-level data leakage, a metric that looks great while hiding zero lesion detection — so AI output is reviewed against that risk, not for style.

---

## AI-assisted tasks (specific examples)

- **Boilerplate code** — MONAI transform chains, YAML config loaders, argparse, repo scaffolding. *e.g. "Write a MONAI `Compose`: LoadImaged → EnsureChannelFirstd → Orientationd(RAS) → Spacingd → ScaleIntensityRanged for a [-100,300] HU window."*
- **Debugging** — interpreting MPS/CUDA errors, tensor shape mismatches between CT and mask, NaN losses. *e.g. paste a traceback, ask it to localize a channel-order bug.*
- **Documentation** — drafting README sections, docstrings, design docs, and the final report's methods section from my notes.
- **Library lookup** — how a specific MONAI transform or `sliding_window_inference` argument behaves.
- **Refactoring** — turning a working notebook cell into a clean, config-driven module.
- **Research/verification** — confirming dataset facts (license, scale, pretrained checkpoints) before they go into the proposal.

## Manual / human-owned tasks (specific examples)

- **Methodology decisions** — Level 4.5 as the target, patient-level splitting, the 70/30 positive-sampling ratio, loss choice, single-stage vs cascade. I decide and can defend these.
- **Verifying data correctness** — personally inspecting sanity-check overlays to confirm masks sit on the pancreas. AI can't see whether the green outline is right.
- **Interpreting results** — judging whether a lesion Dice of 0.4 is acceptable; reading failure cases.
- **Scientific honesty** — the "not a diagnostic system" framing, stated limitations, no overclaiming. Non-negotiable, human-owned.
- **Scope calls** — what ships in the 5-week course vs. the capstone.

## Guardrails

- Review every AI-generated block before committing — especially anything touching data splits, masks, or metrics.
- Never trust AI-generated metric numbers; verify against MONAI's own outputs and spot-check by hand.
- Log notable AI interactions weekly in `AI-usage.md` (what worked, what needed correction).
- Keep the agent context file (`CLAUDE.md` at repo root) current so assistance stays aligned with project constraints (config-driven, no committing raw data, no clinical claims).
