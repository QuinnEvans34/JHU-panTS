# Codex audit prompt — full-system robust audit (Week 4)

Paste this to Codex with the repo connected. It caught a real ROI-leak last time (`docs/codex-metrics-audit.md`), so the same adversarial style is wanted here: **assume there ARE bugs and holes and find them.** This is a FULL-SYSTEM audit — data → training → model → inference → cascade → metrics → claims — not just the recent cascade work.

---

## Read first (context)

- `CLAUDE.md` — project state and the "Next session" block (current Week 4 status).
- `docs/experiments.md` — the experiment log; focus on EXP-17c, EXP-20, EXP-22, EXP-22b, EXP-23 (the most recent entries at the end), plus the "Checkpoint & logging discipline" note.
- `docs/codex-metrics-audit.md` — your prior audit of this repo (same output style wanted).
- `docs/implementation-plan.md` — the plan + ownership contract.

## What the system is

3D pancreas + pancreatic-lesion segmentation on JHU PanTS (MONAI/PyTorch). Non-diagnostic CADe assist. SegResNet, fine-tuned from SuPreM pretrained weights, vs a from-scratch baseline. Extreme class imbalance (lesion ~0.04% of a volume). The current architecture is a **localize-then-segment cascade**: a full-scan localizer finds the pancreas, its predicted bounding box (never the GT) is cropped + resized into a 128³ cube, and a whole-box segmenter predicts pancreas + lesion inside it. This removes the "oracle ROI" and the ROI data-leak.

## Environment constraints (do NOT flag these as bugs — they are deliberate)

- Apple Silicon **MPS**, not CUDA. `fp32` (autocast is unreliable on MPS). `PYTORCH_ENABLE_MPS_FALLBACK=1`. Sliding-window patches run on MPS, stitched on CPU to save memory.
- Dataset lives on an **external drive**; path is in `configs/level45.yaml`, never hardcoded. Two venvs: `.venv312` (has MLflow) and `.venv` (py3.14, no MLflow). Runs are small-scale (dev subsets / disk cache) by necessity, not choice.
- Guardrails that are intentional: split by patient not slice; full-volume sliding-window eval; pancreas & lesion Dice reported separately; tumor-positive sampling; no raw data or checkpoints committed.

## Files in scope (audit all; cite file + line)

- **Data:** `src/data/transforms.py` (ComposeLabeld, whole-box, crop, augmentation), `src/data/dataset.py` (cache tags, PersistentDataset/CacheDataset), `scripts/build_manifest.py`, `scripts/create_splits.py`, `scripts/make_scaled_split.py`, `scripts/audit_masks.py`.
- **Model / loss:** `src/models/segresnet.py` (SuPreM load + 32→3 head re-init), `src/training/losses.py` (DiceFocal, include_background), `src/training/metrics.py`.
- **Training:** `scripts/train.py` (loop, checkpoint archive, `--resume`, best.pt selection, optimizer/scheduler, encoder freeze/unfreeze).
- **Inference / eval:** `src/inference/sliding_window.py`, `src/inference/postprocess.py`, `scripts/evaluate.py`, `scripts/cascade_eval.py`, `scripts/analyze_cases.py`.
- **Config:** `configs/level45.yaml` (does the code actually honor every key; are "NOT-YET-WIRED" keys clearly inert?).

## Audit areas (rate each finding Critical / High / Moderate / Minor; separate real-bug vs framing vs design-risk)

1. **Mask-source robustness (diagnosis resolved — validate the planned fix).** `audit_masks.py` (raw nibabel, val n=1800) found the pancreas has TWO flaky sources: combined `pancreas.nii.gz` empty on 110, `head/body/tail` union empty on 116, they disagree (9 subregion-only, 15 combined-only), and 6-7 have a CORRUPT-HUGE combined (445-855 mL) with normal subregions (~60 mL); on normal cases the two reconstruct each other (ratio ~1.00). 101 cases empty in BOTH sources are all healthy, clustered in one cohort (site CH / SIEMENS) = a genuine dataset gap. Config `source_masks.pancreas` loads ONLY the combined file. PLANNED FIX: pancreas = union(combined, head, body, tail), dropping the combined file when >300 mL. VALIDATE: right place (`ComposeLabeld` / `source_masks` / loader)? Does `ComposeLabeld` keep lesion-wins-on-overlap with multiple pancreas keys? Risk to the ~1670 normal cases? Are the empty/corrupt cases excluded in TRAINING splits (scaledmax), not just val?

2. **Cascade correctness (`scripts/cascade_eval.py`).** It crops AFTER resampling to 1.5mm (one path for gt/pred), whereas training cropped in NATIVE space then resampled — is the `gt-union` arm a valid reproduction (it lands ~0.03 below the oracle 0.528)? Check `bbox_from_mask`, `face_clearance_mm` (signed clearance vs true pancreas), largest-connected-component box selection (can a spurious blob become the box?), the ResizeWithPadOrCrop center-crop on oversized boxes (does containment, computed on the PRE-resize box, overstate what the segmenter sees after the cube center-crops it — i.e. is the 94.6% optimistic for the 27.5% oversized cases?), and that the GT label is carried through the SAME predicted crop as the image.

3. **Training loop (`scripts/train.py`).** The `--resume` path reportedly corrupted a keeper once (reset best_val, clobbered best.pt) — is it actually safe now, or still broken? best.pt is selected by val LESION Dice (`score = vl if vl is not None else ...`) — is that wrong for a pancreas-only localizer run (it should arguably use pancreas Dice or last.pt)? Check the checkpoint archive/ledger logic, optimizer/scheduler construction (does resume restore them?), the encoder freeze→unfreeze at warmup, and differential LR.

4. **Model + loss + transfer.** `segresnet.py`: is the SuPreM checkpoint loaded correctly (strip `module.`, unwrap `net`, re-init 32→3 head) with the right architecture (init_filters=16, GroupNorm groups=8, blocks)? Any silently-skipped weights? `losses.py`: DiceFocal with `include_background=False` — correct for this 3-class imbalance, and does `to_onehot_y`/`softmax` line up with how logits are produced?

5. **Data pipeline + caching.** `dataset.py` disk-cache tag (`_cache_tag`) — can two different recipes ever collide in one cache dir, serving stale preprocessed data? Does PersistentDataset correctly exclude random augments from the cached prefix? Whole-box + crop-native + roi_source interactions in `transforms.py`.

6. **Metrics + statistics.** The NaN-on-empty-GT Dice + nanmean (is it applied everywhere, incl. `analyze_cases.py`?); `ignore_empty`; the "rule of three" bound (0 fails in n → <3/n at 95% CI) — applied honestly, n=40 vs n=800? Mask-negative specificity@50mm3 definition. Any metric where healthy cases could inflate/deflate a mean.

7. **Leakage + splits.** Confirm patient-level, no train/val overlap in the cascade path and in localizer training (`scaledmax` train vs `val` eval). Does the GT-quality gate bias the reported number? Does the whole-box crop leak lesion location (the ROI-leak we fixed — verify `roi_source`)?

8. **Config vs code.** Does the code honor every `configs/level45.yaml` key it appears to, and are keys labeled "NOT-YET-WIRED" truly inert (no silent half-effect)? Any place a CLI override and the config disagree.

9. **Hyperparameters worth tuning (we WANT leads here).** Flag any hyperparameters that look mis-set or worth a sweep for Week 4: LR / schedule / warmup, focal gamma, loss weights, sampling ratios, patch/spacing/whole-box size, encoder-freeze duration, post-processing thresholds. Say which you'd expect to move lesion Dice or specificity, and why.

10. **Verify these specific CLAIMS against the code/data (flag any that the code doesn't support):**
    - Provided-ROI lesion Dice ~0.528, autonomous (predicted-box) ~0.483, detection sensitivity 90% (EXP-17c / EXP-20).
    - Containment: pancreas 94.6% / tumor 98.9% fully contained on valid-GT (EXP-22).
    - Transfer >> scratch (EXP-09), and "four recipe nulls, data is the lever" (EXP-05/07/08/16 → EXP-17).
    - Both models (`transfer_wholebox_scaledmax`, `localizer_fullscan_scaledmax`) are logged in MLflow and archived on disk.

11. **The architecture IDEA itself + deployment.** Is "localizer box → whole-box segmenter" the right design for a trustworthy pipeline that JHU could run on 10k full-abdomen scans? What failure modes are we NOT measuring (contrast phase, scanner/site domain shift, partial/whole-body scans, non-axial orientations)? Is containment/clearance the right reliability metric, or are we missing something (e.g. a tumor near a clipped pancreas boundary, or a localizer that fails silently on out-of-distribution scans with no GT to catch it)? Is there a needed runtime fail-safe we haven't built?

12. **Anything else** — silent failures, misleading metrics, dead code, or any place a confident conclusion is stronger than the evidence.

## Output

Write a report to `docs/codex-audit-week4.md`: findings grouped by severity, each with file+line and a concrete fix. Separate **real bug** / **framing-or-reporting** / **design-risk**. Explicitly list (a) anything that would change a headline number, and (b) your top 3 highest-value fixes for Week 4. If something is actually correct and well-done, say so briefly — we want signal, not padding.
