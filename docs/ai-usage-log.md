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

Later in the week (Jul 7 to Jul 10) I ran a nightly experiment loop, and the AI usage shifted from writing code to running a disciplined scientific process:

- Reframing every training run as a formal experiment with a hypothesis, a single variable, and an accept-or-reject bar, kept in a running experiments log. Each morning I pasted the raw evaluation output and had the AI help me decide accept or reject against the prior baseline, not just describe the numbers.
- Catching a bug in my own evaluation script that would have wasted the whole week. A clarity run looked completely broken (pancreas Dice fell from 0.72 to 0.22). Rather than accept that, the AI and I traced it to the eval script accepting a crop flag but never applying it, so it was scoring the whole body against a model trained only on small crops. The tell was that a resolution change cannot move pancreas that far. We fixed it and re-ran.
- Building my own idea into the pipeline: feeding the entire pancreas box to the model as one cube instead of random sub-patches. The AI wrote the transform and the CLI wiring, and I had it explain the resolution-versus-coverage tradeoff so I picked the cube size and spacing deliberately.
- Using a second AI (Codex) as an independent reviewer before committing an overnight run. It ran a code audit that found a real train/eval mismatch bug plus two more fixes, then a design review that approved the plan and told me to validate on 20 cases instead of 12. I treated the two AIs as a check on each other rather than trusting either blindly.
- Verifying a utility before letting it touch real files. When I needed to re-log a run into MLflow (the overnight run never logged because I launched it from the wrong virtualenv), the AI wrote the logging script and tested it against a throwaway database first, so my real tracking database was only touched once the script was proven.

What this week reinforced: the AI is most useful when I make it defend a number or a change, and when I keep a second reviewer in the loop. The biggest win, the whole-box result that beat my previous best on lesion Dice, pancreas Dice, and specificity at once, came from my own idea, with the AI as the implementer and skeptic, not the author.

## Week 3 — Jul 13 – Jul 19

Tasks I used AI assistance for:

- A full read-through audit of the pipeline code (config, transforms, dataset, model plus the SuPreM loader, losses, metrics, trainer, sliding-window, post-processing, and the train and evaluate scripts). I had the AI confirm that the bugs I fixed earlier are actually closed in the code (the train/eval preprocessing mismatch, the encoder that was not training after the warm-up freeze, and the resume shape mismatch), and surface anything imprecise. It flagged three things: the disk cache the data-scale plan needs is not implemented yet, a few config keys that the code does not read, and a loss default that did not match my locked setting.
- Cleaning up those imprecisions so the config reflects what the code really does: annotating the not-yet-wired keys (`training.cache`, `validation.interval_epochs`, `validation.patience`) and flipping the `build_loss` default for `include_background` to False to match the bg0 base I locked in EXP-07. These are documentation and safety changes, not behavior changes, since my config already sets those values explicitly.
- Wiring test-time augmentation into the evaluation path (8-view flip averaging of the softmax probabilities, `evaluate.py --tta`). The AI wrote the helper and I had it keep the non-TTA path untouched so my existing numbers stay reproducible.
- Designing the week's two experiments as single-variable tests with accept/reject bars written before I run them: EXP-09 (transfer versus from-scratch on the whole-box recipe, to defend the SuPreM choice at my check-in) and EXP-15 (the TTA lever). I had it state the confounds honestly up front, including that the transfer and scratch arms also differ in learning rate and encoder freeze, and that the EXP-12 checkpoint the TTA test needs may have been overwritten by my clarity and contrast runs.
- Building the data scale-up once the recipe nulls pointed at data as the lever: the AI wrote the disk-cache (PersistentDataset) branch and a script to build tumor-enriched splits, and pre-registered the two scaling runs, EXP-17 (300 cases) and EXP-17c (all 1,412 cases), with accept bars set before the runs. It flagged honestly that EXP-17c changes two things at once, data volume and training length, so it is a decisive practical result rather than a clean single-variable decomposition, and I kept that caveat in both the experiments log and the report.
- A metrics audit before committing to long runs, done as my own pass plus an independent AI session (recorded in `docs/codex-metrics-audit.md`). It confirmed the Dice and specificity arithmetic and the absence of train-validation leakage, and found one real issue, that my region-of-interest crop is built from the pancreas union the lesion, so lesion extent can leak into the field of view and my lesion Dice is an upper bound. I had the fix coded behind a flag with the default left unchanged for comparability, and pre-registered EXP-19 to quantify the leak.
- Finalizing the Friday deliverables: folding the new max-data model into the experimentation report as the selected model with an honest plan-status section, cross-checking that every number in the report matched my slide deck, and updating the repository readme into a clickable grader map for the Week 3 submission. I made the accept/reject and framing calls; the AI drafted and cross-checked.

Prompts and context that worked well:

- Having the AI read the experiments log, the schedule, and the implementation plan together before proposing anything, so the week's work lines up with what I already committed to and does not re-litigate settled decisions.
- Making it separate what I own (running the training and eval, all git, the presentation and the accept/reject calls) from what it owns (experiment design with pre-registered bars, code, honest interpretation, and keeping the living docs current). We recorded that split in the implementation plan.

Cases where AI output needed correction or specific instruction:

- I had it deliberately defer the disk-cache build even though it is the biggest lever, because it is the heaviest code and the longest runs and it is not what Friday's check-in needs. The AI initially treated data scale-up as the default next step; I redirected the week toward the cheaper, presentation-relevant runs first.
- I had it rewrite the EXP-09 design from the old patch-96 recipe to the current whole-box recipe, so the transfer-versus-scratch comparison is against the model I actually present, not a superseded baseline.
- When I found my best checkpoint (EXP-12) had been overwritten by later runs, I used a second Claude session with more run history to confirm the file was genuinely gone, then had this session fix the root cause in code rather than trust myself to remember a manual backup. It added a per-run checkpoint archive with a self-documenting run_info file, a persistent run ledger, and a loud warning when MLflow is not logging. I verified the archive and ledger logic in a sandbox before trusting it. The lesson I am recording: when a manual step fails once and costs a model, make the code enforce it instead of promising to be more careful.
- When I first asked it to fold the big result into the report, the AI wrote that the MLflow comparison screenshots were already exported. They were not, and that is my task to produce, so I had it correct the claim to say the comparison is shown live and not overstate work that was not done. The check I am keeping: the report should only assert artifacts that actually exist in the repo.
- The most important correction of the whole project: the AI wrote `make_scaled_split.py` (my data-scaling split builder), and it sampled the training pool from the manifest's `split` column — which turned out to mark the source folder, not my carved training fold. That silently leaked ~266 validation cases into training and inflated my headline numbers. Neither I nor the AI caught it at the time. I then had a SECOND, independent AI session run an adversarial audit of the whole repo (`docs/codex-audit-week4.md`), which found it; I verified the leak myself by set-intersecting the split files before trusting the finding, then had the first AI fix the root cause and add a startup assertion so it cannot recur. The lesson I am recording, and it is a big one: AI-written code can carry a subtle, high-impact bug that reads as correct, so an independent adversarial review and my own verification of any critical claim are not optional — the audit was worth more than any accuracy point this week.
- The audit also corrected two overstatements the AI (and I) had let stand: that the pipeline was "leak-free by construction" (the localizer is actually a 3-class model that sees lesion supervision — no oracle at inference, but the framing was wrong), and that editing a YAML `source_masks` key would fix the pancreas mask loading (no runtime code reads that key). I had both corrected in the docs rather than left as aspirational claims.

## Week 4 — Jul 20 onward (kickoff, logged early because the weekend's work belongs here)

Tasks I used AI assistance for:

- Building the localize-then-segment cascade (`scripts/cascade_eval.py`) so the pipeline finds the pancreas on the full CT itself instead of being handed the ground-truth box, plus a millimeter-level containment audit and a per-case localizer diagnostic. The AI wrote the code and I ran it; I had it add a GT-quality gate after we found some pancreas labels were empty/corrupt in the source data.
- The full-system adversarial audit (above) and then the fixes it surfaced: the leakage fix, and wiring a Tversky loss (`train.py --loss tversky`) to attack the over-segmentation the clean model showed. I smoke-tested each before committing to an overnight run.

Cases where AI output needed correction or specific instruction:

- I kept the AI honest about the numbers after the leak: it had to withdraw the contaminated 0.528 headline and re-anchor everything on the clean, held-out 0.415, in the report and every living doc, rather than quietly keep the better-looking figure.
- I directed it to keep tonight's Tversky run single-variable (only the loss changes vs the clean baseline) rather than bundling the mask-resolver and resize-to-fit changes into the same run, so the result is actually interpretable.

<!-- Add later Week 4/5 detail below as the project progresses. -->
