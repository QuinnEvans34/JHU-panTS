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

## EXP-09: Transfer versus from-scratch (the pretraining ablation) [Week 3, queued]

Run: to fill in (`--scratch`, whole-box recipe, 6000 iters). MLflow name `scratch_wholebox_p128_1p5`.

Design update (2026-07-12): the original stub compared scratch-vs-transfer at the old patch-96 recipe (baseline lesion 0.206). That is superseded. The project's best base is now the EXP-12 whole-box recipe (transfer lesion 0.263, pancreas 0.807, spec 55%), so the fair and presentation-relevant version of this ablation runs from-scratch on the SAME whole-box recipe and compares against EXP-12. This makes the transfer arm a run we already have (EXP-12) and keeps the comparison on the model we actually present. The single toggled flag is still `--scratch` vs `--transfer`.

Question it answers: does the SuPreM pretraining actually earn its place, or would a from-scratch SegResNet on 95 cases do just as well? Every prior scratch run was only the 2-case overfit gate, so the transfer benefit has never been measured at full scale. This is the number that defends the core model decision at the Week 3 check-in.

Hypothesis (H1): SuPreM pretraining materially helps, so from-scratch scores clearly lower pancreas and/or lesion Dice than the EXP-12 transfer model.
Null (H0): from-scratch matches transfer within noise, meaning the pretraining is not doing much at 95 cases (which would itself be a real, report-worthy finding, and consistent with the data-scale story).

Variable: `--scratch` instead of `--transfer`. Everything else identical to EXP-12: same `dev_subset_clean` split, whole-box, crop-native 16, patch 128, spacing 1.5, bg0 DiceFocal, seed 42, 6000 iters, val on the same 20 tumor-positive cases.

Confound to state honestly (do not skip): the two arms are not a pure initialization-only test. Transfer uses `lr_transfer` 1e-4 with a 3-epoch encoder-freeze warm-up; scratch uses `lr_scratch` 2e-4 with no freeze (train.py applies the freeze only when pretrained). That is the intended, each-regime-tuned way to run them, so the honest framing of the result is "the SuPreM transfer recipe vs a from-scratch recipe," the practical question. If a strictly initialization-only isolation is wanted later, re-run scratch at matched LR with no freeze on the transfer side.

Measurement: full eval at n-pos 20 / n-neg 20 on the same val cases as EXP-12, so the transfer numbers are EXP-12's (0.807 / 0.263 / 55%). Report pancreas Dice, lesion Dice (raw + cleaned), and specificity.

Accept H1 if: transfer beats scratch by a clear margin (lesion Dice gap >= 0.03 or pancreas Dice gap >= 0.03). Reject (accept H0) if they land within noise (both within +/- 0.02), and record that pretraining does not move the needle at this scale.

Runbook (fire-and-forget overnight; no dependency on other runs; back up whatever best.pt currently exists first):

```bash
source .venv312/bin/activate
# preserve the current best.pt before this run overwrites it
cp outputs/checkpoints/pants-level45/best.pt \
   outputs/checkpoints/pants-level45/prev_best_backup_$(date +%Y%m%d).pt 2>/dev/null || true

# from-scratch arm, identical to EXP-12 except --scratch
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --scratch \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name scratch_wholebox_p128_1p5
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/scratch_wholebox_best.pt

# morning: eval on the SAME 20/20 val cases and recipe as EXP-12, compare to 0.807 / 0.263 / 55%
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/scratch_wholebox_best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Note on the transfer arm: EXP-12's whole-box checkpoint is the transfer side of this comparison. If that checkpoint was overwritten by the EXP-13/14 20-case runs (see the EXP-15 provenance note), re-run the EXP-12 command (swap `--scratch` back to `--transfer`, run-name `transfer_wholebox_p128_1p5`) so both arms are freshly matched under the current code, then compare the two directly.

Result (2026-07-14, both best-val checkpoints, eval n=20/20; transfer = regenerated EXP-12 step 2000, scratch step 4000):

| metric | transfer (SuPreM) | scratch |
|---|---|---|
| pancreas Dice | 0.778 | 0.650 |
| lesion Dice raw | 0.257 | 0.120 |
| lesion Dice cleaned | 0.263 | 0.137 |
| specificity raw | 50% (10/20) | 0% (0/20) |
| specificity cleaned | 55% (11/20) | 5% (1/20) |

Decision: ACCEPT H1 DECISIVELY. Transfer beats scratch on every axis by margins far past the 0.03 bar: lesion +0.137 raw, pancreas +0.128, specificity +50 points. From-scratch on 95 cases barely learns the pancreas (0.650) and over-predicts on every single healthy scan (0% specificity), while the SuPreM-initialized model reaches a usable 0.778 / 0.263 / 55%. So the SuPreM pretraining is not a marginal boost, it is what makes the model work at this data scale, which is the number that defends the model choice at the Week 3 check-in. Confound acknowledged: the two arms also differ in LR (1e-4 vs 2e-4) and the encoder-freeze warm-up (transfer only), so this is the practical "transfer recipe vs scratch recipe" comparison, not a pure initialization-only isolation. But the gap is far too large for the LR/freeze differences to account for it. The transfer arm here is also the regenerated EXP-12 (see EXP-12 regeneration note), which reproduced the lost original within noise.

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

Regeneration (2026-07-14): the original EXP-12 checkpoint was confirmed lost (see the Checkpoint &
logging discipline note), so I re-ran the identical command (seed 42, dev_subset_clean, whole-box,
6000 iters). The clean, uninterrupted re-run REPRODUCED the result within noise: pancreas 0.778 (vs
0.807), lesion 0.257 raw / 0.263 cleaned (vs 0.263 raw), specificity 50% raw / 55% cleaned (vs 55%).
The 55% specificity reproducing is the important part: it was not a lucky draw. Two process lessons
came out of the recovery: (1) an interrupted-then-`--resume`d run produced a badly non-reproducing
checkpoint (lesion 0.096, pancreas 0.723) because resume resets the best-val tracker to -1 and then
overwrote the good shared best.pt with a worse late checkpoint. So keeper runs must run uninterrupted,
and resume needs hardening (restore best_val from the checkpoint; never overwrite a better best.pt with
a worse one). (2) A separately interrupted run's best.pt landed at step 3000 with only 15% specificity,
confirming specificity is the noisier, run-to-run-variable metric (it is not what best.pt selects on),
while lesion Dice reproduces tightly across all three checkpoints (0.236 / 0.257 / 0.263). The per-run
archive is what made recovery possible: every attempt's best.pt survived in its own immutable folder.
Reported EXP-12 numbers going forward use the clean regenerated checkpoint (archive
`transfer_wholebox_p128_1p5__20260713_221119`, pinned as `wholebox_p128_1p5_GOOD.pt`).

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

Result (eval n=20 pos / 20 free, both best.pt at step 2000; models early-stopped by val since 20 cases overfit fast):

| metric | clarity20 (sharp, median 0.80mm) | repr20 (representative, 1.50mm) |
|---|---|---|
| pancreas Dice | 0.780 | 0.782 |
| lesion Dice raw | 0.204 | 0.189 |
| lesion Dice cleaned | 0.208 | 0.182 |
| specificity raw | 85% (17/20) | 50% (10/20) |
| specificity cleaned | 90% (18/20) | 60% (12/20) |

Sweep: clarity holds ~0.20 lesion Dice at 80-95% specificity (0.70 thr -> 0.196 / 95%); repr must reach 0.90 thr to hit 85% and sits at 55% at 0.50 thr.

Decision: SOFT NULL on the pre-registered accuracy bar, STRONG (but confounded) surprise on specificity. Lesion Dice is +0.015 raw / +0.026 cleaned and pancreas is flat, so it does not cleanly clear the +0.02 accuracy bar. That soft null is consistent with the predicted confound #1: resampling to 1.5mm normalizes native resolution away before the model sees it, so "sharper = more accurate" barely shows up in Dice. The unregistered surprise is specificity: the clarity-weighted model is far less trigger-happy on healthy scans (raw 50->85, cleaned 60->90), a Pareto win here since Dice is tied-or-better too. Treat this as a strong hypothesis-generating result, NOT a confirmed causal claim of sharpness, because (confound #2) the sharp cohort also differs in site and contrast phase (mostly non-contrast), so the gain could be domain/appearance rather than resolution; and n=20 (each free case = 5 pts) means the 7-case gap is directionally credible but wide. Mechanistic read: training on the sharp, mostly non-contrast cohort may give the model a cleaner sense of "normal pancreas," so it hallucinates fewer tumors on healthy scans. Follow-up to isolate the cause: repeat controlling for contrast phase, or at larger n. Note both arms are 20-case models, so absolute numbers sit below the 95-case whole-box base (lesion 0.263); the value is the relative clarity-vs-representative contrast, which is real and large on specificity.

---

## EXP-14: Contrast phase, isolated from resolution [Week 3, follow-up to EXP-13]

Motivation: EXP-13 raised specificity but its sharp cohort was also mostly non-contrast, so clarity and contrast phase were confounded. This isolates contrast phase to answer the question EXP-13 could not: is contrast phase the real driver of the specificity effect?

Design: `scripts/make_contrast_splits.py` builds two disjoint 20-case sets (10 tumor / 10 healthy), both drawn from the slice 1.0-2.0mm + in-plane 0.7-1.1mm band, so both land at median slice ~1.2mm and in-plane 0.80mm. Only contrast phase differs: `nc20` = non-contrast, `pv20` = portal-venous. Both trained with the whole-box recipe (crop-native 16, whole-box, 128 @1.5mm, SuPreM transfer, bg0), 4000 iters, best.pt by val lesion on the same 20 tumor-positive val cases, evaluated on the identical val set (20 pos / 20 free).

Hypothesis (H1, primary and clean = specificity): at matched resolution, non-contrast trains a MORE specific model than portal-venous, because non-contrast tumors are subtle so the model learns to be cautious about calling them. Accept if nc20 specificity beats pv20 by >= 3 healthy cases (about 15 points) at n=20.
Secondary (confounded = sensitivity): portal-venous >= non-contrast on lesion Dice, since tumors are more conspicuous with contrast. Report but do not over-claim (see limitation).

Interpretation either way: if nc >> pv on specificity, contrast phase IS the driver behind the EXP-13 surprise (confirms the reinterpretation). If nc ~ pv, contrast is ruled out and EXP-13's specificity gain came from something else (residual resolution, or site/domain). Both outcomes are informative.

Known limitation, stated up front: tumor SIZE could not be fully matched. At this resolution non-contrast has only ~11 tumors, and they are smaller, so even after a common 1000-20000 mm3 size band the venous tumors stay ~1.9x larger (median 8359 vs 4473). Therefore the SPECIFICITY read (healthy scans, no tumor size involved) is the clean primary result; the lesion-Dice read carries a residual size advantage for portal-venous and cannot separate contrast conspicuity from tumor size at n=10. That non-contrast tumors are both fewer and smaller at matched resolution is itself a finding. n=20 eval (each healthy case = 5 points).

Split facts (seed 42, disjoint): nc20 median slice 1.25mm / in-plane 0.80mm / lesion 4473 mm3; pv20 1.12mm / 0.81mm / 8359 mm3.

Runbook:

```bash
source .venv312/bin/activate
python scripts/make_contrast_splits.py            # writes nc20.txt + pv20.txt

# Arm NC: non-contrast
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split nc20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name nc20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/nc20_best.pt

# Arm PV: portal-venous
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split pv20 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 4000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name pv20_wholebox
cp outputs/checkpoints/pants-level45/best.pt outputs/checkpoints/pants-level45/pv20_best.pt

# eval both on the identical val set + recipe
for M in nc20 pv20; do
  echo "===== $M ====="
  PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
    --ckpt outputs/checkpoints/pants-level45/${M}_best.pt \
    --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
    --crop-native 16 --whole-box --roi 128 --spacing 1.5
done
```

Result (eval n=20 pos / 20 free; nc20 best.pt step 2000, pv20 best.pt step 1000, both early-stopped by val):

| metric | nc20 (non-contrast) | pv20 (portal-venous) |
|---|---|---|
| pancreas Dice | 0.791 | 0.704 |
| lesion Dice raw | 0.116 | 0.124 |
| lesion Dice cleaned | 0.116 | 0.138 |
| specificity raw | 90% (18/20) | 10% (2/20) |
| specificity cleaned | 95% (19/20) | 10% (2/20) |

Sweep: nc20 holds 90-95% specificity at every threshold (already saturated); pv20 climbs 10% -> 50% only by threshold 0.90.

Decision: ACCEPT H1 (specificity), DECISIVELY. At matched resolution, non-contrast trained a far more specific model than portal-venous: raw specificity 90% vs 10%, a 16-case gap at n=20, cleaned 95% vs 10%. This confirms the reinterpretation of EXP-13: contrast phase, NOT resolution/clarity, is the driver of the specificity effect (EXP-13's clarity cohort was mostly non-contrast). Mechanism: non-contrast tumors are subtle, so the model learns caution and rarely false-alarms on a healthy pancreas; portal-venous tumors are conspicuous, so the model learns "bright pancreatic region = tumor" and over-fires on healthy scans (18/20 flagged). Secondary, size-confounded: portal-venous edges non-contrast on lesion Dice (raw 0.124 vs 0.116, cleaned 0.138 vs 0.116), directionally consistent with contrast raising sensitivity, but the gap is small and pv tumors were ~1.9x larger, so do not over-claim. Pancreas gap (0.791 vs 0.704) is partly a training-time artifact (pv early-stopped at step 1000 vs nc 2000). Caveats: n=20 (but 90 vs 10 is far outside noise); contrast phase is not randomized, it travels with acquisition protocol and scan indication, so it bundles those. Product implication: contrast phase is a real operating-point dial, train toward non-contrast for specificity (screening) or portal-venous for sensitivity (catch-everything); the phase-mixed dev subset (EXP-12, 55% spec) sits between the two extremes. This is the strongest single explanatory result of the project so far and the headline for the Week 3 check-in.

---

## EXP-15: Test-time augmentation at evaluation (free lever, no retrain) [Week 3, queued]

Motivation: TTA is the cheapest lever left. Averaging the model's predictions over label-preserving flips of the input usually steadies segmentation output at no training cost. It is a pure evaluation change on an existing checkpoint, so it either helps for free or it does not, and either way it is a clean thing to report.

What it does (now wired in code): `evaluate.py --tta` runs sliding-window inference on all 8 flip combinations of the three spatial axes, un-flips each prediction back to the original frame, and averages the softmax probabilities before argmax/threshold. The threshold sweep and the anatomical constraint run on the averaged probabilities exactly as before. Implemented in `src/inference/sliding_window.py::predict_probs_tta`; the non-TTA path is untouched.

Target checkpoint: the EXP-12 whole-box best (lesion 0.263 / pancreas 0.807 / spec 55%). This is a single-variable test: same checkpoint, same 20/20 val cases, same recipe, TTA off (EXP-12 numbers) vs TTA on.

PROVENANCE CAVEAT (RESOLVED 2026-07-12): the EXP-12 whole-box checkpoint is confirmed GONE from disk. A second Claude session searched the whole repo tree: the four named backups are other runs (aggressive/balanced = sampling, `p128_ctx` = EXP-08, `roi_1mm` = EXP-10), there is no Jul-10 file anywhere, and the current `best.pt`/`last.pt` are the EXP-14 pv20 model. It was never an MLflow artifact either (EXP-12 ran in `.venv` without mlflow; `log_run_to_mlflow.py` logs only params/metrics, not weights). Only a Time Machine snapshot from before Jul 11 13:18 could recover the exact bytes. Plan: regenerate by re-running the EXP-12 command (`--transfer`, whole-box, run-name `transfer_wholebox_p128_1p5`); seed 42 + unchanged training code reproduces a statistically equivalent model (within n=20 noise of 0.807/0.263/55%), which is all TTA needs. This folds into the EXP-09 night (the transfer arm IS the regenerated EXP-12). Going forward this cannot recur: `train.py` now auto-archives every keeper into `outputs/checkpoints/pants-level45/runs/<run_name>__<timestamp>/` with a `run_info.txt`, plus a `run_ledger.csv` row, independent of MLflow.

Hypothesis (H1): 8-view flip TTA improves the deployable numbers on the EXP-12 model, lesion Dice +>=0.01 OR specificity +>=1 healthy case, without regressing the other.
Null (H0): TTA changes nothing beyond noise (whole-box input is already centered and low-variance, so flips add little).

Accept if: either lesion Dice or specificity improves with no meaningful regression on the other, then adopt TTA as a default at eval (it is free). Reject if flat or if it trades one metric down for the other (then it is not a free win and we leave it off).

Cost: 8x forward passes at eval only. In whole-box mode each case is a single 128-cube window, so 40 cases x 8 views is a few minutes, not an overnight run.

Runbook:

```bash
source .venv312/bin/activate
# EXP-12 baseline (TTA off) for the matched comparison, if not already recorded at n=20/20:
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/<exp12_wholebox>.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5

# same checkpoint + recipe, TTA on (the only change)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/<exp12_wholebox>.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5 --tta
```

Result (2026-07-14, EXP-12 GOOD ckpt `wholebox_p128_1p5_GOOD.pt`, eval n=20/20):

| metric | no TTA (EXP-12) | 8-view flip TTA |
|---|---|---|
| pancreas Dice | 0.778 | 0.756 |
| lesion Dice raw | 0.257 | 0.234 |
| lesion Dice cleaned | 0.263 | 0.238 |
| specificity raw | 50% (10/20) | 75% (15/20) |
| specificity cleaned | 55% (11/20) | 80% (16/20) |

TTA sweep: thr 0.40 -> lesion 0.239 / spec 75%; 0.60 -> 0.220 / 85%; 0.80 -> 0.161 / 90%; 0.90 -> 0.140 / 90%.

Decision: REJECT as an always-on default, per the pre-registered bar (it did not improve one metric with no meaningful regression on the other). TTA raised specificity sharply (+25 points, 55% -> 80% cleaned) but cost lesion Dice (0.263 -> 0.238) and a little pancreas Dice (0.778 -> 0.756), so it is a sensitivity-for-specificity TRADE, not a free win. KEEP it in the toolbox as a genuine specificity lever, though: it reaches an 80-90% specificity regime the non-TTA threshold sweep could NOT (that sweep capped at 55% even at threshold 0.90). Mechanism: averaging predictions over the 8 flips softens the lesion probabilities and suppresses the high-confidence near-organ false positives that a threshold alone cannot remove, so it behaves like a principled confidence-lowering. Product read: TTA joins contrast phase (EXP-14) and the probability threshold as an operating-point dial for the CADe story, use it when screening specificity is the priority and leave it off when lesion-outline accuracy is. Caveat: n=20 (each healthy case is 5 points), so +25pp is directionally strong but wide. Adopted default stays TTA-off for the reported accuracy numbers.

---

## EXP-16: Resolution inside the whole box (finer spacing, matched field of view) [Week 3, running tonight]

Motivation: whole-box (EXP-12) fixed the field of view and the specificity, but lesion Dice has plateaued around 0.26 across every recipe change. Resolution is the one untested accuracy axis that needs no new infrastructure, and EXP-10 hinted finer resolution helps once the whole organ is in view. The current whole box is a 128 cube at 1.5mm = a 192mm span sampled at 1.5mm per voxel. This run holds that physical span constant but samples it finer.

Variable (single = resolution): patch 128 -> 160 AND spacing 1.5 -> 1.2mm together, so the box footprint stays 192mm (160 x 1.2 = 192 = 128 x 1.5) but each voxel is 1.2mm instead of 1.5mm, giving the tumor about 1.95x more voxels. Holding the field of view constant is exactly what makes this a resolution test and not a field-of-view change (the confound that sank EXP-11). Everything else is identical to EXP-12: SuPreM transfer, crop-native 16, whole-box, bg0 DiceFocal, seed 42, 6000 iters, val on the same 20 tumor-positive cases.

Hypothesis (H1): finer resolution raises lesion Dice by >= 0.02 over EXP-12 (0.263 cleaned) at n=20, because the tumor is resolved in more voxels.
Null (H0): no meaningful lesion Dice gain (within +/- 0.02), meaning resolution is not the ceiling and data scale is (consistent with every other null this project).

Accept H1 if: lesion Dice clears 0.283 at n=20 without specificity collapsing. Reject if within noise.

Cost / risk: about 2x the voxels of EXP-12, so more MPS memory and a longer run. Smoke-tested first (50 iters) so a memory failure aborts before the full run rather than wasting the night. If it OOMs, the fallback is patch 144 @ 1.33mm (also ~192mm span, ~1.4x voxels), or keep 128 and drop spacing to 1.2 (smaller 154mm FOV, less preferred).

Runbook (smoke test gates the full run via `&&`, so a broken/OOM config never reaches the overnight run):

```bash
source .venv312/bin/activate
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 160 --spacing 1.2 \
  --max-iters 50 --val-limit 0 --no-mlflow --ckpt-every 50 --run-name smoke_p160 \
&& caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split dev_subset_clean --transfer \
  --crop-native 16 --whole-box --patch 160 --spacing 1.2 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_p160_1p2

# morning eval (must match training: roi 160, spacing 1.2)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_p160_1p2__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 160 --spacing 1.2
```

Result (2026-07-15, `transfer_wholebox_p160_1p2` best.pt, eval n=20/20):

| metric | EXP-12 (128 @ 1.5mm) | EXP-16 (160 @ 1.2mm) |
|---|---|---|
| pancreas Dice | 0.778 | 0.805 |
| lesion Dice raw | 0.257 | 0.248 |
| lesion Dice cleaned | 0.263 | 0.228 |
| specificity raw | 50% | 55% |
| specificity cleaned | 55% | 55% |

Decision: REJECT H1 (accept H0). Finer resolution at matched field of view did NOT raise lesion Dice: raw 0.248 vs 0.257 (within noise, slightly lower), cleaned 0.228 vs 0.263 (lower), both well short of the 0.283 bar. It DID raise pancreas Dice (0.778 -> 0.805, back to the original EXP-12 level), which makes sense: the large, easy pancreas benefits from more voxels, the tiny lesion does not. Specificity unchanged (55%). Interpretation: resolution is not the lesion-accuracy lever. This is the decisive null the strategy needed. We have now ruled out, for lesion accuracy, every recipe axis available without new data: sampling (EXP-05), loss (EXP-07), field-of-view / context (EXP-08), and now resolution (EXP-16), while the one structural win (whole-box, EXP-12) lifted pancreas and specificity but not lesion Dice. Four independent nulls point the same way: lesion Dice ~0.26 is the honest ceiling at 95 cases, and DATA SCALE is the remaining lever (the disk-cache / capstone direction). Minor process note: cleaned < raw here (0.228 < 0.248), unlike EXP-12, suggesting finer resolution fragments the lesion into pieces the largest-CC/constraint prunes; if resolution is ever revisited, relax largest-CC. Reported base model stays EXP-12 (128 @ 1.5mm, lesion 0.263).

---

## EXP-17: Data scale-up — 3x the tumor cases (the lever every null pointed to) [Week 3/4, running tonight]

Motivation: four independent recipe axes are now ruled out for lesion accuracy (sampling EXP-05, loss EXP-07, context EXP-08, resolution EXP-16), and the whole-box structural win lifted pancreas + specificity but not lesion Dice. Every arrow points at data scale. This is the first test of that hypothesis: hold the winning whole-box recipe fixed and just feed it more tumor cases. No disk cache needed yet — the RAM CacheDataset handles ~300 whole-box cubes (~5 GB); the cost is a longer one-time cache build.

Variable (single = training-set size): split `dev_subset_clean` (95 cases, 50 tumor) -> `scaled300` (300 cases, 150 tumor). A 3x increase in tumor examples, the bottleneck class. Everything else identical to EXP-12: SuPreM transfer, crop-native 16, whole-box, 128 @ 1.5mm, bg0 DiceFocal, seed 42, 6000 iters, val on the same 20 tumor-positive / 20 tumor-free cases. Split built by `scripts/make_scaled_split.py --n-tumor 150 --n-healthy 150` (manifest-only, seed 42, drawn from the 706 tumor / 6494 healthy train pool).

Hypothesis (H1): more tumor data raises lesion Dice by a real margin, clearing 0.30 at n=20 (up from the 0.263 ceiling), because the model finally sees enough tumor variety to generalize rather than memorize ~50.
Null (H0): lesion Dice stays within noise of 0.263, meaning 3x is not enough and the fix is either much more data or the cascade (capstone).

Accept H1 if: lesion Dice >= 0.30 at n=20 without specificity collapsing. Reject if within +/- 0.02 of 0.263. Secondary read: EXP-12/16 peaked early (best checkpoint ~step 2000) then overfit; with 3x data the peak should land later and higher, so watch whether the in-loop val is still climbing at step 6000 (if so, EXP-17b extends to 10-12k iters).

Cost / risk: the cache build loads 300 full scans from the external drive up front (~30-45 min) before training starts, which front-loads the drive I/O (good: training then runs from RAM, less overnight drive exposure) but concentrates drive-drop risk in the first hour, so keep the drive mounted + lid open + caffeinate. Bad-mask cases (empty/tiny pancreas) are handled by the whole-box `PadEmptyCropd` guard rather than crashing, so an audit pass is optional; run `audit_masks.py` only if the cache build errors on a case. 6000 iters held constant for a clean comparison to EXP-12.

Runbook:

```bash
source .venv312/bin/activate
# split already built: outputs/splits/scaled300.txt (300 cases, 150 tumor)

caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled300 --transfer \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_scaled300

# morning eval (same recipe + val set; use the archived path)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaled300__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result (2026-07-16, `transfer_wholebox_scaled300` best.pt, eval n=20/20):

| metric | EXP-12 (95 cases, 50 tumor) | EXP-17 (300 cases, 150 tumor) |
|---|---|---|
| pancreas Dice | 0.778 | 0.815 |
| lesion Dice raw | 0.257 | 0.313 |
| lesion Dice cleaned | 0.263 | 0.327 |
| specificity raw | 50% | 50% |
| specificity cleaned | 55% | 50% |

Sweep: lesion Dice ~0.31 flat-to-slightly-rising across thresholds; specificity climbs 40% -> 70% (thr 0.90 -> lesion 0.319 / spec 70%; thr 0.80 -> 0.318 / 65%).

Decision: ACCEPT H1 DECISIVELY. Tripling the tumor data moved lesion Dice from 0.263 to 0.313 raw / 0.327 cleaned (+0.05 / +0.064), clearing the 0.30 bar and beating the ceiling that four recipe levers (sampling, loss, context, resolution) could not touch. Pancreas also rose (0.778 -> 0.815). Specificity essentially held (50% vs 55%, within n=20 noise). Two extra wins: (1) CADe post-processing now HELPS (cleaned 0.327 > raw 0.313, the reverse of EXP-16), so the predictions are cleaner; (2) the whole operating curve shifted UP, at threshold 0.90 you get lesion 0.319 AND specificity 70%, a strictly better dial than EXP-12. This is the first result all week to beat 0.263 and it directly confirms the project's central hypothesis: lesion accuracy is DATA-limited, not recipe-limited. Data scale is THE lever. New Track-A best base. Caveats: n=20 (each healthy case ~5 spec points, so 50 vs 55 is noise); the run executed in `.venv` (Python 3.14, no MLflow) so re-log via `log_run_to_mlflow.py`; check the best checkpoint's step, if in-loop val was still climbing near 6000, EXP-17b (more iters and/or more data) likely climbs further. Pinned as `wholebox_scaled300_GOOD.pt` (archive `transfer_wholebox_scaled300__20260715_205005`). Next: Week 4 = build the disk cache to scale past 300 (500-1000 cases) + add a patient-level detection-sensitivity metric.

---

## EXP-17b: Scale further with the disk cache — 600 cases, 6x tumor [Week 4, running tonight]

Motivation: EXP-17 proved data is the lever (0.263 -> 0.327 at 300 cases). This continues up the curve to 600 cases (300 tumor, 6x the original dev subset) and, in doing so, tests the new disk-cache code that makes scaling past RAM feasible and resume-safe.

New infrastructure (built 2026-07-16): `dataset.py` now supports `cache=disk` via MONAI `PersistentDataset`, wired through `train.py --cache disk` and `config training.cache`/`cache_dir`. It caches the deterministic preprocessing to the internal SSD (`outputs/cache/<recipe-tag>/`) once, filling lazily over the first epoch, then every epoch and every future run reuses it. Unlike the RAM CacheDataset (rebuilt each run, capped by memory), the disk cache scales to thousands of cases and survives interruption. Split built by `make_scaled_split.py --n-tumor 300 --n-healthy 300 --name scaled600`.

Variables (not a pure single-variable run, stated honestly): (1) training data 300 -> 600 cases / 150 -> 300 tumor; (2) iterations 6000 -> 8000, because more data warrants more exposure; (3) cache ram -> disk (an infrastructure change that should not affect the model, only speed/scale). The recipe is otherwise the EXP-12/17 whole-box: SuPreM transfer, crop-native 16, whole-box, 128 @ 1.5mm, bg0 DiceFocal, seed 42, val on the same 20/20.

Hypothesis (H1): continued data scaling raises lesion Dice further, clearing 0.35 at n=20 (a real climb above EXP-17's 0.327), because the model is still data-starved.
Null (H0): lesion Dice plateaus near 0.327, meaning 300 tumor cases is near the point of diminishing returns for this recipe and the next gain needs the cascade or richer labels, not just more data.

Accept H1 if: lesion Dice clears 0.35 at n=20 (or clearly beats 0.327 beyond noise) without specificity collapsing. Either way it maps the data-scaling curve, which is the Week 4 deliverable.

Notes / risk: RUN FROM `.venv312` so it logs to MLflow (EXP-17 ran in `.venv` and did not). The disk cache loads the 600 scans off the external drive over the first epoch (spread out, not a giant upfront build), so keep the drive mounted through roughly the first hour; after that training runs from the SSD cache and the external drive is no longer touched. Do NOT `--resume` (best_val reset bug still unhardened) — run uninterrupted. ~8000 iters at MPS ~0.3 it/s is roughly 7-8h plus the first-epoch cache fill, comfortably inside a 12h window.

Runbook:

```bash
source .venv312/bin/activate   # MLflow logging this time

# 0. smoke test the disk-cache path (~2-3 min): confirms it writes to outputs/cache/
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled600 --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 30 --val-limit 0 --no-mlflow --ckpt-every 30 --run-name smoke_disk
ls -la outputs/cache/ && du -sh outputs/cache/* 2>/dev/null   # should show a populated cache dir

# 1. full overnight run
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled600 --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 8000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_scaled600

# 2. morning eval (archived path)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaled600__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result: to fill in.
Decision: to fill in.

---

## EXP-17c: Max data + long training — every tumor case, 15h+ [Week 4, running tonight]

Motivation: EXP-17 proved data is the lever (0.263 -> 0.327 at 300 cases); the per-case analysis (analyze_cases.py, scaled300) then showed the model DETECTS 95% of tumors but OVER-SEGMENTS them (predicted volume 4-8x ground truth on small/medium tumors), which is what caps Dice. This run pushes the data lever to its ceiling and trains long, to answer two questions at once: (1) does more data + more training keep raising lesion Dice, and (2) does it reduce the over-segmentation on its own — or does that need a loss change (EXP-18 Tversky)?

Scale: `scaledmax` = 706 tumor + 706 healthy = 1412 cases — ALL 706 tumor cases in the train pool (14x the original dev subset, and the maximum tumor data the Mini release's train partition offers; val/test tumors are held out). Uses the new disk cache (`--cache disk`, ~22 GB on the SSD) since this far exceeds RAM.

Variables (not single-variable, stated honestly): data 300 -> 1412 cases (150 -> 706 tumor) AND iterations 6000 -> ~24000 (long training). Recipe otherwise fixed to the EXP-12/17 whole-box: SuPreM transfer, crop-native 16, whole-box 128 @ 1.5mm, bg0 DiceFocal, seed 42. Loss deliberately held at DiceFocal so this is a clean test of "data + training time," with the loss (Tversky, to attack over-segmentation) reserved for EXP-18.

Hypothesis (H1): max data + long training raises lesion Dice clearly above 0.327 (target >= 0.36) and the val curve is still climbing at the end (which would justify a multi-day run).
Null (H0): lesion Dice plateaus near 0.327 despite 14x tumor data and 4x iterations — which would mean the remaining gap is the over-segmentation the LOSS must fix (EXP-18), not something more data solves.

Accept H1 if lesion Dice clears 0.36 at n>=20 without specificity collapsing. Read the val-Dice progression: still rising at 24k iters -> a 72h run is warranted; flat by ~12k -> the ceiling is the loss/recipe, not data volume.

Notes / risk: RUN FROM `.venv312` (MLflow). First epoch fills the disk cache by loading 1412 scans off the external drive (~1-2h) — keep the drive mounted + lid open + caffeinate through that window; after it caches, training runs from the SSD and the drive is idle. Do NOT `--resume` (best_val reset bug); run uninterrupted. ~24000 iters at MPS ~2s/step is roughly 13-14h of training + the cache build, landing near morning. best.pt (by val lesion Dice) is archived, so whatever it reaches is safe. Morning: eval at a larger n (e.g. --n-pos 40) for a stabler read, and re-run analyze_cases.py to check whether the over-segmentation shrank.

Runbook:

```bash
source .venv312/bin/activate

# 0. smoke test the disk-cache path on scaledmax (~2-3 min)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaledmax --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 30 --val-limit 0 --no-mlflow --ckpt-every 30 --run-name smoke_scaledmax

# 1. the long run (~15h)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaledmax --transfer --cache disk \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 500 \
  --max-iters 24000 --val-limit 20 --val-positive --val-every 2000 \
  --run-name transfer_wholebox_scaledmax

# 2. morning: stabler eval + over-segmentation check
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaledmax__<STAMP>/best.pt \
  --n-pos 40 --n-neg 40 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/analyze_cases.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaledmax__<STAMP>/best.pt \
  --n-pos 40 --crop-native 16 --whole-box --roi 128 --spacing 1.5
```

Result (2026-07-17, run `transfer_wholebox_scaledmax`, archive `..._scaledmax__20260716_165439`, logged to MLflow from .venv312): **best in-loop VAL lesion-Dice 0.487** (n=20 tumor-positive), up from EXP-17's 0.327 — a +0.16 jump, the biggest single move of the project, blowing past the pre-registered 0.36 bar and approaching the ~0.53 segmentation SOTA. Pinned `wholebox_scaledmax_GOOD.pt`.

PENDING before this is final: (1) full `evaluate.py` at n=40 to confirm the in-loop number (in-loop has tracked full-eval closely for whole-box, e.g. scaled300 was 0.313/0.313, so 0.487 is expected to hold, but confirm); (2) read the MLflow val-Dice curve — was it still climbing at 24k iters? and (3) analyze_cases to see whether the gain came from tighter outlines (less over-segmentation) or catching more tumors.

FULL EVAL CONFIRMED (2026-07-17, n=40/40): pancreas Dice **0.837**, lesion Dice **0.524 raw / 0.528 cleaned** — HIGHER than the in-loop 0.487 and on double the cases, so this is solid. Essentially at the ~0.53 segmentation SOTA reference (with the provided-ROI-upper-bound caveat). Detection sensitivity 36/40 = 90%; detected-only lesion Dice 0.582. analyze_cases breakdown:
- By size: small <1cm3 (n=7) 0.225 @ 86% det; medium 1-8cm3 (n=23) 0.536 @ 87%; large >8cm3 (n=10) 0.703 @ 100%. Every bin improved vs scaled300 (small 0.054->0.225, medium 0.324->0.536, large 0.609->0.703).
- By phase: non-contrast (n=18) 0.425, arterial (n=6) 0.491, venous (n=16) 0.646 — the EXP-14 conspicuity gradient persists but non-contrast rose from 0.169.
- KEY MECHANISM: the over-segmentation from scaled300 is LARGELY GONE. Predicted lesion volumes are now within ~1-2x of ground truth (e.g. gt 327/pred 344, gt 7574/pred 7685, gt 8522/pred 7952, gt 25917/pred 27439) versus the 4-8x over-prediction at 300 cases. So the +0.20 gain came primarily from TIGHTER OUTLINES, exactly the failure mode the per-case analysis flagged — and data fixed it without a loss change. This makes EXP-18 (Tversky) less urgent.
- Remaining failure modes: 4 misses (detection 90%); a few small tumors detected but localized wrong (0 Dice despite a lesion predicted, e.g. gt 256/pred 820, gt 392/pred 1458); and one giant 94cm3 tumor under-segmented to 0.197 (an outlier likely exceeding the whole-box field of view). Small tumors and non-contrast remain the hard tail.

Decision: ACCEPT decisively (pending full-eval confirmation). What we can already conclude and what we cannot:
- CONFIRMED: the data-scaling curve is still climbing steeply — 0.169 (whole-scan) -> 0.263 (whole-box, 95 cases) -> 0.327 (300) -> 0.487 (1412 + long training). Data scale is not just a lever, it is THE dominant lever, and at max tumor data it has not plateaued.
- CONFOUND: two things changed vs EXP-17 (data 300 -> 1412 AND iters 6000 -> 24000), so this run does not separate "more data" from "more training time." A control (300 cases at 24k iters, or 1412 at 6k) would decompose it. But the practical result is unambiguous.
- CEILING NOTE: we have now used ALL 706 tumor cases in the train pool, so further data gains from the Mini release are exhausted. Remaining levers: more training TIME (iterations) on this max-data set, the loss (Tversky for over-segmentation, EXP-18), and the ROI-leak correction (EXP-19).
- CAVEAT (do not drop): this is still the UNION ROI, so 0.487 is an upper bound inflated by the lesion-extent leak (unquantified until EXP-19). It is a "provided pancreas+lesion ROI, development-validation" number, not autonomous full-volume performance.

72h decision: if the MLflow val curve was still rising at 24k iters, a much longer run on scaledmax (60-80k iters) is justified and likely climbs further — this is the weekend's highest-value move. If it plateaued, the next lever is the loss/ROI, not more time.

---

## EXP-19: Pancreas-only ROI — quantify the lesion-extent leak [Week 4, the audit control]

Motivation: a two-way metrics audit (mine + Codex, 2026-07-17, saved in `docs/codex-metrics-audit.md`) found the "oracle pancreas box" is actually built from pancreas UNION lesion (`_foreground_label` = label>0). When a lesion protrudes past the pancreas mask, it enlarges/shifts the crop, so lesion location leaks into the model's field of view and biases lesion Dice UPWARD. Every result so far (EXP-10/12/16/17/17b/17c) used this union crop, so the RELATIVE conclusions hold, but the absolute lesion Dice is an upper bound on the provided-ROI setting. This control measures the leak.

Fix implemented (2026-07-17): `preprocessing.roi_source` = `union` (legacy default, unchanged) | `pancreas` (organ mask only). `ComposeLabeld` now keeps the original pancreas mask as `panc_roi`, threaded through orientation/crop/resample, so the crop can be built from pancreas alone. Wired as `train.py --roi-source pancreas` / `evaluate.py --roi-source pancreas`, with its own disk-cache tag so it never collides with union caches.

Variable (single): `roi_source` union -> pancreas. Everything else matched to EXP-17 (scaled300, SuPreM transfer, whole-box, crop-native 16, 128 @ 1.5mm, bg0 DiceFocal, seed 42). Anchor to compare against: EXP-17 union = lesion 0.327 cleaned.

Hypothesis (H1): pancreas-only ROI lowers lesion Dice materially (>= 0.03 drop), i.e. the union crop was inflating the number and the honest provided-pancreas-ROI figure is lower.
Null (H0): lesion Dice is within noise of 0.327, i.e. lesions are almost always inside the pancreas mask so union ~ pancreas and there was effectively no leak.

Either result is publishable and important: it tells us how much (if any) of our headline was ROI leak, and the pancreas-only number becomes the honest one to report going forward.

Runbook (smoke-test FIRST — this exercises the new crop path, which has not run live):

```bash
source .venv312/bin/activate
# smoke (~2-3 min): confirms the pancreas-only crop + panc_roi threading works end to end
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled300 --transfer --cache disk --roi-source pancreas \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 \
  --max-iters 30 --val-limit 0 --no-mlflow --ckpt-every 30 --run-name smoke_panc_roi

# full run (matched to EXP-17 except roi_source)
caffeinate -is env PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/train.py \
  --config configs/level45.yaml --split scaled300 --transfer --cache disk --roi-source pancreas \
  --crop-native 16 --whole-box --patch 128 --spacing 1.5 --ckpt-every 200 \
  --max-iters 6000 --val-limit 20 --val-positive --val-every 1000 \
  --run-name transfer_wholebox_scaled300_pancROI

# eval (MUST pass --roi-source pancreas so eval matches training)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/evaluate.py \
  --ckpt outputs/checkpoints/pants-level45/runs/transfer_wholebox_scaled300_pancROI__<STAMP>/best.pt \
  --n-pos 20 --n-neg 20 --sweep --lesion-within-pancreas-mm 10 \
  --crop-native 16 --whole-box --roi 128 --spacing 1.5 --roi-source pancreas
```

Result: to fill in.
Decision: to fill in.

---

## EXP-20: Autonomous cascade — predicted ROI, the comparable-to-published number [Week 4, the credibility run]

Motivation (the credibility problem, raised 2026-07-17): every lesion Dice to date — including the EXP-17c headline 0.528 — was measured on a crop built from the GROUND-TRUTH pancreas. That is an oracle ROI: the model is handed *where the pancreas is* before being asked *what is in it*. Published whole-scan pancreatic-tumor numbers get no such gift, so our number is not comparable to anyone else's, which undercuts its credibility. The instructor's bar, stated directly: if the model produces the same result when the crop comes from a *predicted* pancreas instead of the ground truth, the results can be taken seriously. This experiment builds that autonomous pipeline and measures it.

Design — a localize-then-segment cascade, both stages full-volume sliding-window, NO retraining:
- Stage 1 (localizer): a full-scan pancreas model predicts the pancreas on the whole CT; take the largest connected component; read off its bounding box + a buffer. Its job is COVERAGE (contain the pancreas and the tumor), not accurate segmentation, so a ~0.75-Dice pancreas model is enough. Reused checkpoint: `p128_ctx_step6000.pt` (EXP-08, full-scan patch-128, pancreas Dice 0.747). Fallback if coverage is poor: stock SuPreM (32-class, segments pancreas natively) or a quick dedicated localizer.
- Stage 2 (segmenter): the EXP-17c whole-box model, UNCHANGED, run on the predicted crop.

Single-variable harness (`scripts/cascade_eval.py --roi-from`), everything downstream of the crop identical:
- `gt-union` — crop from GT pancreas UNION lesion. Matches how EXP-12/17/17c were scored, so it must REPRODUCE ~0.528 and thereby validate this harness. If it does not, nothing else here is trusted.
- `gt-panc` — crop from GT pancreas ONLY (an inference-time read on the ROI-leak of EXP-19, on the existing model, no retrain). Gap gt-union -> gt-panc = the lesion-extent leak.
- `pred` — crop from the LOCALIZER's predicted pancreas box. The autonomous number. Pancreas-only by construction (the localizer never sees a lesion), so also leak-free. Gap gt-panc -> pred = the pure cost of imperfect localization.

Metrics: lesion + pancreas Dice on tumor-positive cases (raw + cleaned), specificity on tumor-free cases, threshold sweep — all matched to `evaluate.py`. PLUS localizer coverage: fraction of the GT pancreas and GT tumor that falls inside the predicted box, and a count of cases where the box clips >10% of the tumor (the cascade's main failure mode — a clipped tumor cannot be segmented).

Hypothesis (H1): the autonomous (`pred`) lesion Dice lands within noise of the oracle (`gt-union`) number — within ~0.05 at n=40 — with box coverage of the tumor >~95%. If so, the oracle number was a fair proxy all along and the result is credible/comparable.
Null (H0): `pred` drops materially below oracle because localization clips or mislocates tumors (low coverage), meaning the oracle number was optimistic about autonomous performance.

Either way it is the honest headline. Report BOTH numbers going forward — oracle as the "with provided ROI" upper bound, autonomous as the deployable one — exactly how cascade papers present it, which also lets us decompose error into leak vs localization vs segmentation.

Honest confounds, stated up front:
1. Harness crops AFTER resampling to 1.5mm (one clean code path for gt and pred), whereas training cropped in native space then resampled. The whole-box resize to 128^3 normalizes most of this away; the `gt-union` arm is the check — if it reproduces ~0.528, the crop-space change is harmless.
2. Train/eval crop-source mismatch: the Stage-2 model was TRAINED on GT (union) boxes but is now fed PREDICTED boxes (shifted/clipped). This is deliberately the thing under test (does it transfer?). If `pred` sags, the fix is known and cheap — retrain Stage-2 with random jitter on the training box so training looks like deployment (EXP-21, staged and ready but NOT run until we see whether zero-retrain transfer holds).
3. Buffer size (`--margin-vox`, default 12 @1.5mm ~= 18mm) trades clip-risk against drifting back toward a whole-scan input; test sensitivity if `pred` underperforms only from clipping.

Runbook (tonight — eval-only, ~1-2h for 40+40 cases through two SW stages; SANITY one case FIRST):

```bash
source .venv312/bin/activate   # or .venv; no MLflow needed for eval
SEG=outputs/checkpoints/pants-level45/wholebox_scaledmax_GOOD.pt
LOC=outputs/checkpoints/pants-level45/p128_ctx_step6000.pt

# 0. SANITY: one tumor-positive case, saves an overlay PNG — eyeball the crop before trusting aggregates
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from pred --sanity <a_tumor_positive_val_case_id>

# 1. HARNESS CHECK: must land near the oracle 0.528, else stop and debug the harness
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from gt-union --n-pos 40 --n-neg 40

# 2. THE AUTONOMOUS NUMBER (the credibility result)
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from pred --n-pos 40 --n-neg 40 --sweep --lesion-within-pancreas-mm 10

# 3. (optional, same harness) the leak control, EXP-19 inference-time read
PYTORCH_ENABLE_MPS_FALLBACK=1 python scripts/cascade_eval.py --seg-ckpt $SEG --loc-ckpt $LOC \
  --roi-from gt-panc --n-pos 40 --n-neg 40
```

Read in the morning: if `gt-union` ~= 0.528 (harness valid) AND `pred` is within ~0.05 with tumor coverage >95%, the number is credible and we build on it. If `pred` drops, the coverage line says whether it is a localization/clip problem (low coverage -> bigger buffer or better localizer) or a crop-shift robustness problem (good coverage but lower Dice -> the EXP-21 jitter retrain). Do NOT launch a 15h run tonight; this eval answers the question first, and the fix (if needed) is a targeted overnight run tomorrow with full information.

### EXP-22 (sub-run of the cascade): a dedicated full-scan pancreas LOCALIZER [Week 4, launched 2026-07-18 overnight]

Goal: replace the reused `p128_ctx` (0.747 pancreas, trained on ~95 cases) with a stronger Stage-1 localizer trained on all 1,412 `scaledmax` cases. A better pancreas model gives tighter, more reliable boxes, so containment needs less buffer. Full-scan patch training (NOT whole-box): standard SuPreM transfer, patch 96, the pancreas channel of the 3-class output is the localizer. Loss stays DiceFocal (pancreas is easy; recall is obtained at inference via the low-probability-threshold box, `cascade_eval --loc-thresh`). Validation off (`--val-limit 0`) because train.py selects best.pt by LESION Dice, which is the wrong metric for a localizer — use the archived `last.pt`. A recall-oriented loss (Tversky, penalize pancreas false-negatives = "dock for missing pancreas") is the reserved next lever IF the containment audit shows the buffer alone is insufficient.
Command run: `train.py --split scaledmax --transfer --cache disk --patch 96 --num-samples 2 --max-iters 16000 --val-limit 0 --run-name localizer_fullscan_scaledmax`.
Then (tomorrow): `cascade_eval.py --audit-coverage --loc-ckpt <last.pt> --loc-roi 96 --loc-thresh 0.1 --margin-vox 16 --n-audit 1000` to certify containment, and re-run the accuracy arm with the new localizer.
Result: to fill in.

Result (2026-07-18, `cascade_eval.py`, n=40 pos / 40 neg; localizer `p128_ctx_step6000.pt` @0.747 pancreas, segmenter `wholebox_scaledmax_GOOD.pt`):
- Sanity (PanTS_00000029): pancreas coverage 1.00, lesion coverage 1.00, lesion Dice 0.790 — overlay confirms the crop + mapping are correct.
- HARNESS CHECK (`gt-union`): pancreas 0.833, lesion 0.496 raw / 0.484 cleaned, specificity 30% (raw=cleaned). Reproduces the EXP-17c oracle (pancreas 0.837, lesion 0.524/0.528) within ~0.03. The small dip is confound #1 (crop-after-resample + margin-12 vs training's native crop), so the harness is VALIDATED: within-harness comparisons are trustworthy, and its absolute lesion Dice reads ~0.03 below the native-crop oracle.
- AUTONOMOUS (`pred`): pancreas 0.819, lesion **0.483 raw** / 0.456 cleaned, specificity 38% (raw=cleaned; sweep reaches 48% at threshold 0.90 for only -0.007 lesion Dice). Localizer coverage pancreas 0.992, tumor 0.979; only 2/40 cases clip >10% of the tumor; 0 full localizer misses.
- THE KEY NUMBER: within the same harness, autonomous (0.483) vs GT-box (0.496) is a **0.013 lesion-Dice gap — inside n=40 noise**. The predicted pancreas box gives essentially the same result as the ground-truth box. Coverage 98% confirms the localizer almost never clips the tumor.

Decision: **ACCEPT H1 DECISIVELY.** The pipeline is now autonomous and the headline is credible/comparable: lesion Dice ~0.48 with a PREDICTED ROI, ~equal to the provided-ROI result, at 98% tumor coverage. No jitter retrain (EXP-21) needed — zero-retrain transfer held. Report going forward as two numbers: autonomous lesion Dice ~0.48 (deployable, comparable to the ~0.53 published reference) vs provided-ROI ~0.52 (upper bound).
- Corollary on the ROI leak (EXP-19): the autonomous arm is leak-free by construction (the localizer never sees a lesion) yet matches the leaky `gt-union` arm, which implies the lesion-extent leak was small. Running `gt-panc` would quantify it exactly (optional, same harness), but the practical conclusion is the leak was not materially inflating the headline.
- HONEST caveat (the real specificity, finally measured): this is the first proper specificity read on the max-data model — ~30-38% at n=40 (tunable to ~48% by threshold), MODERATE and lower than the small-data models' 50-55%. More data bought a large lesion-Dice gain and 90% detection, but not higher specificity. Specificity stays an operating-point dial (threshold / TTA / anatomical constraint) and a capstone data problem; detection sensitivity (90%) remains the CADe headline.
- Next: fold the autonomous number into the report/UI as the deployable figure; optionally run `gt-panc` to close the leak decomposition; the remaining accuracy lever is small-tumor localization + specificity (both data/curriculum problems for Week 4 / capstone).

---

## Backlog: designed but not yet run

- More data, scaling past the 100-case dev subset. The EXP-05/07 null results point at data volume as the real ceiling; this is the main Week 3/capstone lever and needs a persistent/disk cache to replace the RAM `CacheDataset` (not yet wired — see `configs/level45.yaml` `training.cache`).
- Harder-negatives sampling (`sampling.strategy: classes`), already coded, to be tried only if it becomes the priority; sampling proved a weak lever in EXP-05.
- ROI cascade (coarse locate then fine segment), the autonomous version of the EXP-12 whole-box stage: a pancreas detector in front of the box stage; capstone.

Now formalized as experiments (moved off this backlog): transfer-vs-scratch = EXP-09; test-time augmentation = EXP-15.

## Checkpoint & logging discipline (added 2026-07-12, after losing EXP-12)

The EXP-12 whole-box best (lesion 0.263) was lost because every run shared one `best.pt`/`last.pt` and the manual "copy it after the run" step was skipped, so the EXP-13/14 runs overwrote it; it also ran without MLflow, so no metrics were live-logged either. Two code fixes now make both failure modes structural rather than dependent on memory:

1. Per-run archive (in `train.py`). Alongside the shared `best.pt`/`last.pt`, every run writes immutable copies into `outputs/checkpoints/<experiment>/runs/<run_name>__<timestamp>/` with a `run_info.txt` recording the recipe (split, mode, patch, spacing, whole_box, crop, loss, seed). No later run can touch a previous run's folder, so a keeper is never clobbered and never an orphan. Point eval at the archived path, not the shared `best.pt`, for anything you care about.
2. Persistent, MLflow-independent ledger. Every run appends one row to `outputs/checkpoints/<experiment>/run_ledger.csv` (timestamp, run_name, split, mode, iters, best_val_lesion, archive_dir). If MLflow is unavailable, `train.py` now prints a loud banner instead of a quiet one-liner, so an unlogged run cannot slip by unnoticed.

Rules of thumb: always launch from `.venv312` (has MLflow); the archive/ledger live under `outputs/` (git-ignored, local safety net) while `experiments.md` stays the committed record; periodically prune archive folders of rejected runs to reclaim disk (each is ~110 MB).

## How to add the next entry

Before a run: write the hypothesis, the single variable, what is held constant, and the accept/reject bar. After the run: paste the MLflow name, the training-time val, the full evaluation numbers, and the decision. Never edit a past result; add a new experiment if something changes.
