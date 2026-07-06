# M2P2 Presentation Outline - Data Understanding and Revised Plan

Target: 12 minutes presenting, then 10 minutes of Q&A. Audience is my class, briefed as if they are a business stakeholder deciding whether to fund the next stage. The whole talk has to show that my EDA findings actually drive my modeling decisions, because that is what the rubric grades and what people will challenge me on.

The spine of the talk is three findings, each one paired with the decision it forced. If someone asks "why did you do X," the answer is always "because the data showed Y."

---

## 1. Opening and framing (about 1.5 min)

- What this is: a tool that outlines the pancreas and flags where a tumor might be, so a radiologist or annotator can accept, edit, or reject the outline. It is a segmentation assist, not a diagnosis. I say this out loud early because it sets the honest scope.
- The data in one line: 9,901 abdominal CT scans from Johns Hopkins PanTS, each with voxel-level pancreas and tumor masks, gathered across 20 sites and 6 scanner makers.
- Where I am: the full pipeline is built and has passed its sanity gate, and I have my first honest evaluation, which is where the interesting story is.

## 2. What the data looks like, quality issues found and resolved (about 2 min)

- Source and ingestion: one-time bulk download to an external drive, reproducible through two scripts. I address Airflow head on: the data is static, so a scheduled ingestion DAG would be infrastructure for an event that never happens; my scripts give the same reproducibility.
- Quality: the imaging is essentially 100 percent usable, no duplicates, every case has its masks. The metadata is messy (about half of age and sex missing, a stray "M " with a trailing space), and I do not use it as a model input, so it does not affect training.
- The trust check: my tumor label agrees with the dataset's own tumor flag 99.6 percent of the time, and I flag the 44 disagreements rather than trusting the spreadsheet blindly.

## 3. The three findings that drive the model (about 5 min, the core)

Finding 1: severe class imbalance. Only 10 percent of scans have a tumor, and the lesion is a tiny fraction of a scan. Decision it forced: bias patch sampling toward tumor voxels and use a Dice-based loss instead of plain cross-entropy, and score lesion accuracy only on tumor cases while measuring specificity separately on healthy ones.

Finding 2: extreme geometry heterogeneity. Slice counts run from 8 to over 1,000 and voxel spacing varies by more than tenfold. Decision it forced: reorient every scan and resample to a common 1.5 millimeter grid, then window CT intensity, before the model sees anything. Without this the model would be comparing apples to oranges.

Finding 3: the model over-predicts (this is the honest, interesting one). My first real evaluation: pancreas Dice 0.72, lesion Dice 0.17 on tumor cases, but specificity only 8 percent, and post-processing did not fix it. Decision it forced: the whole Week 3 and 4 plan is now a sensitivity-specificity strategy (balanced retraining, a probability-threshold sweep, and constraining lesions to lie inside the predicted pancreas), not just more cleanup. I show the overfit curve here as proof the pipeline learns, so the over-prediction is a tuning problem, not a broken pipeline.

## 4. What changed from my Week 1 framing (about 1.5 min)

- The dataset is the Mini release (9,901 cases), not the full set, so full-scale training is a capstone follow-on.
- No patient IDs, so each scan is its own patient, which is actually the safe choice for splitting.
- The big shift: fixing how I measure mattered as much as fixing the model. Lesion Dice reading zero was a measurement artifact, and correcting that is what revealed the real over-prediction problem.

## 5. Finalized requirements and schedule (about 1.5 min)

- Walk the seven measurable Core Requirements (R1 done through R7 target), pointing out which are done and which are targeted, with the lesion Dice target of 0.35 to 0.50 and a defensible specificity number by Week 4.
- The schedule with the one line that shows I know what behind looks like: if lesion specificity is still weak by Week 4, I deliver a strong pancreas result plus a documented analysis of why lesion detection is hard, which is still a complete and honest project.

## Likely Q&A and my answers

- "Why not Airflow?" Static dataset, covered above; scripts give the same reproducibility, and Airflow is the capstone answer if ingestion ever becomes continuous.
- "Your specificity is 8 percent, is the project failing?" No. The model clearly finds tumors and the pipeline provably learns; 8 percent specificity is an over-prediction I have a concrete, ordered plan to fix, starting with balanced retraining and an anatomical constraint.
- "Why did cleanup make lesion Dice worse?" Because the false positives are large connected regions, not specks, so largest-component and volume thresholds cannot help and can clip real lesion pieces. That is exactly why the fix has to be in training, not post-processing.
- "Is 100 dev cases enough?" It is enough to prove the method and tune the balance; more data is the real lever for both sensitivity and specificity, and that is the capstone's job. I am honest that the subset is a limitation.
- "How do you prevent patient leakage across splits?" Each scan is its own patient here, and I split at the patient level, so leakage is structurally impossible.
