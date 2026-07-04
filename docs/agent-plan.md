# Agent Plan — Coding-Agent Operating Guide

**Purpose.** This file tells any AI coding agent (Claude, etc.) how it is expected to work on this project, and it distinguishes which tasks are AI-assisted versus human-owned. It satisfies the M1A1 "Agent plan" deliverable.

**How the three AI files relate (so there's no overlap):**
- **`agent-plan.md`** (this file) — the *rules*: how the agent should behave + which tasks are AI vs manual.
- **`AI-usage.md`** — the *record*: a weekly log of what the AI actually did, prompts that worked, and corrections.
- **`Claude.md`** — the higher-level *usage plan* / intent (mirrors the proposal's AI section).
- **`CLAUDE.md`** (repo root) — the *project context*: current state, decisions, and guardrails an agent reads to get up to speed.

---

## Who is in charge

**Quinn (the developer) directs the project and makes the decisions.** The agent's job is to advise, propose, and execute *when asked* — not to run ahead. When something is ambiguous or a decision has real tradeoffs, the agent defers to Quinn.

## Operating rules (what the agent must do)

1. **Do not write code unless explicitly asked.** Default to discussing the approach first, and wait for a clear go-ahead before creating or editing code.
2. **Ask questions whenever anything is unclear or ambiguous** instead of guessing. A clarifying question is always better than a wrong assumption.
3. **Propose before implementing.** For any non-trivial change, briefly explain the plan and the tradeoffs, then implement after approval.
4. **Keep changes small and reviewable** — one logical change at a time, with a short explanation of what changed and why.
5. **Test what can be tested.** Validate pure logic on small synthetic data before handing work off, and provide short "run and verify" instructions, since the real dataset and GPU live on Quinn's machine.
6. **Keep the docs current.** Update `CLAUDE.md` and the design docs whenever a decision or the project state changes, so context never drifts between sessions.
7. **Respect the guardrails** (below) at all times.
8. **Be honest about uncertainty.** Do not overclaim results; surface risks, unknowns, and anything that needs verification.

## AI-assisted tasks (specific, realistic examples)

- **Boilerplate & config code** — MONAI transform chains, argument parsing, YAML config loaders, repo scaffolding. *e.g. "Write the manifest builder that pairs each `ct.nii.gz` with its masks and flags `has_lesion`."*
- **Debugging** — interpreting tracebacks and shape/dtype/MPS errors. *e.g. pasting the `GroupNorm missing num_groups` error and getting the one-line fix.*
- **Documentation** — design docs, docstrings, the README, and the final report's methods section from my notes.
- **Research & verification** — confirming dataset facts, pretrained-checkpoint availability, and library APIs *before* they go into the work.
- **Refactoring** — turning a working script into a clean, config-driven module.

## Manual / human-owned tasks (specific, realistic examples)

- **Methodology decisions** — the Level 4.5 scope, patient-level splitting, the pos/neg sampling ratio, loss choice, single-stage vs. cascade. I decide these and can defend them.
- **Verifying data correctness** — personally inspecting the sanity-check overlays to confirm the masks sit on the right anatomy. The AI can't see whether the outline is actually on the pancreas.
- **Interpreting results** — judging whether a given lesion Dice is acceptable and reading the failure cases.
- **Scientific honesty** — the "segmentation tool, not a diagnosis" framing, the stated limitations, and never overclaiming.
- **Final scope and priority calls** — what ships in the 5-week course vs. the 10-week capstone.

## Guardrails

Never commit raw data · split by **patient**, not slice · full-volume sliding-window evaluation (never patch-only) · report pancreas and lesion Dice **separately** · tumor-positive patch sampling is required · **no clinical or diagnostic claims** · keep the pipeline config-driven · the dataset path comes from config, never hardcoded.
