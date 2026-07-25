# EXP-26 pre-training readiness dossier

Everything measured, checked, and built before launching the two-night anatomy-aware experiment.
Purpose: a final go/no-go review. Nothing has trained yet beyond a 50-iter smoke test.

---

## 1. The experiment
**Hypothesis:** adding auxiliary head/body/tail (subregion) supervision to the whole-box
SegResNet+SuPreM model raises **lesion Dice** without diluting the tumor objective. It's also
the first step toward a richer multi-structure (Level-5 / capstone) model.

**Design — two arms, identical except one scalar `λ_anat`:**
- Both arms: 5-class output (bg, head, body, tail, lesion), same SuPreM-initialized head, same
  cohorts, ROI, seed, data order, and **LR-schedule horizon = 24,000 steps** (locked, pre-registered
  below), with an **operational stop at step 12,000** tonight (`--stop-after-step 12000`). Both arms
  use the identical horizon and stop; either can be continued to 24,000 later, together.
- **26A control:** `λ_anat = 0` (the 3 pancreas channels are trained only through their sum).
- **26B treatment:** `λ_anat = 0.3` (auxiliary loss forces the channels to mean head/body/tail).
- Causal read = paired 26B−26A per-case lesion Dice (mean diff + bootstrap CI).

**Loss (custom, one softmax, no double-softmax):** collapse 5→3 probs (`p_panc = p_head+p_body+p_tail`),
primary = soft Dice + foreground-only probability focal on the collapsed 3-class (bg excluded);
auxiliary = masked per-class Dice for head/body/tail over non-lesion pancreas voxels (raw probs,
no renormalization, empty-class excluded, all-absent → differentiable zero). This is a deliberate
reformulation, **not** claimed equivalent to MONAI DiceFocal; 26A is the sole baseline.

## 2. Where the model stands now (the baseline this builds on)
Clean, leakage-free held-out numbers (EXP-24, whole-box scaledmax_clean, n=40):
**lesion Dice 0.415 · pancreas 0.817 · detection 95% · specificity 15%.**
Diagnosis: the model detects tumors but over-segments them (small-tumor Dice 0.11, medium 0.43,
large 0.60). EXP-26 targets lesion Dice; specificity is a separate (capstone) axis.

## 3. How the masks are built and handled
- **Pancreas resolver = head ∪ body ∪ tail** (`--pancreas-resolver hbt_union`), decoupled from the
  label mode. This replaces the single `pancreas.nii.gz` combined mask, which has known corrupt/empty
  cases. Audit confirms the union has **no corrupt-huge masks** (max 278.7 mL, all within [20, 300]).
- **Single mutually-exclusive 5-class label** (`ResolveLabeld`): paint head=1, body=2, tail=3, lesion=4
  (lesion wins). The primary-collapse target, the auxiliary domain `M = label∈{1,2,3}`, and the
  per-subregion targets are all derived from this ONE integer map inside the loss. This is provably
  lossless for the auxiliary domain because **head/body/tail never overlap** (audit: 0.00%), and it
  is better-defined than overlapping booleans (softmax cannot satisfy p_head=p_body=1). One
  NN-interpolated map ⇒ minimal alignment surface. (Codex approved this design, conditional on the
  audit PASS, which we now have.)
- **Whole-box ROI:** crop to the pancreas-union bbox + 16-voxel native margin, resample to 128³ @ 1.5mm,
  feed as one cube (no random sub-patch). Same recipe as the current best models.

## 4. Every check we ran, and what it told us
| Check | Result | Meaning |
|---|---|---|
| Loss math (numpy mirror) | collapse sums to 1; collapsed Dice == hand-rolled reference; focal foreground-only + finite; aux masked + finite; all-absent aux == 0; finite at logits×±50 | The loss algebra is correct independent of torch. |
| Loss unit tests (`tests/test_anatomy_loss.py`) | 7/7 pass | Softmax-once, gradients reach H/B/T via p_panc, λ=0 == primary, numerically stable, aux empty-class handling. |
| Collapse tests (`tests/test_collapse.py`) | 6/6 pass | 5→3 collapse is mode-declared (a body-only {0,1,2} case maps to pancreas, never lesion). |
| Geometry audit (`audit_subregions.py`, 1,512 → full val pool) | 420 cases excluded, then **VERDICT: PASS** on the frozen cohorts (1,349 cases: 0 fatal / 0 overlap / 0 volume) | Masks are CT-aligned; empty-subregion and CT/mask-orientation defects removed. |
| H/B/T mutual overlap | **max 0.00% / mean 0.000%** | Validates the single-label design unconditionally. |
| Pancreas-union volume | 20.2 – 278.7 mL (no >300) | The union resolver avoids the corrupt combined-mask blobs. |
| Shared init checkpoint | 81/83 tensors loaded; head re-init **verified** = exactly `conv_final.2.conv.{weight,bias}`; sha256 `8c9af5eb…` | Both arms start byte-identical (recorded in checkpoint metadata). |
| 50-iter smoke test | loss 1.55→1.25; primary ≈1.02, aux ≈0.69 → at λ=0.3 aux ≈17% of total; val ran | Runs end-to-end; aux is on a mild scale, so λ=0.3 is confirmed (not aux ≫ primary). |
| Leakage / disjointness guards | train ∩ val/report/neg/test = ∅ (asserted at build + startup) | No leakage of the class fixed last week. |

## 5. Frozen cohorts (committed + hashed, `configs/cohorts/exp26/`)
- train 1,249 · val20 20 · report40 40 · report40_neg 40 — all disjoint, all outside official test.
- SHA-256 recorded in the README and embedded in every checkpoint's metadata; eval verifies the
  `--pos-ids`/`--neg-ids` hashes against the checkpoint and aborts on mismatch.

## 6. Metrics reported + decision rule
- Headline: **collapsed lesion Dice** on report40 (comparable to the 0.415 baseline), + pancreas Dice
  (flagged: pancreas GT changed to the union), + per-subregion Dice (bonus), + specificity on report40_neg.
- **Primary inference:** paired 26B−26A per-case lesion-Dice **mean difference + bootstrap 95% CI**
  (`paired_bootstrap.py`, fails closed on any cohort mismatch/NaN/wrong-n).
- **Accept 26B** iff the lesion CI excludes 0 (target mean ≥ +0.02) AND pancreas regresses by ≤ 0.01.
  Null/negative is a fine, publishable outcome.

## 7. Multi-day run safety (pause/resume design — hardened per Codex round 2)
The run spans two nights + a school day and must be interruptible. Guarantees:
- **Atomic checkpoints:** `save_checkpoint` writes `*.tmp` then `os.replace()`. A Ctrl-C/crash mid-write
  can only corrupt the temp file; `last.pt`/`best.pt` are always complete.
- **Deterministic, resumable data:** the (case index, augmentation) at global step S is a pure function
  of (seed, S) — per-epoch shuffle seeded by (seed, epoch), MONAI transform RNG reseeded per step under
  `num_workers=0` + direct `ds[idx]` (Codex confirmed this seeds the PersistentDataset random suffix).
  So `--resume` at step S reproduces the SAME trajectory as an uninterrupted run, and both arms see
  identical data per step regardless of interruptions. (MPS float ops aren't bitwise-deterministic.)
- **Graceful Ctrl-C, correct step:** first SIGINT finishes the current step, saves `last.pt` at the
  EXACT stopping step (the earlier bug that stamped it `total_iters` — making resume a no-op — is fixed
  via a `paused` flag + for/else, so a paused run never claims completion). Second SIGINT force-quits.
- **Resume verifies experiment identity:** before restoring, the checkpoint's metadata is compared to
  the current command (label_mode, λ_anat, init SHA, all cohort hashes, seed, patch, sw_roi, spacing,
  crop margins, whole_box, roi_source, loss, **total_iters horizon**, val_every) and ABORTS on any
  mismatch — you can't resume 26A from a 26B checkpoint or a different horizon/cohort. Also aborts if
  `step ≥ total_iters`.
- **Strict optimizer/scheduler on resume (anatomy5):** missing/unloadable optimizer or scheduler state,
  or a scheduler step that disagrees with the checkpoint step, RAISES — no silent fresh-optimizer
  fallback that would change the trajectory.
- **Self-contained `last.pt`:** stores `best_val` directly (still cross-checks the sibling `best.pt`).
- **Per-arm active checkpoint dir:** anatomy5 writes to `…/pants-level45/<run_name>/` so 26A and 26B
  never share (or resume from) each other's `best.pt`/`last.pt`.
- **Operational stop, fixed schedule:** `--stop-after-step 12000` ends the loop at 12,000 while the LR
  cosine keeps its 24,000 horizon, so the run can be continued later with the identical schedule.
- Known residual: a resumed launch opens a new MLflow run (metrics split by step range); `best.pt`,
  the archive, and the ledger `status` (paused/stopped/complete) are unaffected.

## 8. Pre-registered horizon decision (locked before 26A starts)
LR-schedule horizon = **24,000 steps**, tonight's operational stop = **12,000** (`--stop-after-step`),
best checkpoint = val-selected on val20. Rationale: keep the pre-registered 24,000 cosine (EXP-24's best
was ~step 18k, and anatomy specialization may develop later than the collapsed lesion objective), but
stop at 12,000 for the overnight and retain the option to continue BOTH arms to 24,000 together. This is
a resource-driven protocol, fixed for both arms before either starts; the treatment arm will never be
extended alone.

## 9. Runbook (both arms; drive connected, lid open)
```bash
# 26A control — LR horizon 24000, stop at 12000 tonight
python scripts/train.py --label-mode anatomy5 --whole-box --crop-native 16 --patch 128 \
  --init-weights outputs/checkpoints/exp26_init_5ch.pt \
  --train-ids configs/cohorts/exp26/train.txt --val-ids configs/cohorts/exp26/val20.txt \
  --report-ids configs/cohorts/exp26/report40.txt --neg-ids configs/cohorts/exp26/report40_neg.txt \
  --lambda-anat 0.0 --max-iters 24000 --stop-after-step 12000 --val-every 500 --cache disk \
  --run-name exp26A_lam0

# 26B treatment — identical except --lambda-anat 0.3 --run-name exp26B_lam03

# PAUSE (Ctrl-C once, before step 12000): rerun the EXACT same command + --resume:
#   --resume outputs/checkpoints/pants-level45/exp26A_lam0/last.pt
#
# CONTINUE past a natural 12000 stop toward 24000 (later, both arms): rerun with --resume AND
# REMOVE --stop-after-step (or set it to 24000). Keeping --stop-after-step 12000 does 0 steps.
```

## 10. Pre-launch determinism check (2 min, do this first)
Run the 50-iter smoke twice with the same command → the per-step loss sequence should match. Then run
~30 steps, Ctrl-C once, resume with `--resume …/exp26A_lam0/last.pt`, and confirm it prints
`resumed … at step 30` and continues with a sane loss (not restarting at 0, not jumping to 12000).
