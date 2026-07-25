# SPEC v4 — EXP-26: Anatomy-Aware AUXILIARY Supervision (+ pancreas label fix)

Status: DRAFT v4 for final review. v1→REVISE (10), v2→REVISE (4 holes), v3→REVISE (5 pts). v4 folds in all v3-review points. Codex said "after those revisions, the spec is ready to implement." v4 → confirm APPROVE → code → code-review → run. Do not implement until approved.

**Changelog v3 → v4:**
- **Dropped the "faithful MONAI-DiceFocal equivalent" claim** (it was wrong: MONAI `DiceFocalLoss(softmax=True)` softmaxes the Dice term only; its focal term is **sigmoid**, channel-wise). The v4 primary loss is a **deliberate probability-based reformulation** required by differentiable class collapse. **No causal comparison to EXP-24's 0.415** — 26A is THE matched baseline. Unit tests rewritten accordingly.
- **Auxiliary loss fully specified:** masked per-class Dice, independent then equal-averaged, empty-class exclusion, all-absent → differentiable zero, **no renormalization** of H/B/T within the mask, `smooth_nr=smooth_dr=1e-5`, `squared_pred=False`, `batch=False`.
- **All retained subregion masks pass through EVERY spatial transform** (incl. `SpatialPadd`, `ResizeWithPadOrCropd`, `RandFlipd`, `RandRotate90d`); renamed to "non-destructively retained source-derived masks"; intensity transforms hit the CT only.
- **val20 and report40 are now DISJOINT** (fully held-out reporting cohort).
- **Step-zero weight-hash verification, explicit `torch.Generator` DataLoader seed, `--train-ids` leakage check, λ=0 computes-then-zeros the aux branch**, + committed cohort README.

---

## 1. Objective
Raise **lesion Dice** by adding **auxiliary anatomical supervision** (pancreas head/body/tail) to the whole-box SegResNet+SuPreM model WITHOUT diluting the primary lesion objective, and bundle the prerequisite **pancreas label fix** (pancreas = head∪body∪tail). The measured intervention is a single scalar: the auxiliary-loss weight `λ_anat`.

## 2. Honest expectations & framing
Subregions supply within-pancreas position, not surrounding-organ context (PanTS's +10.3pp came from neighbor organs). **Target: +0.01–0.04 lesion Dice, or null.** The neighbor-organ + larger-crop version is EXP-27. Accept only on a positive **paired 26B−26A** lesion-Dice mean difference with a bootstrap CI excluding 0. **We make no causal comparison to EXP-24's 0.415** — that number used a different focal implementation and different pancreas GT (combined mask), and is historical context only. The clean claim this experiment can support is: "under an identical 5-channel whole-box model differing only in `λ_anat`, auxiliary head/body/tail supervision changes lesion Dice by X (paired CI …)."

## 3. Design — two matched arms, identical except `λ_anat`
Both arms: **5-channel output** (0=bg, 1=head, 2=body, 3=tail, 4=lesion), same SuPreM-initialized head, same cases/order, ROI, resolver, seed, augmentation stream, LR schedule, optimizer STEPS (24000), validation schedule, checkpoint-selection IDs, loss code.
- **26A (control):** `λ_anat = 0`. The 3 pancreas channels are permutation-symmetric, trained only through their summed pancreas probability. The aux branch is still **computed and then multiplied by zero** (no separate code path).
- **26B (treatment):** `λ_anat = 0.3`. Identical; the aux loss forces channels 1/2/3 to mean head/body/tail.
Causal comparison = paired **26B − 26A** per-case lesion Dice.

## 4. Losses (exact, differentiable, no double-softmax)
Compute the 5-channel **softmax probabilities once**: `p = softmax(logits)`, [B,5,...].

**Collapsed 3-class probabilities (differentiable):** `p_bg = p[:,0]`, `p_panc = p[:,1]+p[:,2]+p[:,3]`, `p_lesion = p[:,4]`. Sum to 1. Gradients reach all H/B/T logits through `p_panc`.

**Primary loss (both arms):** on collapsed probs `[p_bg,p_panc,p_lesion]` vs collapsed 3-class one-hot GT `[bg, panc=H∪B∪T, lesion]` (lesion wins overlap):
- **Soft Dice** directly on the probabilities (bg excluded, `smooth_nr=smooth_dr=1e-5`, `squared_pred=False`, `batch=False`).
- **Probability-based focal CE** `-(1-p_c)^γ · log(clamp(p_c, ε, 1))` at each voxel's true collapsed class `c` (bg excluded, `γ=2.0`, `ε=1e-7`, mean reduction).
- `primary = λ_dice·softDice + λ_focal·focal`, `λ_dice=λ_focal=1`.
- **This is a deliberate probability-based reformulation, NOT MONAI-DiceFocal-equivalent.** It is the same primary loss for BOTH arms, so the 26B−26A comparison is valid regardless.
- **Unit tests:** (a) 5-class softmax collapse sums to 1; (b) collapsed loss equals a hand-computed 3-probability reference; (c) gradients reach all H/B/T logits via `p_panc`; (d) `λ_anat=0` yields exactly `primary`; (e) numerical stability at p→0 and p→1.

**Auxiliary loss (weighted by `λ_anat`; computed both arms):** masked per-class Dice teaching head/body/tail position, from **non-destructively retained source masks**.
- Domain mask `M = (H∪B∪T) AND NOT lesion`.
- For each k∈{head,body,tail}: soft Dice between `p[:,k]` and the boolean target, **restricted to `M`** (voxels outside `M` excluded from num and denom). **Do NOT renormalize** `p[:,k]` within `M` — use the raw 5-class softmax prob, so assigning a pancreas voxel to bg/lesion is still penalized. `smooth_nr=smooth_dr=1e-5`, `squared_pred=False`, `batch=False`.
- **Reduction:** compute the three Dice losses independently, average **equally**. If a subregion target is **empty** for a sample, exclude that class/sample term from the mean (do not let smoothing define it). If ALL aux targets are unavailable for a sample (should be prevented by the audit), return a **differentiable zero**.
- **Total = primary + λ_anat · auxiliary.** `λ_anat` pre-registered (0.3), **finalized before either full run**.
- **Smoke-scale check (numerical, pre-run):** log unweighted `primary` and `auxiliary` magnitudes + grad norms for ~100 steps; if aux is naturally >~2× primary, reconsider `λ_anat` and **document the change before both arms start**. Must not be tuned on outcomes or applied to only one arm.

## 5. Label construction — three distinct objects, all spatially aligned

> **v4 → implementation note (flagged for the code review, docs/exp26-code-review-handoff.md):**
> the code realizes the three objects from a SINGLE mutually-exclusive 5-class integer `label`
> map (head=1, body=2, tail=3, lesion=4-wins) carried through the pipeline, deriving the primary
> collapse target, the aux domain `M`, and per-subregion targets inside the loss. This is lossless
> for the aux domain when head/body/tail mutual overlap is negligible (audit-gated), is better-
> defined than overlapping booleans (softmax cannot satisfy p_head=p_body=1), and minimizes the
> alignment surface. Codex to confirm or request separate mask keys.

Per case, on the common processed grid (all three follow the SAME spatial pipeline as the image):
1. **Non-destructively retained source-derived masks:** `H, B, T, lesion` — each passes through orientation, native crop, **nearest-neighbor** spacing, `SpatialPadd`, whole-box `ResizeWithPadOrCropd`, `RandFlipd`, `RandRotate90d` (identical params/RNG to the image); re-boolean after NN steps. Intensity transforms apply to the **CT only**. Used for the aux loss + collapse GT.
2. **Mutually-exclusive segmentation TARGET (for argmax/metrics):** head=1, body=2, tail=3 (audit overlap policy), lesion=4 last (wins).
3. **Primary collapsed GT:** `bg / pancreas=(H∪B∪T) / lesion` (lesion wins). Pancreas GT is the UNION, independent of destructive painting.
`panc_roi = H∪B∪T` (crop source — subregions only, no lesion → no lesion-extent leakage).

## 6. Pre-implementation DATA AUDIT (step 0 — EVERY used case)
`scripts/audit_subregions.py` over the exact **train + val20 + report40 + report40_neg** cohorts: pairwise H/B/T overlap; `H∪B∪T` vs valid combined-pancreas gap; lesion voxels outside `H∪B∪T`; empty/missing subregion masks; `H∪B∪T` volume outliers (both guards); **affine/shape agreement** per case. Output fixes the H/B/T overlap policy and the exclusion list. A geometry/missing-mask failure on ANY evaluated case invalidates pairing → all cohorts must pass; any excluded case is excluded from BOTH arms.

## 7. Frozen cohorts (committed / immutable / DISJOINT)
Generate + **commit** ordered ID files to `configs/cohorts/exp26/`: `train.txt`, `val20.txt`, `report40.txt`, `report40_neg.txt`, plus a **README** recording: construction rules, source parent split, exclusions + reasons, creation date, per-file SHA-256, pairwise-intersection assertions, lesion status/counts. Required relationships (asserted at build + at train startup):
- `train ∩ val20 = ∅`, `train ∩ report40 = ∅`, **`val20 ∩ report40 = ∅`**, `report40_neg` disjoint from all positive cohorts, every cohort within the original train/val partition and **outside official test**.
Store each file's hash in checkpoint metadata. Both arms consume the SAME files. Not `outputs/splits/` (git-ignored).

## 8. New CLI (exact semantics)
- `--label-mode {pancreas_lesion, anatomy5}` — output channels + target composer.
- `--pancreas-resolver {combined, hbt_union}` — DECOUPLED from label-mode; both arms `hbt_union`.
- `--lambda-anat FLOAT` — aux weight (26A=0, 26B=0.3).
- `--train-ids FILE`, `--val-ids FILE`, `--report-ids FILE`, `--neg-ids FILE` — explicit frozen cohorts; **bypass** `--val-positive`/`--val-limit`/manifest re-filter; fix exact ordered lists. The **leakage guard reads `--train-ids`** and asserts disjointness vs val/report/neg/official-test.

## 9. Evaluation, selection & stats
- Shared helpers everywhere: `collapse_hard(argmax)` {1,2,3}→panc,{4}→lesion; `collapse_probs(p)` `P_panc=p1+p2+p3`, `P_lesion=p4`.
- `best.pt` on **collapsed hard-argmax lesion Dice** on `val20`.
- Report on the **disjoint** `report40`: collapsed lesion Dice (headline) + collapsed pancreas Dice (flag: pancreas GT changed) + per-subregion Dice (bonus). Specificity on `report40_neg` via `collapse_probs` + sweep.
- **Paired stats (primary):** per-case 26B−26A lesion-Dice diff; **mean difference + bootstrap 95% CI** = primary inference; median/IQR/win-loss-tie (tolerance-based ties) = descriptive.

## 10. Checkpoint metadata + logging
`extra`: `label_mode`, `pancreas_resolver`, `out_channels`, ordered `class_names`, `collapse_map`, `roi_source`, `lambda_anat`, SHA-256 of the **model-only init checkpoint**, and hashes of **train/val20/report40/report40_neg**. Eval verifies vs CLI/config, **aborts on mismatch**. `run_info.txt`/`run_ledger.csv`/MLflow log `label_mode`, `pancreas_resolver`, `out_channels`, `lambda_anat`.

## 11. Code-change inventory (review target)
1. `configs/level45.yaml`: `label_mode`, `pancreas_resolver`, `out_channels` (5), `lambda_anat`, class list.
2. `src/data/dataset.py`: `build_records` API takes resolver + required-mask keys (decoupled from label_mode); emit H/B/T/lesion paths; update **every caller** (`train.py`, `evaluate.py`, `analyze_cases.py`, `cascade_eval.py`, `sanity_check_case.py`). `_cache_tag` gets a versioned resolver+class-map fingerprint.
3. `src/data/transforms.py`: `IMAGE_MASK_KEYS` mode-derived; retained subregion masks threaded through **every spatial transform** (§5.1); new composer producing the three §5 objects; `panc_roi=H∪B∪T`; legacy 3-class path preserved.
4. `src/training/losses.py`: custom primary (§4) + masked auxiliary (§4); config `lambda_anat`; both computed always (26A ×0); the §4 unit tests.
5. `src/training/metrics.py` `DiceEvaluator`: explicit class names; collapsed pancreas/lesion accumulator for selection + reporting.
6. `scripts/evaluate.py`, `analyze_cases.py`, `cascade_eval.py`, `export_case.py`, overlay/mesh/confidence code: replace `pred==2`/`probs[2]` with shared collapse helpers; repo-wide class-ID literal search. `postprocess.py` may stay 3-class IF callers collapse first (explicit boundary).
7. `scripts/train.py`: best.pt on collapsed lesion Dice; frozen-cohort CLI; metadata + logging; leakage guard extended to `--train-ids`; **step-0 weight-hash verify** (both arms byte-identical); **explicit `torch.Generator`** for DataLoader shuffle; identical worker count; log first N case IDs + aug seeds.
8. `src/models/segresnet.py`: build a single **model-only 5-channel SuPreM-init checkpoint**, record SHA-256; smoke test asserting only the final head weight+bias are re-init on load (reject other mismatches). Both arms load THOSE exact weights.
9. `scripts/audit_subregions.py` (§6); a helper to build + hash + README the §7 cohorts.
10. `scripts/inspect_checkpoint.py`: class-count-aware reporting (not hard-coded "re-init to 3").

## 12. Run-equivalence checklist (26A vs 26B differ ONLY in λ_anat)
Same: 5-channel init head from ONE hashed model-only checkpoint, byte-identical at step 0 · ordered examples + explicit-generator shuffle stream · deterministic cache inputs (hash-check a few preprocessed cases) · augmentation RNG stream (log first N IDs+seeds) · validation schedule + exact `val20`/`report40`/`report40_neg` IDs · loss code, aux computed both arms (λ only differs) · target composer + retained masks + exclusion logic · optimizer STEPS · selection rule · missing-mask handling (excluded from BOTH). Do **not** resume only one arm (restart or apply identically to both). `λ=0.3` finalized before both runs.

## 13. Risks & mitigations
Lesion dilution → primary-collapsed loss (§4). Confound → identical 5-ch heads + one hashed init + λ-only diff (§3,§12). Double-softmax → custom loss on collapsed probs (§4). Wrong focal-equivalence assumption → claim dropped; 26A is the baseline (§2,§4). Aux over wrong domain → masked to non-lesion pancreas voxels, no renorm (§4). Mask misalignment → all masks through every spatial transform (§5.1). Stale cache → resolver+class-map fingerprint (§11.2). Silent mislabel → explicit class names + metadata verify (§10). Cohort loss → committed/hashed + README (§7). Under-power → paired mean-diff + bootstrap CI (§9). Non-λ divergence → §12 checklist + step-0 hash.

## 14. Success criteria
Accept 26B if paired 26B−26A **mean** lesion-Dice diff > 0 with bootstrap 95% CI excluding 0 (target mean ≥ +0.02), AND mean collapsed pancreas Dice regresses by **≤ 0.01** vs 26A. Null/negative → EXP-27 (neighbors + larger crop, matched control). Report collapsed-3-class throughout; flag the changed pancreas GT; state that no causal claim is made vs 0.415.
