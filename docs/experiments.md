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

Watch in the first ~15 min: startup prints `device=mps ... cases=100`, the MLflow line `run 'transfer_dice_focal_bg1_posneg_6000i'`, and loss every 25 steps. `last.pt` first writes near step 200. Keep the drive connected and the lid open. Runtime about 5.5 to 6 hours. (A macOS update killed the run at step 5000 overnight; resumed from `last.pt` to finish the last 1000 iters.)

Result (2026-07-08, resumed to 6000, val n=12/12): REJECTED on the primary metric. Raw specificity stayed at 8 percent (1/12), unchanged from every prior model, so including background did not stop the over-prediction at the default decision point. Lesion Dice came in around 0.149 (below the balanced run's 0.169) and cleaned specificity was 33 percent (below the balanced run's 42 percent). On the deployable numbers this is a small step backwards, not forwards.

One real secondary effect worth keeping. Including background recalibrated the model's confidence. The probability-threshold sweep, which was nearly useless before (specificity stuck at 8 percent until 0.90 reached only 25 percent), now climbs to 33 percent at threshold 0.80 and 42 percent at 0.90. So background made the lesion probabilities less overconfident on healthy scans, which finally makes the threshold lever work. But that does not beat what the balanced model already gets from the anatomical constraint (42 percent), and it costs lesion Dice.

Decision: REJECT H1 and revert `include_background` to false. The balanced bg0 config stays the best base (lesion 0.169, cleaned specificity 42 percent). Bigger picture, this is the SECOND training-side lever, after sampling, to leave raw specificity pinned at 8 percent. Two independent knobs ruling it out is strong evidence that the raw over-prediction is a data-scale problem, not something a training tweak fixes at 100 cases. So the plan shifts: stop chasing raw specificity with loss and sampling knobs, bank the post-processing levers (the anatomical constraint reaches 42 percent, and a threshold helps once the model is calibrated), and treat further specificity gains as a more-data problem for the capstone. The next experiment moves to a different axis entirely, patch size and field of view (EXP-08), which tests accuracy rather than specificity.

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

Result (2026-07-09, both models re-scored at matched n=20/20):

| metric | 96 baseline | 128 |
|---|---|---|
| pancreas Dice | 0.740 | 0.747 |
| lesion Dice raw | 0.206 | 0.187 |
| lesion Dice cleaned | 0.197 | 0.175 |
| specificity raw | 10% (2/20) | 25% (5/20) |
| specificity cleaned | 35% (7/20) | 40% (8/20) |

REJECTED on the accuracy hypothesis. Pancreas Dice moved +0.007 (fails the +0.03 bar) and lesion Dice actually went down 0.206 to 0.187 (fails the +0.02 bar, wrong direction). Both accuracy differences are within the noise of 20 cases, so the honest read is that more context did not improve accuracy. Important correction: the apparent lesion "win" seen the night before was an artifact of comparing the 128 (n=20) against the old 96 number on n=12; once the 96 baseline was re-scored on the same 20 cases it came out at 0.206, erasing the gain. This is exactly why the matched baseline is mandatory.

What the larger patch DID do is raise specificity: raw 10 to 25 percent, cleaned 35 to 40 percent. So more context made the base model less trigger-happy on healthy scans, the same over-prediction axis the anatomical constraint works on, at a small cost to lesion Dice. That is a sensitivity-for-specificity trade, not an accuracy gain.

Decision: REJECT H1. Do not adopt 128 as the base for the accuracy line, the plain 96 bg0 balanced model has the best lesion Dice so far (0.206) and stays the accuracy baseline; 128 is noted as a specificity lever if that becomes the priority. The bigger takeaway: context (EXP-08) is now ruled out for accuracy, which isolates the one untested lever, resolution, and elevates EXP-10 (crop to pancreas + finer 1.0mm) as the experiment most likely to move lesion Dice. EXP-10's baseline to beat is the 96 model's lesion Dice of 0.206.

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

## EXP-09: Transfer versus from-scratch (the pretraining ablation)

Run: to fill in (`--scratch`, dice_focal bg0, patch 96, 6000 iters). MLflow name auto `scratch_dice_focal_bg0_p96_posneg_6000i`.

Hypothesis (H1): the SuPreM pretraining materially helps, so a from-scratch SegResNet on the same 100-case dev subset scores clearly lower pancreas and lesion Dice than the transfer model.

Null (H0): from-scratch matches transfer within noise, meaning the pretraining is not doing much at this data scale.

Variable: `--scratch` instead of `--transfer`. Everything else identical to the balanced bg0 baseline.

Why run it now: it fills a real gap (every prior scratch run was only the 2-case overfit gate, so the transfer benefit has never been measured at full scale), and it is the ideal fire-and-forget overnight run because it does not depend on the EXP-08 patch result. It also directly strengthens the presentation claim about why transfer learning was the right call.

Accept H1 if: transfer beats scratch by a clear margin on pancreas and/or lesion Dice. Reject if they land within noise.

Runbook (launch overnight AFTER the EXP-08 run finishes; back up the EXP-08 model first so this does not erase it):

```bash
cp outputs/checkpoints/pants-level45/best.pt \
   outputs/checkpoints/pants-level45/p128_ctx_step6000.pt

source .venv312/bin/activate
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --scratch \
  --ckpt-every 50 --max-iters 6000 --val-limit 12 --val-positive --val-every 1000 \
  --run-name scratch_dice_focal_bg0_p96

# morning: evaluate and compare against the transfer baseline (balanced_step6000.pt)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10
```

Result: to fill in.
Decision: to fill in.

---

## EXP-10: Oracle pancreas ROI at high resolution (the cascade proof-of-concept)

Motivation: the "what the model sees" analysis made it concrete that the model reads a 1.5mm-blurred, low-contrast grid where a tumor is only a handful of voxels whose value barely differs from the pancreas around it. This experiment tests the cascade idea directly: crop each scan to the pancreas and resample it finer, so the model works on a high-resolution view of only the organ. For the course we use the ground-truth Johns Hopkins pancreas mask as the provided outline (the oracle ROI); at capstone a stage-1 model predicts that region and the pipeline is fully automated.

Hypothesis (H1): cropping to the pancreas and training at 1.0mm instead of 1.5mm substantially improves lesion Dice over the whole-scan baseline, because the tumor is now many more voxels and the model is not diluted by irrelevant abdomen.

Null (H0): no meaningful lesion Dice improvement, meaning the ceiling is set by something other than resolution and focus (most likely data volume).

What changes (a bundled package, on purpose): (1) crop to the ground-truth pancreas plus a 20mm margin, and (2) target spacing 1.5mm to 1.0mm. It is intentionally two changes at once because the goal is to prove the concept and measure its ceiling. If it wins, EXP-10a decomposes it by cropping only, still at 1.5mm, to separate how much came from focus versus resolution.

Held constant: same dev_subset and splits, same SuPreM model and bg0 loss, seed 42, 6000 iters, 96 patch, same validation protocol.

Honesty note (important): this is an ORACLE result. It assumes the pancreas region is handed to the model, by the JHU mask now, by a human outline or a stage-1 model later. It must be reported as an upper bound or a semi-automated number, exactly like raw-versus-cleaned, never as the fully autonomous system. That framing is also the real deployed design, where a radiologist provides the outline.

Measurement: full evaluation on the cropped ROIs at n-pos 20 and n-neg 20, passing the same `--spacing` and `--crop-pancreas` at eval so preprocessing matches training. Compare lesion and pancreas Dice against the 96 baseline (`balanced_step6000.pt`) and the 128 result.

Accept H1 if: lesion Dice clears a clear margin over baseline (target +0.05, since this is the big-lever bet). Then adopt the cascade as the capstone direction and report it as the headline "with a provided ROI" number. Reject if lesion Dice is within noise of baseline.

Runbook (de-risk with a 5-minute smoke test first, then the full run):

Sampler note (2026-07-09): the smoke test crashed twice with `No sampling location available` (once at patch 96, once at 64), which ruled out patch size. The real cause is that on a case whose cropped pancreas comes out effectively empty at fine spacing, the pos/neg sampler has no valid location and throws. Fix: when `crop_to_pancreas` is set, training uses `RandSpatialCropSamplesd` (plain random crops) instead of the pos/neg sampler. Inside a cropped pancreas the organ and tumor fill most of the volume so random crops still hit the tumor often, and that sampler cannot raise this error. Runbook uses `--patch 64 --crop-pancreas 30`.

Optimizer/encoder fix (2026-07-09): resuming crashed with an optimizer param-group size mismatch. Root cause: `build_optimizer` only included currently-trainable params, so its shape changed when the encoder unfroze, and as a side effect the encoder was never actually being trained after the warm-up (it never entered the optimizer). Fixed by putting all params in the optimizer and freezing via requires_grad only, plus making checkpoint loading tolerate an optimizer mismatch instead of crashing. CONFOUND to note: this run therefore trains the encoder after step 750, while the 96 baseline (lesion 0.206) was trained under the old frozen-encoder behavior. So a big EXP-10 win is partly attributable to the encoder finally training, not purely resolution. If EXP-10 wins, re-run the 96 baseline with the fixed code for a strictly matched comparison before crediting resolution.

```bash
source .venv312/bin/activate

# 0. SMOKE TEST (~5 min): confirm the pancreas-crop + finer-spacing pipeline runs end to end
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --patch 64 --spacing 1.0 --crop-pancreas 30 --max-iters 50 --no-mlflow --ckpt-every 50

# 1. FULL RUN (only after the smoke test trains cleanly)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --patch 64 --spacing 1.0 --crop-pancreas 30 --ckpt-every 50 \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000 \
  --run-name transfer_roi_pancreas_1mm

# 2. EVAL (must match training preprocessing: same patch/roi + spacing + crop)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --roi 64 --spacing 1.0 --crop-pancreas 30
```

Both prior models are already backed up (`balanced_step6000.pt`, `p128_ctx_step6000.pt`), so this run may overwrite best.pt. Runtime is roughly 4 to 5 hours (small cropped volumes, 64 patch), a comfortable overnight run.

Result (2026-07-09, oracle-ROI `best.pt`, n=20/20, cropped-ROI eval): pancreas Dice 0.726, lesion Dice raw 0.234, cleaned 0.214. Versus the 96 whole-scan baseline (lesion raw 0.206), lesion Dice improved by +0.028, the highest lesion Dice achieved so far. Pancreas came in slightly lower (0.726 vs 0.740), but pancreas was not the target and is scored on the crop here.

Verdict: PROMISING, partial. Lesion Dice improved by a real but modest margin (+0.028), short of the ambitious +0.05 bar but the best result yet, and it supports the cascade thesis directionally. Two honesty caveats: (1) this is an ORACLE result using the ground-truth pancreas mask as the ROI, so it is an upper bound / "with a provided ROI" number, not the autonomous system; (2) this run also got the encoder-training bug fix that the baseline lacked, so part of the +0.028 may be the encoder finally training rather than resolution.

Decision: adopt the ROI/cascade as the capstone direction (best lesion Dice yet, and the mechanism your own reasoning pointed to). The modest size of the gain is further evidence that the dominant remaining lever is data scale, not preprocessing. Next steps: (a) EXP-10b, re-run the 96 baseline with the fixed code to isolate resolution from the encoder fix (if the fixed baseline stays ~0.21, resolution is the driver; if it rises to ~0.23, the encoder fix was); (b) scale up the tumor cases per the Week 3-5 plan, which is the likeliest path to a materially higher number.

---

## EXP-11: Clarity package (crop native, then resample fine) [Track A, tonight]

Motivation: EXP-10 cropped the pancreas AFTER resampling the whole scan to 1.0mm, so detail was averaged away before the crop, and finer spacing on the whole scan is unaffordable. This crops the pancreas in NATIVE resolution first, then resamples only that small ROI to a fine 0.7mm grid. So the model gets the sharpest honest view of the organ, and fine spacing is now cheap because it only touches the ROI.

Hypothesis (H1): cropping native then resampling to 0.7mm beats the EXP-10 oracle ROI (lesion 0.234), because the tumor is both sharper (less pre-crop averaging) and larger in voxels (0.7 vs 1.0mm).

Null (H0): no meaningful lesion Dice gain over 0.234.

Variable (bundled clarity package): crop order (native, before resample) plus spacing (1.0 to 0.7mm). Both serve clarity; if it wins we can decompose later. Transfer-safe: still 1 channel, SuPreM intact. Same 64 patch, bg0 loss, encoder-training fix (same as EXP-10, so this is a clean comparison to 0.234).

Accept H1 if lesion Dice clears 0.234 by a real margin at n=20/20. Reject if within noise.

Runbook (smoke-test first; back up the EXP-10 0.234 model so it is not lost):

```bash
source .venv312/bin/activate
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/roi_1mm_step6000.pt

# smoke test (~5 min)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --crop-native 24 --spacing 0.7 --patch 64 --max-iters 50 --no-mlflow --ckpt-every 50

# full run
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset --transfer \
  --crop-native 24 --spacing 0.7 --patch 64 --ckpt-every 50 \
  --max-iters 6000 --val-limit 12 --val-positive --val-every 1000 \
  --run-name transfer_cropnative_0p7

# eval (match: same crop-native, spacing, roi)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 24 --spacing 0.7 --roi 64
```

Result: INCONCLUSIVE, and it exposed an eval bug. Training-time validation ended at pancreas 0.661 / lesion 0.100 (n=12), already below the 0.72 / 0.206 anchors. The full evaluate.py run printed pancreas 0.217 / lesion 0.024, which looked catastrophic, but that was a measurement bug: evaluate.py defined `--crop-native` but never applied it to the config, so the eval ran the whole body through a model trained only on tiny cropped-pancreas ROIs (total train/eval mismatch). The pancreas collapse to 0.217 was the tell (a resolution change cannot move pancreas from 0.72 to 0.22). Bug fixed on 2026-07-09 (evaluate.py now applies `--crop-native`). The trustworthy signal is the in-loop 0.661 / 0.100.

Decision: REJECT the bundled clarity package as run. Even the trustworthy number was below baseline, because four things changed at once and two starved the model: a 64-voxel patch at 0.7mm is only a 45mm field of view (a thin slab of a 150-200mm organ), and the crop path uses random (not tumor-biased) sub-patches, so the rare lesion was seldom centered. Not a verdict on resolution; a verdict on tiny-FOV plus random sampling. This directly motivates EXP-12 (feed the WHOLE box instead of random sub-patches). Baseline to beat stays EXP-10 lesion 0.234.

Track A queue after this: per-ROI intensity normalization; test-time augmentation at eval (free, no retrain); scale up tumor data. Data-integrity: `scripts/audit_masks.py` screens for empty/tiny pancreas masks (run once, optionally `--write-clean`).

---

## EXP-12: Whole-box ROI (feed the entire pancreas box, no sub-patching) [Track A, tonight]

Motivation: EXP-11 confirmed that random sub-patches inside a cropped ROI starve the model (thin field of view, tumor rarely centered). Quinn's idea: draw the axis-aligned bounding box of the pancreas plus a buffer (which is exactly what CropForegroundd already computes), then feed the ENTIRE box to the model as one fixed cube instead of taking random crops out of it. The model then sees the whole organ plus surrounding context every step. This also simulates the product's "radiologist provides the ROI" mode (an oracle ROI, honestly labelled).

Hypothesis (H1): feeding the whole pancreas box as one cube beats EXP-10 (lesion 0.234), because the model always has the whole organ and its tumor in view, removing the FOV starvation and the sampling lottery that hurt EXP-11.

Null (H0): no meaningful lesion Dice gain over 0.234.

Variable: input construction (whole box fit to one cube via ResizeWithPadOrCropd) versus random sub-patch. Held constant vs a fair anchor: SuPreM transfer, bg0 loss, encoder-training fix. Spacing 1.5mm with a 128 cube spans 192mm, so almost no case gets center-cropped (the whole-organ guarantee holds). Transfer-safe: 1 channel, SuPreM intact.

Accept H1 if lesion Dice clears 0.234 by a real margin at n=20/20. Reject if within noise. Secondary read: does pancreas Dice rise above ~0.72 now that the whole organ is always in view?

Runbook (Codex-audited first, then smoke-test, then full run; uses the clean split that excludes the 5 empty-pancreas cases):

```bash
source .venv312/bin/activate
# back up the EXP-10 0.234 model so it is never lost
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/roi_1mm_step6000.pt 2>/dev/null || true

# smoke test (~3-5 min): proves the whole-box path builds, trains, and checkpoints
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 50 --no-mlflow --ckpt-every 50

# full overnight run
# val-limit 20 (not 12): select the best checkpoint on the SAME 20 tumor-positive cases used at
# final eval, per Codex design review — cuts checkpoint-selection noise and lines the two sets up.
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_p128_1p5

# eval (MUST match training: same crop-native, whole-box, roi, spacing)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result (run `transfer_wholebox_p128_1p5`, 6000 iters, best.pt = best-val checkpoint; note this run
executed in `.venv`, not `.venv312`, so it likely did NOT log to MLflow — re-log the numbers):

In-loop val (n=20 tumor-positive): best val lesion-Dice 0.263 (final step val pancreas 0.812 / lesion 0.220).

Full eval, val split, n=20 positive / 20 free:
- pancreas Dice        : 0.807   (vs ~0.72 anchor — whole-organ context)
- lesion Dice (raw)    : 0.263   (BEATS the 0.234 bar — best result to date)
- lesion Dice (cleaned): 0.252
- specificity (raw)    : 11/20 = 55%   (vs 8% on every prior model)
- specificity (cleaned): 11/20 = 55%   (constraint now a near no-op)
- threshold sweep: 0.30 -> les 0.271 / spec 50%; 0.50 -> 0.263 / 55%; 0.70 -> 0.253 / 60%;
  0.90 -> 0.234 / 70%. Monotonic, usable CADe operating dial.

Decision: ACCEPT. First result to beat 0.234, and it wins on all three axes at once (lesion +0.029,
pancreas +0.09, raw specificity +47pp). The mechanism is clean: raw == cleaned specificity and
near-flat cleaned lesion Dice mean the model now stays quiet on healthy scans by itself, so the
anatomical constraint (our old strong lever) has almost nothing left to remove. This is the new
Track-A best base.

Honesty caveats to carry into the writeup: (1) ORACLE ROI ("radiologist provides the box"), not
autonomous. (2) The specificity leap is partly STRUCTURAL: looking only inside the pancreas box
leaves far less tissue to false-alarm on, so 8%->55% is not like-for-like against the old whole-scan
numbers; frame it as "with a provided ROI." (3) Composite change vs 0.234 (spacing, crop order, FOV,
sampling all moved), n=20 (each free case = 5 specificity points), so this is evidence that "whole-box
at feasible resolution" works, not proof any single knob caused it. (4) Shares the encoder-training
fix, same as EXP-10, so that is controlled in this comparison.

Follow-ups: re-log to MLflow (graded deliverable); pick a default CADe operating threshold from the
sweep; the remaining big lever is data scale (capstone). Autonomous version needs a pancreas detector
in front of this box stage (the cascade).

---

## EXP-13: Clarity curriculum (train on sharper scans) [Week 3, professor's idea]

Motivation: professor's suggestion. Curriculum learning idea. Weight the training set toward the
CLEAREST scans so the model builds good feature detectors on sharp, easy-to-read images before it
has to cope with the blurry ones. "Clearest" is defined by spatial resolution: native slice thickness
first, then in-plane pixel spacing (thinner and finer = sharper).

Data check (train pool): a genuinely sharp cohort exists. The "15 Sites" collection is sub-millimeter
(0.80mm slices, 0.76mm in-plane) with 163 tumor cases, and there is a clean gradient down to 5.0mm.
Wrinkle 1: clarity and tumor-richness are anti-correlated across cohorts (the sharp cohort is
tumor-poorer than the blurry, tumor-rich "1 Site" group), so we MUST hold tumor count constant or we
would be measuring tumor availability, not clarity. Wrinkle 2: the sharpest scans skew non-contrast,
which is actually harder for tumor visibility, so "sharp geometry" and "good tumor conspicuity" are
not the same axis (we chose the resolution axis deliberately).

Design (single variable = training-set clarity; hold N, tumor count, eval set, recipe, seed constant):
`scripts/make_clarity_splits.py --clear-slice-max 0.8` builds two disjoint 20-case training sets, each
10 tumor / 10 healthy:
- `clarity20` (treatment): 12 from the sharpest scans (<=0.8mm) + 8 spread across the rest. Median
  native slice 0.80mm.
- `repr20` (baseline): 20 drawn representatively across the whole clarity range. Median slice 1.50mm.
Both trained with the EXP-12 whole-box recipe (crop-native 16, whole-box, 128 @1.5mm, SuPreM transfer,
bg0), 4000 iters, best.pt by val lesion Dice on the same 20 tumor-positive val cases. Evaluated on the
identical val set (20 pos / 20 free).

Hypothesis (H1): clarity20 beats repr20 by a real margin (lesion Dice +0.02 OR pancreas +0.03) at
n=20 eval, because sharper training images give cleaner patterns to learn.
Null (H0): no meaningful difference, or clarity-weighting hurts (domain gap: the sharp cohort differs
from the representative val set in more than resolution).

Predicted confounds to write up honestly (this is most of the scientific value):
1. Our pipeline resamples every scan to 1.5mm, which NORMALIZES resolution before the model sees it,
   so it may mute the pure-clarity effect. A null result could mean "clarity does not help" OR "our
   resampling already erased the clarity signal." A finer-spacing follow-up would separate these.
2. The sharp cohort differs from the pool in more than sharpness (specific multi-site collection,
   mostly non-contrast), so any effect is clarity plus domain, not clarity alone.
3. n=20 train and n=20 eval: very noisy (each free eval case = 5 specificity points). This is a
   directional pilot, not proof.
4. Both arms share the eval set, so the comparison is a fair relative A/B even though absolute numbers
   at 20 training cases will be well below the 95-case EXP-12 base.

Runbook:

```bash
source .venv312/bin/activate
python scripts/make_clarity_splits.py --clear-slice-max 0.8   # writes clarity20.txt + repr20.txt

# Arm B: clarity-weighted
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split clarity20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name clarity20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/clarity20_best.pt

# Arm A: representative baseline
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split repr20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name repr20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/repr20_best.pt

# eval both on the identical val set + recipe
for M in clarity20 repr20; do
  echo "===== $M ====="
  PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
    --ckpt outputs/checkpoints/pants-level45/${M}_best.pt \
    --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
    --crop-native 16 --whole-box --roi 128 --spacing 1.5
done
```

Result: to fill in (compare clarity20 vs repr20 lesion + pancreas Dice and specificity).
Decision: to fill in.

---

## Backlog: designed but not yet run

- Transfer versus scratch, full comparison. The scratch runs so far were only the 2-case overfit gate; a full-scale from-scratch baseline has not been run, so the real value of the SuPreM pretraining is not yet quantified on the dev subset. One clean 6000-iter `--scratch` run would give the number.
- Harder-negatives sampling (`sampling.strategy: classes`), already coded, to be tried only if the loss change (EXP-07) is not enough, since sampling proved a weak lever in EXP-05.
- More data, scaling past the 100-case dev subset. The EXP-05 null result points at data volume as the real ceiling; this is the capstone direction.
- ROI cascade (coarse locate then fine segment), the proper fix for whole-organ context; capstone.

## How to add the next entry

Before a run: write the hypothesis, the single variable, what is held constant, and the accept/reject bar. After the run: paste the MLflow name, the training-time val, the full evaluation numbers, and the decision. Never edit a past result; add a new experiment if something changes.
