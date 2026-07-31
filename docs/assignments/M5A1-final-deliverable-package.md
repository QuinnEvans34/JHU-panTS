# M5A1: Final Deliverable Package

**Due:** Thursday 11:59pm (available until Jul 30 11:59pm) · **Points:** 40 · **Submit:** GitHub (branch → merge to main), inside a `deliverables/week5/` documentation folder

## Overview
The culmination of five weeks. The final deliverable is a **complete, professional-quality project package** that a business stakeholder could evaluate, a developer could pick up and run, and you could confidently show in a job interview. Every component should be connected, documented, and presentable.

## Instructions

### 1. Business-Facing UI — screenshots + short walkthrough
- What the UI lets the business user do — inputs, outputs, controls.
- How the UI connects to the deployed model endpoint.
- How data freshness / last-updated info is surfaced to the user.
- Design decisions made with a non-technical user in mind.

### 2. How to Use It — concise, non-technical user guide (`how-to-use.md`)
- What the tool does and who it's for.
- Step-by-step usage — assume the reader has never seen it before.
- What the outputs mean and how a business user should interpret them.
- Any known limitations the user should be aware of.

### 3. README — complete and professional
- Project overview and business problem.
- System architecture — a diagram or clear description of all components.
- Tech stack with versions.
- Setup and installation for a developer.
- How to run the pipeline, the model, and the UI locally.
- Links to key documentation files (`claude.md`, `implementation-plan.md`, `ai-usage-log.md`).

### 4. AI Documentation — final entries
- `ai-usage-log.md` — Week 5 entry **+ a final retrospective section (≥1 paragraph)**: overall AI usage across the project — what worked, what didn't, how the approach evolved, its effect on quality/speed.
- `claude.md` — finalize; should reflect how AI was *actually* used, not just how it was planned.
- `implementation-plan.md` — final Week 5 status note. Did you hit MVP? What was completed, what was descoped, and why?

### 5. Project Retrospective (`retrospective.md`, 2–3 paragraphs)
- What you're most proud of technically and why.
- The biggest challenge and how you navigated it.
- What you'd do differently with five more weeks.
- How the project made you a stronger developer/practitioner — connect back to the Week 1 Takeaway.

## Learning Outcomes
- Deliver a production-grade ML system.
- Communicate and defend technical work to a non-technical audience.
- Manage an independent project from proposal to delivery.

## Deliverables (GitHub, inside `deliverables/week5/`)
- `ui-screenshots/` — folder of UI screenshots.
- `how-to-use.md` — non-technical user guide.
- `retrospective.md` — project retrospective (section 5).
- Root `docs/` finalized in place: `README.md` (complete + professional), `implementation-plan.md` (final status note), `claude.md` (finalized), `ai-usage-log.md` (Week 5 entry + final retrospective).

## Rubric (40 pts)
| Criterion | Pts | What "Exceeds" needs |
|---|---|---|
| **Business-Facing UI** | 8 | Functional, connected to the live model endpoint, clearly for a non-technical user; data freshness surfaced; screenshots + walkthrough document the full UX. |
| **User Guide & README** | 8 | User guide for a non-technical audience (inputs, outputs, interpretation); README complete — architecture, setup, stack, links to all docs. |
| **AI Documentation — Final Entries** | 8 | All three finalized; `ai-usage-log.md` has a substantive, honest retrospective on how AI usage evolved + its impact; `implementation-plan.md` closes with an honest MVP assessment. |
| **Project Retrospective** | 8 | Specific and honest — names a genuine challenge, reflects on a real technical decision, connects to the Week 1 Takeaway. |
| **Repository Quality** | 8 | Clean and professional — meaningful commit history, no debug files or dead code, all branches merged, folder structure matches docs; a developer could clone and run it. |

## Our project notes (for prep)
- **UI = React + NiiVue** (not Streamlit). "Connected to the endpoint": the static-first UI reads precomputed predictions; document the `serve.py` FastAPI `/predict` endpoint as the deployed-model layer and explain the static-first design choice honestly.
- **Data freshness:** surface the "Precomputed cases" badge / last-updated framing already in the UI header.
- **Repository quality:** the `scripts/legacy/` cleanup is done; verify no stray debug files, the `outputs/` git-ignore holds, and the README grader-map + structure block are current.
- **MVP assessment (implementation-plan):** hit the Level 4.5 segmentation MVP (pancreas + lesion), CADe framing, React/NiiVue UI, scratch-vs-transfer comparison. Descoped/deferred to capstone: the autonomous localize→segment cascade number, Level 5 multi-structure, the specificity gate. Be honest about provided-ROI vs autonomous.
