# M1A1: Project Proposal

> **Due:** Sunday by 11:59pm · **Points:** 25 · **Submit:** website URL or file upload · **Available until:** Jul 12 at 11:59pm

## Overview

Before a single line of code is written, you must define what you are building, why it matters, and how you plan to execute it. This proposal is your contract with your supervisor (and your team) — it scopes your project and unlocks your ability to proceed.

## Instructions

Work individually or as a pair. If working as a pair, the proposal must explicitly justify the scope and complexity that warrants two contributors.

Your proposal is a professional document — not a form fill. Use the sections below as a guide, but format and present it as something you would be proud to show an employer or client.

1. **What?** Write a short paragraph describing your project for a non-technical reader who is unfamiliar with your topic. What is the problem? Who experiences it? What will your system do about it? Close with a one-sentence description of the ML approach and the business-facing output.
2. **Why?** Write a short paragraph explaining why you chose this project. What makes you curious or excited about it? If you are working as a pair, both partners should contribute a voice to this section.
3. **Your Takeaway.** In a short paragraph, explain what you hope to gain from this project that will make you a stronger developer or data practitioner. Be specific — name a skill, a gap you want to close, or a capability you want to prove to yourself.
4. **Tech Stack.** Provide an annotated list of every technology you plan to use — from data source to database to model framework to deployment to user interface. For each item, note whether it is familiar or new to you. If it is new, briefly state how you plan to get up to speed.
5. **Proposed Schedule.** Map your core requirements onto a 5-week plan. Weeks 1–2 cover project setup and data validation, so your schedule should show meaningful technical milestones from Week 2 onward. For each week, state what you plan to complete and what a "behind schedule" signal would look like.
6. **Claude & AI Usage Plan.** How do you intend to use Claude or other AI tools during this project? What tasks will be AI-assisted (e.g. code generation, debugging, documentation) versus handled manually? This is not graded for correctness — it establishes your intent and will be updated each week as a living record of your actual AI usage. (You are not expected to have your implementation plan at this stage, but you will turn in agent files that you are using to give Claude context around its role in the project along with clear guidelines.)
7. **Scope justification (pairs only).** If working as a pair, clearly describe how the scope, complexity, or breadth of the project requires two contributors. Identify how work will be divided.

## Learning Outcomes

- Manage an independent project from proposal to delivery.

## Deliverables

Submit via GitHub (branch → merge to main with documentation folder):

- **`proposal.md`** — written responses to all 7 sections above.
- **`schedule.md`** — 5-week plan with high-level core requirements.
- **`Claude.md`** — your Claude / AI usage plan in its own file (can mirror section 6 of the proposal initially; this file will be updated each week).
- **`AI-usage.md`** — weekly summary of human-AI interactions:
  - What tasks you used AI assistance for.
  - Specific prompts or context definitions that worked well.
  - Any cases where AI output needed correction or specific instructions.

## Rubric (25 pts)

| Criterion | Description | Pts |
|-----------|-------------|-----|
| Problem & business framing | Problem is specific, business user is named, and the decision or action the ML system supports is clear. | 4 |
| Dataset validity | Dataset is open-source, confirmed whether real-time (daily/weekly), source URL provided, access method described. | 5 |
| ML approach & pipeline plan | ML problem type is correctly identified, approach or model family is justified, and end-to-end data flow is described. | 6 |
| Business-facing layer | Front-end is described in terms of what the business user will see and do. | 4 |
| Agent plan | `agent-plan.md` clearly distinguishes AI-assisted tasks from manual tasks with specific, realistic examples. | 6 |

Each criterion is scored: Exceeds (full) · Mastery (0.75) · Near (0.5) · Below (0.25) · No Evidence (0).
