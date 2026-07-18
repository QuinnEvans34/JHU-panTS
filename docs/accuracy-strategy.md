# Accuracy Strategy: how do we raise lesion Dice?

Working doc for the deep-dive after tonight's run. The question is narrow and specific: what change raises LESION Dice (segmentation accuracy on tumor-positive cases), as distinct from specificity, which the whole-box change largely solved on its own. This doc pre-loads what we already know so the session is about deciding, not re-deriving.

## Where we are

- Current best: EXP-12 whole-box, lesion Dice 0.263 (raw), pancreas 0.807, specificity 55%. Oracle ROI ("provided pancreas box").
- Reference points: dedicated pancreatic-tumor segmentation SOTA is roughly 0.53 lesion Dice (trained on thousands of scans). My pre-registered course target is 0.35 to 0.50. So the gap to close is about +0.10 to +0.24 lesion Dice.
- The through-line of every result so far: the two pure training knobs (sampling, loss-bg) were nulls, and the thing that moved the needle was structural (whole-organ context). That is strong evidence the ceiling is data scale, not hyperparameters.

## Ruled out for accuracy (do not spend the session here)

- Patch sampling ratio (EXP-05): null. Aggressive vs 1:1 identical.
- Loss include-background (EXP-07): rejected. Hurt lesion Dice.
- Bigger patch / more context at whole-scan (EXP-08): accuracy null; it only traded sensitivity for specificity.

These are settled. Revisiting them is not a good use of Week 4.

## What worked (build on these)

- Whole-box ROI (EXP-12): the current base. Whole-organ context in one cube.
- Oracle ROI + finer spacing (EXP-10): +0.028 lesion Dice, the hint that resolution/focus matters once field of view is guaranteed.

## Candidate levers for Week 4 (the menu to decide from)

Each lever below has: the hypothesis, expected value, cost/risk, whether it is transfer-safe (does not break the SuPreM checkpoint load), and a sketch of the single-variable test. Ranked by my current read of expected value per unit effort; the session decides the actual order.

### A. Scale up the tumor data (the big lever)
- Hypothesis: every null points here. Going from 95 dev cases to several hundred (especially more tumor-positive cases) raises lesion Dice more than any recipe change.
- Expected value: highest. Cost: highest too. Needs a persistent/disk cache to replace the RAM `CacheDataset` (the dataset currently caches everything in memory; that does not scale past ~100 cases). Then longer runs.
- Transfer-safe: yes. Test: same whole-box recipe, larger training split, matched val, compare lesion Dice.
- Open question: how many more tumor cases can the drive/laptop realistically train on in a Week 4 timeframe, and is the disk-cache build worth it now vs a smaller intermediate bump (e.g. 200 cases)?

### B. Resolution inside the whole box
- Hypothesis: EXP-10 suggested finer effective resolution helps once the organ is fully in view. The whole box is currently 128 cube at 1.5mm (192mm span). A larger cube at the same span (finer mm/voxel), or a tighter span, gives the tumor more voxels.
- Expected value: medium, and it is the cleanest untested accuracy axis. Cost: memory/compute (bigger cube on MPS). Risk: MPS out-of-memory; may need to drop batch/samples.
- Transfer-safe: yes (field of view and spacing are safe; network width is not). Test: whole-box at e.g. 160 or 192 cube, or 1.25mm, single variable vs EXP-12, matched n.

### C. Loss shape (not the bg flip — that failed)
- Hypothesis: the objective can still be tuned for recall of the tiny lesion without the bg change that failed. Untried: class weights [1,1,3], Tversky / focal-Tversky (explicitly favors recall over precision), boundary/surface losses, gamma tuning.
- Expected value: low-to-medium and cheap. Risk: can trade specificity back. Transfer-safe: yes. Test: one loss variant at a time on the whole-box base.

### D. Anatomy-context channels
- Hypothesis: PanTS reports richer anatomy context adds ~10pp tumor Dice. Add a few neighbor-structure masks (duodenum, vessels) as extra input channels.
- Expected value: potentially high (their strongest reported lever). Cost/risk: adding input channels BREAKS the SuPreM single-channel load, so this is not transfer-safe as-is; needs a channel-adapter or a from-scratch arm. Realistically a capstone item, or a careful Week 4 stretch.

### E. Test-time augmentation (EXP-15)
- Hypothesis: flip averaging steadies output for free. Expected value: small. Cost: eval-only, already coded. Pending tonight's result.

### F. Longer / better-scheduled training
- Hypothesis: 6000 iters on 95 cases may under-train; check whether the val lesion curve had plateaued or was still climbing. If still climbing, more iters is a free-ish gain.
- Expected value: unknown until we read the curve. Cost: low. Test: extend the best run to 10-12k iters, watch for continued val improvement vs overfitting.

### G. Post-processing to recover lesion Dice (not just specificity)
- Hypothesis: the largest-CC step can delete real secondary lesion voxels; relaxing it when the lesion sits inside the predicted pancreas may recover lesion Dice. Noted in implementation-plan as a refinement.
- Expected value: small, cheap, eval-only. Transfer-safe: yes.

## A decision framework for the session

1. Confirm the target: are we optimizing lesion Dice for the course deliverable, or a sensitivity/specificity operating point for the CADe story? (They pull in slightly different directions; contrast-phase EXP-14 is the dial for the latter.)
2. Decide the one or two levers to actually run in Week 4, given each is a multi-hour overnight run and we get roughly one clean run per night.
3. My current recommendation to react to: (B) resolution-inside-the-box is the best single-variable accuracy test we can run without new infrastructure, and (A) data scale is the real ceiling but costs the disk-cache build. A reasonable Week 4 plan is B first (fast, clean, presentation-friendly), then commit to A (disk cache + more data) as the capstone-spanning push. C/E/F/G are cheap add-ons; D is capstone.
4. Keep the guardrails: single variable, pre-registered bar, matched-n eval, honest confounds, and archive every keeper (now automatic).

## Decisions (2026-07-15, after EXP-16)

EXP-16 (resolution, matched FOV) was a REJECT on lesion Dice (0.248 raw / 0.228 cleaned vs 0.263, pancreas rose to 0.805 but the tumor did not move). That makes four independent recipe nulls for lesion accuracy: sampling (EXP-05), loss (EXP-07), context (EXP-08), resolution (EXP-16). Conclusion: lesion Dice ~0.26 is the honest ceiling at 95 cases; the ceiling is DATA, not recipe.

- Target metric priority: lesion Dice (accuracy), pursued via data scale. The CADe operating-point story (whole-box, contrast phase, TTA, threshold) is the strong secondary narrative and does not need more experiments.
- Disk-cache build: IN SCOPE, chosen as the Week 4 lever. It is the one lever the evidence says will move lesion Dice, and it is the capstone bridge.
- Lever that runs first in Week 4: scale the tumor data past 95 cases, which requires the persistent/disk cache (below).
- Pre-registered bar (to hold to): a scaled run (target 300-500 cases, tumor-enriched) ACCEPTS if lesion Dice clears 0.30 at n=20 on the same val set, a clear move off the 0.26 ceiling. Report honestly if it does not.
- Val-curve read: EXP-12 and EXP-16 both peak early (best checkpoint around step 2000-3000) then overfit on 95 cases, which is itself consistent with a data-limited regime, more data should push the peak later and higher.

## Disk-cache build plan (the Week 4 enabler)

- Problem: `get_dataset` uses `CacheDataset(cache_rate=1.0)` = every transformed volume held in RAM, which caps at ~100 cases.
- Fix: add a `PersistentDataset` branch that caches the deterministic transform prefix (load, resample, window, crop, whole-box) to disk once, then applies the cheap random augments on the fly. MONAI caches up to the first Randomizable transform automatically, which lines up with our pipeline.
- Wiring: `training.cache: disk | ram | none` in the config, plus a `cache_dir` on the internal SSD (fast), never the external drive.
- Data: a new tumor-enriched split (e.g. dev_subset_300) drawn from the 1,033 tumor cases in the manifest.
- Risk: one-time cache-build time, longer epochs, and whether the payoff lands inside a single week vs spilling into capstone.
