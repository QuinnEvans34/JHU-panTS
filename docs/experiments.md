# Experiments Log

A running scientific record of every training run and change I have made, written so I can see what worked, what did not, and why. The rule I hold myself to: change one variable at a time, hold the rest constant, and decide the outcome against a bar I set before looking. A clean "this did not help" is a real result and is logged the same as a win.

Two kinds of numbers appear below, and they are not the same thing:
- Training-time validation (logged live to MLflow): measured during the run on whatever val cases the loop sampled. Useful as an in-loop signal but noisy and dependent on which cases were drawn.
- Full evaluation (from `scripts/evaluate.py`): the authoritative score, full-volume sliding-window inference on tumor-positive cases for Dice and tumor-free cases for specificity. When I quote a headline result it is this one.

A caution on the early runs: MLflow did not log the loss's `include_background` flag or the sampling ratio until 2026-07-07, so for runs 1 to 6 those settings are reconstructed from the code history and are marked as such. That gap is exactly why I added richer param logging.

---

## Run ledger (the six real training runs, from MLflow)

| # | MLflow id | date | mode | loss | iters | patch | headline |
|---|-----------|------|------|------|-------|-------|----------|
| 1 | 1f3c1242 | 07-03 | scratch, overfit 2 | dice_ce | 1200 | 96 | pancreas 0.02 to 0.888, lesion stuck 0 |
| 2 | f42bc200 | 07-03 | scratch, overfit 2 | dice_ce | 800 | 96 | pancreas to 0.792, lesion stuck 0 |
| 3 | d3198004 | 07-03 | scratch, overfit 2 | dice_ce | 800 | 96 | lesion learns, to 0.695 |
| 4 | 45e62189 | 07-03/04 | transfer | dice_ce | 6000 | 96 | train-val lesion read 0.000 (artifact) |
| 5 | e72cfdc8 | 07-04 | transfer | dice_focal | 6000 | 96 | "aggressive" model, over-predicts |
| 6 | 4979a5b7 | 07-06 | transfer | dice_focal | 6000 | 96 | "balanced" model, ~identical to 5 |

---

## EXP-01: Can the pipeline learn at all? (overfit gate)

Run: 1f3c1242 (scratch, 2 cases, dice_ce, 1200 iters, lr 2e-4, patch 96).

Purpose: a sanity gate, not a hypothesis. Before trusting anything, force the model to memorize a tiny fixed set. If it cannot drive loss down on 2 cases, the data, loss, or labels are wired wrong.

Result: training loss fell smoothly from 1.874 to 0.538 and pancreas Dice climbed from 0.02 to 0.888. Lesion Dice stayed flat at 0.000 the whole run.

Decision: gate PASSED for the pipeline overall (it clearly learns), but the lesion result exposed a problem to chase. Two causes turned out to be tangled together: the two overfit cases happened to be tumor-free (so lesion Dice was undefined and printed as 0), and the loss was letting the 0.04 percent lesion class be ignored. That sent me into EXP-02.

---

## EXP-02: Make the lesion learnable

Runs: f42bc200 then d3198004 (both scratch, 2 cases, dice_ce, 800 iters).

Hypothesis (H1): the lesion reads 0 because (a) I was overfitting tumor-free cases and (b) background dominates the loss. Drawing overfit cases from tumor-positive scans and excluding background from the loss will let the lesion be learned.

Variable: use `--positive` overfit cases and set `loss.include_background: false` (reconstructed from code history; not logged for this run).

Result: run f42bc200 still showed lesion 0 (pancreas 0.792), an intermediate step. Run d3198004, with the fix in place, showed lesion Dice climb to a max of 0.695 while pancreas reached 0.622.

Decision: ACCEPT. The model can fit both classes when it is actually shown tumors and the loss does not bury the lesion. Key learning that reshaped how I measure everything after this: a lesion Dice of 0 usually means "no tumor in these cases," not "model failed." Locked in `--positive` for overfit and `include_background: false` going forward.

---

## EXP-03: First full transfer run, and the validation measurement artifact

Run: 45e62189 (transfer from SuPreM, dice_ce, 6000 iters, lr 1e-4, patch 96, full 100-case dev subset).

Hypothesis (H1): a real fine-tuning run on the whole dev subset will produce a usable lesion segmenter, and transfer from SuPreM will give a strong starting point.

Result: training-time val lesion Dice read 0.000 the entire run (val pancreas 0.691), which looked like failure. It was not. The val set is about 90 percent tumor-free, so lesion Dice was undefined on almost every case and averaged to near zero. I built `scripts/evaluate.py` to score properly, and on tumor-positive val cases the model scored pancreas Dice 0.716 and lesion Dice 0.174, with specificity only about 8 percent.

Decision: the model does find tumors (real, non-zero lesion Dice), but it badly over-predicts on healthy scans. Two lasting outcomes: fixing the measurement (score positives and negatives separately) mattered as much as fixing the model, and "over-prediction, specificity about 8 percent" became the central problem for everything after.

---

## EXP-04: DiceFocal loss (the "aggressive" model)

Run: e72cfdc8 (transfer, dice_focal, 6000 iters, patch 96, positive-heavy sampling).

Hypothesis (H1): swapping DiceCE for DiceFocal, whose focal term concentrates on hard and rare voxels, will improve the lesion without hurting the pancreas.

Variable: loss `dice_ce` to `dice_focal` (include_background still false).

Result: training-time val reached pancreas 0.703, lesion 0.140. Full evaluation on this checkpoint (the one I later called "aggressive"): pancreas 0.720, lesion Dice 0.169 raw, specificity still about 8 percent. This is the checkpoint the later post-processing levers were first tested on.

Decision: KEEP DiceFocal (lesion learning was at least as good and the focal term is the right tool for the imbalance), but note the over-prediction was not solved. The positive-heavy sampling here was the suspected culprit, which set up EXP-05.

---

## EXP-05: Balanced 1:1 sampling (NULL result)

Run: 4979a5b7 (transfer, dice_focal, 6000 iters, patch 96, balanced 1:1 positive-to-negative sampling).

Hypothesis (H1): the over-prediction is caused by aggressive positive patch sampling; rebalancing to 1:1 will raise specificity without hurting lesion Dice.

Null (H0): the sampling ratio is not the cause and specificity will not move.

Variable: sampling positive-to-negative ratio, aggressive to 1:1. Everything else identical to EXP-04.

Result: essentially identical to the aggressive model on every metric. Pancreas 0.721 versus 0.720, lesion 0.169 versus 0.169, raw specificity 8 percent versus 8 percent, cleaned specificity 42 percent versus 42 percent, threshold sweep nearly the same.

Decision: REJECT H1, accept H0. The sampling ratio is not what drives the over-prediction, so it is ruled out. This is a valuable negative result: it redirected effort away from sampling and toward the loss (EXP-07) and more data. It also reconfirmed that the over-prediction is a property of the model's training, not of the crop mix.

---

## EXP-06: Post-processing levers (evaluation only, no retrain)

Applied to the checkpoints from EXP-04 and EXP-05 with `scripts/evaluate.py`. No training was done, so this is an evaluation experiment.

Hypothesis (H1): false positives on healthy scans can be cut at inference, either by a probability threshold or by an anatomical rule that a lesion must sit near the pancreas.

Result, identical on both the aggressive and balanced models:
- Anatomical constraint (demote lesion components more than 10mm from the predicted pancreas): raw specificity 8 percent (1/12) rose to 42 percent (5/12). Strong lever.
- Probability-threshold sweep: weak. Lesion Dice stayed around 0.16 to 0.18 and specificity held at 8 percent until a 0.90 cutoff, where it reached only 25 percent.
- Cost of the constraint: cleaned lesion Dice on tumor cases dropped from 0.169 to 0.139, the expected sensitivity-for-specificity trade.

Decision: ADOPT the anatomical constraint as the banked specificity lever at evaluation. Interpretation: the false positives are high-confidence and near the organ, so a probability cutoff cannot remove them but a geometric rule can. The fact that it gave the same 8 to 42 lift on both models is why I trust it, it is independent of how the model was trained.

---

## EXP-07: Loss includes background (running 2026-07-07 night)

Run: to fill in (transfer, dice_focal, `include_background: true`, patch 96, 6000 iters). MLflow name `transfer_dice_focal_bg1_posneg_6000i`.

Hypothesis (H1): the over-prediction is driven by the loss excluding background, so the model is never rewarded for calling healthy tissue not-lesion. Including background will raise specificity, and the focal term should keep the rare lesion from being buried.

Null (H0): including background does not lift raw specificity above 8 percent, or it collapses lesion Dice toward 0.

Variable: `loss.include_background` false to true. Single change versus the balanced EXP-05 run.

Accept H1 if: raw specificity climbs above 8 percent while val lesion Dice holds near 0.17.
Reject if: raw specificity stays about 8 percent, or lesion Dice collapses (then use the wired fallbacks, `class_weights [1,1,3]` or lower `lambda_dice`).

Runbook (run this FIRST when I get home; the config already has include_background true):

```bash
source .venv312/bin/activate

# preserve the balanced model before tonight overwrites best.pt
cp outputs/checkpoints/pants-level45/best.pt \
   outputs/checkpoints/pants-level45/balanced_step6000.pt

# tonight's loss experiment (no patch flags, plain 96-cube, only the loss changed)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000

# in the morning: evaluate the new model against the balanced baseline
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 12 --n-neg 12 --sweep --lesion-within-pancreas-mm 10
```

Watch in the first ~15 min: startup prints `device=mps ... cases=100`, the MLflow line `run 'transfer_dice_focal_bg1_posneg_6000i'`, and loss every 25 steps. `last.pt` first writes near step 200. Keep the drive connected and the lid open. Runtime about 5.5 to 6 hours.

Result: to fill in after the run.
Decision: to fill in.

---

## EXP-08: More pancreas context via a larger patch (queued)

Run: to fill in (transfer, patch 128 via `--patch 128`, `--roi 128` at eval). MLflow name auto-includes `p128`.

Motivation: at patch 96 and 1.5mm spacing the field of view is 14.4cm, which usually holds the tumor and most of the pancreas but can clip the tail, and each inference tile reasons locally.

Hypothesis (H1): increasing the patch from 96 to 128 (field of view 14.4cm to 19.2cm, roughly the whole pancreas) improves accuracy, a gain of at least +0.03 pancreas Dice OR +0.02 lesion Dice over the matched 96 baseline, because the model sees more of the organ at once.

Null (H0): the larger patch produces no meaningful change (within plus or minus 0.02).

Variable: patch size only (`sampling.patch_size` and `inference.sw_roi_size` together). Spacing, model, loss, seed, iterations all held constant. Memory-coupled change to watch: try `num_samples 4`, drop to 2 if MPS runs out of memory.

Measurement: full evaluation at n-pos 20 and n-neg 20 (not 12, to cut noise), re-evaluating the 96 baseline at the same n for a fair comparison.

Accept H1 if: pancreas Dice +0.03 or lesion Dice +0.02 without specificity regressing, then adopt patch 128 for the rest of the project.
Reject if: both within plus or minus 0.02 or worse, then record that more context did not help at this depth and defer the fuller fix (ROI cascade) to capstone.

Note: growing the field of view (patch) is transfer-safe; widening the network (init_filters 16 to 32) is not, it breaks the SuPreM load, so that is capstone-only.

Result: to fill in.
Decision: to fill in.

Runbook: see the commands block below.

```bash
source .venv312/bin/activate
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/ctx_baseline_backup.pt
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --patch 128 --num-samples 4 \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000 \
  --run-name transfer_p128_ctx
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 --roi 128
```

---

## Backlog: designed but not yet run

- Transfer versus scratch, full comparison. The scratch runs so far were only the 2-case overfit gate; a full-scale from-scratch baseline has not been run, so the real value of the SuPreM pretraining is not yet quantified on the dev subset. One clean 6000-iter `--scratch` run would give the number.
- Harder-negatives sampling (`sampling.strategy: classes`), already coded, to be tried only if the loss change (EXP-07) is not enough, since sampling proved a weak lever in EXP-05.
- More data, scaling past the 100-case dev subset. The EXP-05 null result points at data volume as the real ceiling; this is the capstone direction.
- ROI cascade (coarse locate then fine segment), the proper fix for whole-organ context; capstone.

## How to add the next entry

Before a run: write the hypothesis, the single variable, what is held constant, and the accept/reject bar. After the run: paste the MLflow name, the training-time val, the full evaluation numbers, and the decision. Never edit a past result; add a new experiment if something changes.
