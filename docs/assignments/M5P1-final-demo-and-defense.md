# M5P1: Final Demo & Defense

**Due:** Thursday 11:59pm (available until Jul 30 11:59pm) · **Points:** 40 · **Presentation date:** Wednesday (live) · **Submit:** full GitHub repo (clean, merged) + `audience-notes-week5.md`

## Overview
The final presentation is a **live demonstration of a working, end-to-end ML system**. Present to a mixed audience — treat the room as if it includes both a technical evaluator and a business decision-maker. Demo the product, walk through the system, and defend every layer. Peers serve as the business review panel for the last time.

## Presenter — 12-minute presentation (structure)
1. **The problem & business value (2 min)** — Remind the audience what was built and for whom. What decision does the system support? What would the business user do differently because of it?
2. **Live demo (3 min)** — Run the UI end-to-end. Show real data flowing through the system to a prediction. If live data is unavailable, use the most recent cached dataset and explain why.
3. **System walkthrough (3 min)** — Walk through the architecture: data pipeline, model, deployment, front-end. Reference the README diagram. Highlight one technical decision you're proud of.
4. **Model performance & limitations (2 min)** — Present final metrics in business terms. Be honest about what the model does *not* do well and what that means for the user.
5. **Reflection (2 min)** — Biggest takeaway from the project. How did AI-tool usage shape the work? Connect back to the Week 1 Takeaway.

**Then 8 minutes of Q&A.** Expect deep questions on any layer — business logic, data decisions, model choices, pipeline design, UI.

## Audience (final peer review)
`audience-notes-week5.md` — for each presentation address:
- Whether the system demonstrates genuine end-to-end integration or feels stitched together.
- Whether the business value is clearly communicated and credible.
- One specific question you'd ask **as a hiring manager** evaluating this student's work.

## Learning Outcomes
- Deliver a production-grade ML system.
- Architect and automate a resilient data and training pipeline.
- Apply experiment tracking, hyperparameter tuning, and evaluation.
- Communicate and defend technical work to a non-technical audience.
- Manage an independent project from proposal to delivery.

## Deliverables
- **Presenter:** full GitHub repository — clean, merged, submitted; all documentation files finalized.
- **Audience:** `audience-notes-week5.md` submitted.

## Rubric (40 pts)
| Criterion | Pts | What "Exceeds" needs |
|---|---|---|
| **Live Demo & System Integration** (Presenter) | 10 | Demo runs end-to-end without error; real/recent data flows to a visible prediction; audience sees all layers (pipeline, model, UI) working as one coherent system. |
| **Business Value Communication** (Presenter) | 8 | Business problem, target user, and value communicated compellingly; a non-technical audience member could explain what the tool does and why it matters. |
| **Technical Depth & Ownership** (Presenter) | 10 | Speaks fluently to every layer — data, model, pipeline, deployment, UI — with specific detail; technical decisions explained with trade-offs acknowledged. |
| **Q&A Confidence & Honesty** (Presenter) | 4 | Handles all questions directly; acknowledges limitations/unknowns without deflecting; equal composure on technical and business questions. |
| **Question Quality** (Audience) | 4 | Substantive, specific questions probing integration, business credibility, model limitations, or what the student would do differently; ≥1 hiring-manager-framed. |
| **Audience Notes Quality** (Audience) | 4 | Notes include summary, questions asked, assessment of integration + business value, and a specific hiring-manager-framed question. Analytical and specific throughout. |

## Our project notes (for prep)
- **Demo = static-first React + NiiVue** reading precomputed cases (no live backend). This is a deliberate design (justify it: the pipeline pre-computes predictions → the UI reads saved NIfTI + `results.json`), not a limitation. Have the FastAPI `/health` + `/predict` endpoint ready as the "deployed model" layer if asked.
- **Technical decision to feature:** the whole-box ROI breakthrough, or the data-scale lever, or the honest leakage-catch-and-fix. Pick one with a clean trade-off story.
- **Metrics in business terms:** detection sensitivity 96% (catch rate = the CADe headline), lesion Dice 0.474 (edit burden, near the ~0.53 JHU benchmark), specificity 17% (false-alarm rate = the honest weakness). Provided-ROI caveat; autonomous number = capstone.
- **Honesty is graded** (Q&A + limitations). Lead with the over-segmentation of small tumors and the provided-ROI caveat.
