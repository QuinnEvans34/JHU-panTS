# EXP-26 code-review handoff (for Codex) + runbook

The spec `docs/spec-exp26-anatomy-aware.md` (v4) was APPROVED. This is the implementation for
code review. Nothing has been trained yet. Review the code, then we run 26A + 26B.

## What to review (files changed / added)
| File | Change |
|---|---|
| `configs/level45.yaml` | `label_mode` doc, `pancreas_resolver`, subregion `source_masks`, `loss.lambda_anat`. |
| `src/data/transforms.py` | `resolver_of`/`mask_key_map`/`mask_keys`/`load_keys` helpers; `ResolveLabeld` composer; mode-derived keys in `build_transforms`. |
| `src/data/dataset.py` | `build_records(…, cfg)` resolver-aware; `_cache_tag` now includes label_mode + resolver. |
| `src/training/losses.py` | `AnatomyAwareLoss` + `_soft_dice_from_probs`; `build_loss` returns it for anatomy5. |
| `src/training/metrics.py` | `DiceEvaluator(collapse="anatomy5")` collapses 5→3 before Dice. |
| `src/models/segresnet.py` | `sha256_file`, `load_suprem_asserting_head_only`, `save_init_checkpoint`, `load_init_weights`. |
| `scripts/train.py` | `--label-mode/--pancreas-resolver/--lambda-anat/--init-weights/--train-ids/--val-ids/--report-ids/--neg-ids`; seeded `torch.Generator` + `transform.set_random_state`; `--train-ids` leakage guard; `run_meta` in every checkpoint; loss-component logging. |
| `scripts/evaluate.py` | `--label-mode anatomy5` → collapse probs + GT. |
| `src/inference/collapse.py` | shared 5→3 collapse helpers. |
| `scripts/audit_subregions.py` | step-0 geometry audit (you run on the drive). |
| `scripts/make_init_checkpoint.py` | builds the one hashed init both arms load. |
| `scripts/build_exp26_cohorts.py` | builds/freezes/hashes the 4 cohorts (already run). |
| `configs/cohorts/exp26/` | frozen train/val20/report40/report40_neg + README + hashes. |
| `tests/test_anatomy_loss.py` | loss unit tests (spec §4). |

## KEY DESIGN DECISION to rule on (deviation from spec §5.1, flagged deliberately)
Spec §5.1 said carry H/B/T/lesion as four separate boolean masks through every spatial
transform. **The code instead carries ONE mutually-exclusive 5-class integer `label`**
(head=1, body=2, tail=3, lesion=4-wins) through the pipeline, and derives inside the loss:
the collapsed primary target, the aux domain `M = label∈{1,2,3}`, and per-subregion targets
`label==k`. Rationale:
1. **Lossless for the aux domain** whenever head/body/tail MUTUAL overlap is negligible —
   which `audit_subregions.py` gates (VERDICT prints if overlap >2%). Lesion-vs-subregion
   overlap is irrelevant because those voxels are excluded from `M`.
2. **Better-defined than overlapping booleans:** softmax cannot satisfy p_head=p_body=1 at a
   shared voxel; the mutually-exclusive assignment is the sensible target.
3. **Minimal alignment surface:** one NN-interpolated map through the exact, proven pipeline,
   instead of four mask keys threaded through ~10 transforms (the alignment-bug risk you flagged).
If you disagree, the fix is localized (emit head/body/tail/lesion keys from `mask_key_map`,
thread them through the composer). But we believe single-label is *more* correct here.

## Specific things to verify (your v4 checklist)
- **No double softmax:** `AnatomyAwareLoss.forward` softmaxes ONCE; Dice + focal operate on the
  collapsed probs directly (`_soft_dice_from_probs` has no internal softmax).
- **Foreground focal reduction:** denominator = count of non-background target voxels; zero-fg
  guarded by `p.sum()*0` (differentiable zero).
- **Aux:** masked per-class Dice over `M`, RAW probs (no renormalization), equal average,
  empty-subregion term excluded via `present`, all-absent → differentiable zero.
- **Numerical check done in numpy** (`/tmp/check_anat_math.py` output): collapse sums to 1;
  collapsed Dice == naive reference; focal + aux finite; all-absent aux == 0; finite at logits×±50.
  Torch gradient/stability tests are in `tests/test_anatomy_loss.py` (run on the Mac — no torch in the review sandbox).
- **Identical init:** both arms `--init-weights outputs/checkpoints/exp26_init_5ch.pt`; its
  SHA-256 is recorded in `run_meta.init_sha256` in every checkpoint → verify both arms match post-hoc.
- **Transform RNG controlled, not just shuffle:** `ds.transform.set_random_state(seed)` +
  `DataLoader(generator=torch.Generator().manual_seed(seed))`.
- **Cohorts frozen + disjoint:** `build_exp26_cohorts.py` asserts train/val20/report40/neg
  disjoint + outside test; hashes in the README and in `run_meta.cohort_sha256`.
- **Metadata abort:** `run_meta` embedded; (note: `evaluate.py` currently reads `--label-mode`
  from CLI and does not yet hard-abort on metadata mismatch — call that out if you want it enforced).

## Known scope notes (not bugs)
- `cascade_eval.py` / `sanity_check_case.py` still call `build_records` without cfg → legacy
  3-class default. They are NOT part of the EXP-26 path (headline eval is `evaluate.py`) and
  don't break. Updating them for anatomy5 is deferred (autonomous cascade = capstone).
- anatomy5 assumes the **whole-box** recipe (no random sub-patch sampler); the `classes`
  sampler still hardcodes `num_classes=3` and must not be used with anatomy5.

## Runbook (after code review passes) — CORRECTED (train uses --patch, eval uses --roi)
```bash
# 0. geometry audit on the frozen cohorts (drive connected) — must say VERDICT: PASS
python scripts/audit_subregions.py --cohorts configs/cohorts/exp26
#    if REVIEW: rebuild excluding the flagged cases, then re-audit + re-hash:
#    python scripts/build_exp26_cohorts.py --exclude outputs/exp26_exclude_ids.txt
#    then paste the audit's overlap max/mean into configs/cohorts/exp26/README.md

# 1. one shared init checkpoint (records + prints SHA-256)
python scripts/make_init_checkpoint.py --out outputs/checkpoints/exp26_init_5ch.pt

# 2. smoke-test (50 iters) — confirm it runs; watch "[loss] primary ... aux ..." scale
python scripts/train.py --label-mode anatomy5 --whole-box --crop-native 16 --patch 128 \
  --init-weights outputs/checkpoints/exp26_init_5ch.pt \
  --train-ids configs/cohorts/exp26/train.txt --val-ids configs/cohorts/exp26/val20.txt \
  --report-ids configs/cohorts/exp26/report40.txt --neg-ids configs/cohorts/exp26/report40_neg.txt \
  --lambda-anat 0.3 --max-iters 50 --val-every 25 --cache disk

# 3. NIGHT 1 — 26A control (lambda_anat = 0)
python scripts/train.py --label-mode anatomy5 --whole-box --crop-native 16 --patch 128 \
  --init-weights outputs/checkpoints/exp26_init_5ch.pt \
  --train-ids configs/cohorts/exp26/train.txt --val-ids configs/cohorts/exp26/val20.txt \
  --report-ids configs/cohorts/exp26/report40.txt --neg-ids configs/cohorts/exp26/report40_neg.txt \
  --lambda-anat 0.0 --max-iters 24000 --val-every 500 --cache disk --run-name exp26A_lam0

# 4. NIGHT 2 — 26B treatment (lambda_anat = 0.3), identical except lambda
python scripts/train.py --label-mode anatomy5 --whole-box --crop-native 16 --patch 128 \
  --init-weights outputs/checkpoints/exp26_init_5ch.pt \
  --train-ids configs/cohorts/exp26/train.txt --val-ids configs/cohorts/exp26/val20.txt \
  --report-ids configs/cohorts/exp26/report40.txt --neg-ids configs/cohorts/exp26/report40_neg.txt \
  --lambda-anat 0.3 --max-iters 24000 --val-every 500 --cache disk --run-name exp26B_lam03

# 5. eval BOTH on the EXACT frozen report cohort (metadata + cohort-hash checked; collapsed 3-class)
python scripts/evaluate.py --ckpt <26A archive>/best.pt --label-mode anatomy5 --whole-box \
  --crop-native 16 --roi 128 --pos-ids configs/cohorts/exp26/report40.txt \
  --neg-ids configs/cohorts/exp26/report40_neg.txt --per-case-csv outputs/exp26A_percase.csv --sweep
python scripts/evaluate.py --ckpt <26B archive>/best.pt --label-mode anatomy5 --whole-box \
  --crop-native 16 --roi 128 --pos-ids configs/cohorts/exp26/report40.txt \
  --neg-ids configs/cohorts/exp26/report40_neg.txt --per-case-csv outputs/exp26B_percase.csv --sweep

# 6. paired inference (fails closed on any cohort mismatch / NaN / wrong n)
python scripts/paired_bootstrap.py --a outputs/exp26A_percase.csv --b outputs/exp26B_percase.csv \
  --require-ids configs/cohorts/exp26/report40.txt --col lesion_raw
```

## Round-2 fixes applied (this review's blocking items + safeguards)
- **Audit** now loads the CT and requires every H/B/T/lesion mask to match CT shape+affine (FATAL on mismatch, not zeroed); missing/empty lesion is FATAL for a manifest-positive case; volume failures count toward the verdict; asserts every requested id exists in the manifest; writes `outputs/exp26_exclude_ids.txt` (fatal ∪ overlap-fail ∪ volume-fail).
- **Collapse** takes an explicit `label_mode` (never infers from `max`); tests cover anatomy labels {0,1,2} and {0,1}.
- **Eval** loads checkpoint metadata and ABORTS on any recipe disagreement (label_mode/out_channels/spacing/sw_roi/whole_box/roi_source/crop margins); verifies `--pos-ids`/`--neg-ids` SHA-256 against the checkpoint's `report40`/`report40_neg`; anatomy5 requires the frozen cohort files (no first-N fallback). Checkpoint metadata now stores the full spatial recipe.
- **Paired bootstrap** fails closed: identical unique case sets, exact `--expect-n` (40), no NaN/inf, B reindexed to A, optional `--require-ids` hash/set check.
- **Safeguards:** aux `den.detach().item()` (no autograd sync); anatomy5 aborts if the transform RNG can't be seeded and if any of `--init-weights/--train-ids/--val-ids/--report-ids/--neg-ids` is missing; `load_suprem_asserting_head_only` requires exactly `conv_final.2.conv.{weight,bias}`; `_cache_tag` carries a `CACHE_VERSION` token.
