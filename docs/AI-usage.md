# AI Usage Log

**Living document — append a new section each week.** A weekly, honest summary of human–AI interaction: what AI assisted with, prompts/context that worked, and where output needed correction. Do not edit past entries.

Format for each week:

```
## Week X — [Date range]
**Tasks AI assisted with:** ...
**Prompts / context that worked well:** ...
**Where AI output needed correction:** ...
```

---

## Week 1 — Jun 29 – Jul 5

> _Status: in progress. This week's formal retrospective is finalized as the last step before Sunday submission. Notes below are accumulating during the week._

**Tasks AI assisted with:**
- Verified the PanTS dataset facts (license, scale, real-time status, access method) before writing the proposal.
- Pressure-tested the project idea against the assignment rubric and identified the missing "business user" framing.
- Drafted the proposal, 5-week schedule, and project documentation structure.

**Prompts / context that worked well:**
- Giving Claude the full assignment rubrics as repo files first, then the project idea — so its drafts mapped directly onto how the work is graded.
- Asking it to flag *gaps* (named business user, real-time confirmation) rather than just write the document.

**Where AI output needed correction:**
- _(To fill in as the week progresses — e.g. any dataset detail or framing I adjusted.)_

**Architecture planning session (Jun 30):**
- Used AI to brainstorm the full technical plan — the segmentation→detection→classification→diagnosis ladder, how to handle 3D CT volumes, and the model choice.
- AI web-verified that PanTS ships downloadable trained checkpoints (MedFormer, R-Super) and surfaced the leaderboard numbers (tumor Dice ~0.53, sensitivity ~80%), which set realistic targets — this corrected my initial assumption that I'd have to train everything from scratch.
- Prompt that worked: asking specifically "transfer learning vs from scratch — what pretrained models actually exist for this exact task right now?" pushed it to verify current resources instead of answering from memory.

---

<!-- Add Week 2, 3, 4, 5 sections below as the project progresses. -->
