# M2P2 Run Sheet (12 min talk + 10 min Q&A)

Quick reference to glance at while presenting. The spine is three data findings, each paired with the decision it forced. Rubric rewards: findings clearly communicated (6), feature/justification (5), revised plan credible (6), Q&A depth (5).

## Deliverables checklist (submit via GitHub before Sunday 11:59pm)

- [ ] `week2/data-understanding-report.md` — DONE. Optional: add a 3-line "Update since drafting" note that the first plan lever (whole-box) already lifted specificity to 55%. Keeps the report consistent with what you say out loud.
- [ ] `week2/eda-notebook.ipynb` — DONE. Make sure it is saved with outputs/charts rendered.
- [ ] `docs/audience-notes-week2.md` — AUDIENCE deliverable. Fill in during and after peers' talks: for each, a summary, the questions asked, and your assessment of whether their EDA justifies their model plan. Do not forget this one, it is graded (4 pts).
- [ ] Commit + push everything to GitHub (report, notebook, audience notes). This is how it is turned in.
- [ ] Have the notebook open and pre-run, plus `week2/diagrams/` ready in a second window for reserve visuals.

## Consistency note (read once)

Report/notebook say specificity 8% then 42% via the constraint. Live you will say the whole-box fix took it to 55%. Handle it by framing whole-box as "since I wrote the report, my first planned lever already worked." Do not contradict the report, extend it.

## Timed outline (12 minutes)

**0:00–1:30 · Open and frame (1.5 min).** No visual, or title slide.
Say: a tool that outlines the pancreas and flags where a tumor might be, so a radiologist can accept, edit, or reject. Segmentation assist, not diagnosis. Data in one line: 9,901 JHU PanTS abdominal CT scans, voxel-level pancreas and tumor masks, many institutions, four scanner makers (Siemens, GE, Philips, Toshiba). Where I am: full pipeline built, sanity gate passed, first honest evaluation done.

**1:30–3:30 · What the data looks like + quality (2 min).** Point to: notebook overview cell, then `diagrams/data-pipeline.svg`, then the label-validation cross-tab (Viz 5).
Say: one-time reproducible bulk download (two scripts, so no Airflow needed for a static dataset). Imaging essentially 100% usable, no duplicates, every case has masks. Metadata messy (half of age/sex missing) but never fed to the model. Trust check: my tumor label agrees with the dataset's own flag 99.6% of the time, and I flag the 44 disagreements instead of trusting the spreadsheet.

**3:30–8:30 · The three findings (5 min, the core).**
- Finding 1, class imbalance. Point to: Viz 1 (tumor prevalence ~10%) and Viz 2 (lesion volume, 5 orders of magnitude). Decision: tumor-biased patch sampling, Dice-based loss not accuracy, score lesion Dice only on tumor cases and specificity separately on healthy ones.
- Finding 2, geometry heterogeneity. Point to: Viz 3 (slice count 8 to 1000+, spacing varies 10x). Decision: reorient to RAS, resample to a common 1.5mm grid, window HU, before the model sees anything. Tie back to `data-pipeline.svg` preprocess box.
- Finding 3, the model over-predicts (the interesting one). Point to: `overfit_curve.png` as the sanity gate. Say: first eval was pancreas 0.72, lesion 0.17, but specificity only 8%. Size cleanup did nothing (false positives are large regions, not specks); the geometric constraint lifted it to 42%; a probability threshold barely moved it. THEN the payoff: "the first structural lever in my plan was to give the model the whole pancreas in view instead of random slabs. I ran it this week and it lifted specificity to 55% on its own, pushed lesion Dice to 0.263, my best yet, and pancreas to 0.807, and it made the constraint almost unnecessary." Reserve `diagrams/dice-explained.svg` and `constraint-before-after.svg` for Q&A.

**8:30–10:00 · What changed from Week 1 (1.5 min).** Optional visual: `diagrams/benchmark-comparison.svg`.
Say: it is the Mini release (9,901), so full-scale training is the capstone. No patient IDs, so each scan is its own patient, which is the safe split. Biggest shift: fixing how I measure mattered as much as fixing the model, lesion Dice reading zero was a measurement artifact, and correcting it revealed the real over-prediction. Show benchmark: pancreas Dice 0.807 is on par with published nnU-Net (0.79 to 0.85); lesion Dice and specificity are on trajectory; the gap is data scale.

**10:00–11:30 · Finalized requirements + schedule (1.5 min).** Point to: the Core Requirements table in `docs/implementation-plan.md`.
Say: walk R1 (done) through R7 (target), lesion Dice target 0.35 to 0.50, a defensible specificity by Week 4. The behind-looks-like line: if lesion specificity is still weak by Week 4, I deliver a strong pancreas result plus a documented analysis of why lesion detection is hard, which is still a complete, honest project.

**11:30–12:00 · Close (0.5 min).** Say: "Every finding is paired with a concrete decision in the pipeline. The data told me what to build, and I built it, and the first upgrade in the plan is already paying off."

## Which visuals to actually show vs hold in reserve

Show (they carry the story): EDA Viz 1, 2, 3; `overfit_curve.png`; `benchmark-comparison.svg`.
Reserve for Q&A (do not spend time unless asked): `data-pipeline.svg` (only if they ask about processing), `dice-explained.svg` (if asked what Dice is), `constraint-before-after.svg` (if asked about post-processing), `segresnet-ushape.svg` (if asked to go deep on the model), `what-model-sees.svg` (if asked about field of view).

## Q&A cheat lines

- "8% then 55%, which is it?" Diagnosis was 8%; the first structural fix in my plan, whole-box, took it to 55%. Honest caveats: this is with a radiologist-provided ROI (oracle), on 20 eval cases, and several things changed together, so I call it evidence that whole-box at a feasible resolution works, not proof one knob did it.
- "How does this compare to state of the art?" Point to benchmark diagram. Pancreas Dice on par with published (0.79 to 0.85); lesion Dice about half of segmentation SOTA (0.40 to 0.53), expected at 95 training cases; detection models hit ~90% sensitivity and ~93% specificity but are fully automated on thousands of scans, so it is not head-to-head. The gap is data scale.
- "Isn't post-processing gaming the score?" No, it lowers lesion Dice while raising specificity, rules are fixed and never see the answer, and I always report raw next to cleaned.
- "Why not Airflow?" Static dataset, scripts give the same reproducibility; Airflow is the capstone answer if ingestion becomes continuous.
- "Is 100 dev cases enough?" Enough to prove the method and tune the balance; more data is the real lever, and that is the capstone. I am honest the subset is a limitation.
- "Patient leakage?" Each scan is its own patient, split at the patient level, so leakage is structurally impossible.
