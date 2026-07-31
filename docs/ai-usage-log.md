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

### Week 4 continued — the anatomy experiment, hyperparameter tuning, and the deployment build (M4A1)

Tasks I used AI assistance for (pipeline and deployment heavy, which is where I leaned on it most):

- A full anatomy-aware experiment (EXP-26): a 5-class model that also learns pancreas head/body/tail as an auxiliary task. I ran this through a strict documentation-first loop — the AI wrote a spec sheet, a second AI (Codex) adversarially reviewed the *idea* across four rounds until it was approved, then it wrote the code, and Codex reviewed the *code* in two more rounds before I ran anything. That process is the point of this entry: for a full-day training run I do not trust a single AI pass. The AI also hardened the whole training path for multi-day runs — atomic checkpoint saves, a deterministic step-indexed data pipeline so a paused-and-resumed run reproduces the exact same trajectory, a recipe-identity guard on resume, and a graceful Ctrl-C. The honest outcome: at an intermediate 12k-step checkpoint the anatomy model looked like a win (+0.041 lesion Dice, confidence interval excluding zero), but I did not report that; I trained both arms to convergence, and at 24k it was a null with a small pancreas regression, so I rejected it. Pre-registering the bar and training to convergence caught what would have been a false positive.
- The formal hyperparameter search (`scripts/tune_optuna.py`): a Bayesian (Optuna TPE) search over learning rate, focal gamma, the loss weights, and weight decay, using short proxy trials so it could evaluate many configurations overnight, with median pruning, a resumable SQLite study, and every trial logged to MLflow. The AI wrote it, Codex reviewed it, and I ran it. It confirmed my learning rate was already near-optimal (anything above ~2e-4 collapses the tiny lesion) and surfaced a mild signal that higher focal gamma helps.
- The deployment build for M4A1: a single-entry inference wrapper (`src/inference/predict.py`), a minimal FastAPI endpoint (`scripts/serve.py`), MLflow model registration (`scripts/register_model.py`), and a provenance-checked test-cohort builder (`scripts/make_test_cohorts.py`). Same loop: I had the AI write a code *plan*, Codex passed off the plan with required changes, the AI wrote the code, and Codex reviewed the code across three rounds.

Prompts and workflows that worked well:

- The documentation-first, two-AI review loop — write the plan, have an independent AI review the *idea*, then write the code, then have it review the *code* — was the single most valuable workflow this week. It caught real defects before they cost a training run or shipped a broken endpoint.
- Pre-registering the accept/reject bar in the spec before training, and training to convergence instead of stopping at a flattering intermediate. That discipline is what turned EXP-26 from an over-claim into an honest null.

Cases where AI output needed correction or specific instruction:

- On the anatomy loss, the AI claimed its implementation matched the standard MONAI DiceFocal loss. It did not — MONAI applies softmax only to the Dice term, so the claim would have double-counted softmax. I had it drop the equivalence claim and describe the loss honestly as a deliberate reformulation. The check I kept: do not let the code assert a mathematical equivalence it has not verified.
- The deployment code took three rounds of code review to get right, and the AI's first passes had genuine bugs: the registration script said it logged the config but did not; a quick data subset would overwrite the canonical cohort filenames; limit arguments were not validated as positive integers; the tests validated a hand-built dictionary instead of the real function; the MLflow 3.x model format needed an explicit serialization mode; the recipe check treated missing metadata keys as mismatches; and a cohort membership check was tautological. I required a regression test for each fix and made the test harness exit nonzero on failure so it cannot report a false pass. The lesson I am recording: even well-structured AI code needs an independent code review plus tests that exercise the exact production conditions, not just the happy path.

Honest status heading into Week 5:

- Complete: the model itself (leakage-free lesion Dice 0.415, detection 95%), the full experiment record including the honestly-rejected anatomy experiment, the Optuna tuning study, and the M4A1 deployment code (inference API, FastAPI endpoint, MLflow registration, test-cohort builder) — Codex-approved with 21 passing tests.
- (Week 4 status as of Sunday submission is recorded below; the Week 5 entry and the final project retrospective follow it.)
- Done as of Sunday submission: the one-time held-out test-set evaluation is complete (official 901-case test: lesion Dice 0.474 [95% CI 0.42–0.52], pancreas 0.827, detection 96%, specificity 17%), the final model is registered in MLflow as `pancreas-lesion-segmenter` v1 with the tuning-run and registered-model screenshots captured, the pipeline diagram and the by-size/phase and sample-prediction figures are in `deliverables/week4/img/`, the FastAPI endpoint is live smoke-tested (health page + `/predict`), and the report plus these AI-documentation files are written. As a bonus, the pre-registered specificity experiment (EXP-25, more healthy data) ran and was honestly rejected — it cleared specificity 17%→46% but missed the ≥90% detection floor (88%), so the plain whole-box model stays the headline. Nothing on M4A1 is outstanding; the remaining risk is entirely Week 5 (the React + NiiVue UI), not this deliverable.

---

## Week 5 — Jul 27 onward (the interface, the demo, and the final package)

**Tasks assisted.** Week 5 split cleanly into two tracks and I ran a different AI on each, which is the
first time I deliberately assigned tools by strength. Codex drove the React and NiiVue interface,
because I had built up enough context in that conversation that it could make multi-file front-end
changes reliably, and because its frontier model is stronger at UI work than what I had available in
the other session. Claude drove the deliverables: repository cleanup, the README, the user guide, the
UI walkthrough, the project retrospective, and the presentation prep. Running both at once is the only
reason a five-day week with a presentation in the middle of it was survivable.

**Specific things AI did well this week.** The interface work was the standout. Codex built the live
inference path end to end, adding CORS and a `/cases` route to the FastAPI service, a scan picker, an
"Analyze scan" flow with a live-scored timestamp badge, and a graceful fallback to cached results when
the endpoint is offline, which is exactly the behavior I want for a demo I cannot afford to have hang.
On the other side, Claude caught a bug in that same work that I would not have caught until the demo
embarrassed me: the server was re-cropping and re-resampling scans that had already been preprocessed
into the model's exact input format, so it was double-processing them and would have quietly served
wrong predictions. That is the same class of train-and-serve mismatch that bit me in Week 2, and the
fix was to feed the prepared cube straight through. Claude also fixed the 3D viewer, which was loading
the label volume instead of the exported surface meshes, so the marching-cubes pancreas and lesion my
instructor specifically liked were never actually being rendered.

**Where AI output needed correction.** Twice, and both were the same failure mode: an AI assuming the
shape of data it had not actually inspected. Codex assumed the demo folder held raw CT scans when it
held finished model inputs. Earlier in the week an AI summary of my metrics conflated "we ran the model
on all 901 test cases" with "every metric is computed over all 901 cases," which are different claims,
and I pushed back until it separated them precisely, because that distinction is exactly what a grader
would probe. The check I kept applying all week is the one that has served me best: make the AI verify
against the actual files in the repository before it asserts anything, and treat any claim it makes
about my own data as unverified until it shows me the command output.

**Honest status heading into the final submission.** Complete: the model, the full experiment record,
the deployment endpoint, the live-scoring UI, the Week 5 written deliverables, and the repository
cleanup. Remaining: UI screenshots, the final presentation rehearsal, and the last commit.

---

## Final retrospective — how I used AI across the whole project

My use of AI changed shape three times over five weeks, and the change was the point.

**It started as a research and planning partner.** In Week 1 I used ChatGPT's deep research mode to
pressure-test my model choice before I wrote any code, and it independently agreed with fine-tuning
SuPreM's SegResNet, which mattered because I was making a locked-in architectural decision with no way
to cheaply reverse it later. That set the pattern of using AI to *stress-test a decision before
committing*, not to make the decision for me. In Weeks 2 and 3 the dominant use was as an explainer.
I was moving from 2D CNNs into 3D medical imaging, and being able to ask what a voxel actually is, how
Dice is computed, why a class occupying 0.04 percent of a volume breaks a normal loss, and to get an
answer at exactly my level, compressed weeks of reading into days. The learning use was probably the
highest-leverage thing AI did for me on this project, and it is the least visible in the repository.

**Then it became a code generator that I stopped trusting.** The turning point was Week 3, when an
adversarial AI audit of my repository found that my data-scaling script sampled from the wrong column
and had been leaking validation cases into training, which meant my headline number was inflated. AI
found the bug, but AI had also written the bug. Both of those facts are true and I have tried to hold
them together honestly. From that point I stopped treating generated code as done when it ran, and
built the loop I used for everything afterward: write a spec, have a second AI review the plan
adversarially, revise until it is approved, write the code, have it reviewed again, then require a
regression test for every issue found. The deployment code in Week 4 went through three review rounds
and the reviews caught genuine production bugs, a registration step that claimed to log config but did
not, a data subset that would have overwritten my canonical cohort files, and a test that validated a
hand-built dictionary instead of the real function. None of those would have survived to production,
but all of them would have cost me hours to find alone.

**Finally it became two specialists running in parallel.** By Week 5 I was assigning work by tool
strength, Codex on the interface, Claude on analysis and documentation, and having each one check the
other's output. That is where I found the most value per hour, and it is also where the failure mode
became clearest: AI is confident about data it has not inspected. Every real error I hit, the double
processing, the wrong-column split, the conflated metric claim, was an assumption about the shape of my
data rather than a coding mistake. So the habit I am taking forward is verification-first: make it read
the file, run the command, and show me the output before it tells me what is true.

**Net effect on quality and speed.** Speed, unambiguously: I do not think a solo five-week project
covering a 3D training pipeline, twenty-six documented experiments, hyperparameter search, model
registration, a serving endpoint, and a clinical review interface is achievable in that window without
it. Quality is more interesting. AI made my code faster to write and my documentation far better, but
the two things I am proudest of, the whole-box idea that fixed over-prediction and the decision to
train an experiment to convergence rather than report a flattering intermediate, were both mine, and in
the second case I was arguing against a result an AI had helped me produce. The most useful thing AI
did for my quality was not writing code, it was being a reviewer harsh enough to find my leakage bug
before an outside evaluator did. I would rather work with a tool that tells me my number is wrong than
one that helps me publish it.
