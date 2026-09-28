# First capstone experiment: readiness checklist

Owner: Quinton Evans; Codex implementation/review. Date: September 28, 2026.
Status: **not ready to launch**. This is daily-plan item 5, not a new numbered plan,
experiment registration, or authorization to bypass G0/G1 or Plan 04.

## Smallest useful target

Prepare a **PanTS-only, train-role pancreas-localizer smoke run**. The question is whether
the new capstone path can load verified CT/pancreas targets, perform a bounded learning
step sequence, save/reload an identifiable checkpoint, and produce correctly aligned
full-volume output. It is not a lesion-performance study or the formal autonomous baseline.

This follows Plan 05's localizer-first sequence and Plan 06's smoke classification. A
positive lesion case is useful for later target/cascade verification, but is not inherently
required to train a pancreas-only localizer. Pancreas annotation qualification still is.
Scratch initialization is the proposed first-smoke default to avoid an unnecessary external
checkpoint dependency; it is not a decision against permitted third-party pretraining later.
Architecture, steps, selection, budget and pass bars must be registered before execution.

## Verified starting point

- Scoped Python environment/test foundation; latest native full suite: **410 passes**, two
  upstream warnings. This is not full G0 or scientific validation.
- Approved legacy memberships reproduce exactly: 7,200 training / 1,800 validation / 901 test.
- Pinned acquisitions and extraction evidence exist; publisher-test CT remains unextracted.
- Tested identity guards, metadata join, file/header evidence and deterministic manifest assembly.
- Two-case diagnostic manifest is quarantined; no frozen real cohort or eligible annotation.
- Reviewed voxel audit and four-pair real-data pilot completed. Both sample pancreas masks
  contain 0/1; both lesion masks are empty. Case 2 units remain unresolved.
- Scoped drive/backup setup exists; scientific-run enablement and production source aliases
  remain disabled. These must not be enabled merely because a smoke run is desired.

Evidence: [pilot](../data/VOXEL-PILOT-2026-09-28.md),
[manifest slice](../data/MANIFEST-SLICE-2026-09-28.md),
[metadata](../data/METADATA-ADAPTER-2026-09-28.md),
[metric foundation](../testing/CONTRACT-METRICS-2026-09-20.md).

## Launch gates and concrete evidence

All unchecked items remain open. Existing helpers are foundations, not completed gates.

| Gate | What exists / what remains | Evidence required to close |
|---|---|---|
| R0 Relevant G0 review | Python/UI foundation evidence exists; full readiness is not declared | Reconcile required G0 checks and owning-plan prerequisites; record passed checks and explicit outstanding non-run scope without silently waiving gates |
| R1 Qualified source and targets | Hash/header/voxel readers work; only two cases inspected | Reconciled source inventory/manifest under Plan 02, verified geometry and pancreas provenance/allowed uses, approved mapping and explicit issue dispositions; meet G1, not a partial-snapshot exception |
| R2 Frozen protected smoke cohort | Exact base controls and identity guards exist; publisher/resolver absent | Registered frozen train-role descendant, parent/ancestor hashes, subject/duplicate checks, profile, completion marker, reproducible membership hash; consumer rejects arbitrary ID files, ineligible annotations and altered packages |
| R3 Tested preprocessing and target | Historical transforms exist, not qualified for this run | Synthetic spacing/orientation/label tests, pancreas-only target definition, train/inference parity, source-space round trip and bounded real-case load; no lesion mask can influence localizer input |
| R4 Initialization lineage | Policy approved; capstone loader/lineage gate not established | Explicit scratch record plus tests that no checkpoint is loaded; historical-checkpoint rejection guards. If using pretraining instead: licensed pinned source, hash and tensor-load audit; never old project-trained weights |
| R5 Run and checkpoint identity | Historical training script has checkpoint logic; not capstone-qualified | Immutable run/config/code/environment/cohort records, new non-overwriting destinations, verified checkpoint reload and interrupted-run handling; no unreviewed resume into historical runs |
| R6 Smoke metrics and outputs | Legacy pure metric goldens exist, not full evaluator | Hand-computed target/empty/failure checks for the selected smoke measurements, finite loss/gradients, declared output shape/classes, source-grid check and checkpoint reload agreement; no generalization claim |
| R7 Storage and compute preflight | Registered drive and initial synthetic restore passed | Verified source resolver, output capacity/free-space floors, single accelerator/writer owner, measured small-fixture memory/timing, hard step/time budget, fail-closed missing-drive behavior and run-relevant keeper/restore checks |
| R8 Run plan and launch review | Living notebook exists; no new CAP-EXP registered | Pre-run CAP-EXP entry with exact IDs/hashes, question/class, seed/config, expected checks, resource/abort rules and artifact paths; explicit review of readiness before launching |

G3 remains required before expensive baseline training. Plan 10 permits bounded component
smokes when their independent gates pass; it does not grant a shortcut around G1 or protected
data roles. Full NSD/detection/CI/operating-curve implementation is needed for later claims,
not for calling a wiring smoke successful. Define that smoke's metrics precisely nonetheless.

## Implementation order from here

1. **Bounded data follow-up design.** Select a small deterministic set from the exact approved
   training list, including source-positive tumour flags for later lesion inspection and
   separately identified anomaly candidates. Record selection provenance, exact file list,
   memory/time/disk budget and stop criteria before running. A source flag is a selection
   clue, not proof of foreground voxels. Do not extend to a full scan by default.
2. **Close interpretation gaps.** Verify source annotation provenance and intended uses;
   inspect actual foreground values. Resolve or explicitly quarantine unknown-unit cases.
   Do not invent units, foreground codes, biological identity or manual-label provenance.
   Publish append-only resolutions and a NEW manifest, preserving the diagnostic package.
3. **Complete Plan 02 source/cohort path.** Reconcile required source coverage and duplicate
   candidates, implement/test frozen cohort publication and resolution, then prove repeat
   builds and train-only consumer enforcement. Full G1 remains open until its evidence exists.
4. **Build the small imaging/run slice.** Test preprocessing/localizer target, initialization
   and run/checkpoint records using synthetic fixtures first. Classify reusable historical
   functions; do not launch scripts/train.py merely with corrected drive paths. Its --split,
   --train-ids and --val-ids interfaces are not the approved cohort-ID consumer contract.
5. **Preregister and smoke.** Agree the exact recipe and numeric limits, record the CAP-EXP
   game plan, verify all R0–R8 evidence, then run the bounded experiment. Log every attempt,
   including interruption, failure, null learning and negative results.

Steps 2–3 are the current critical path to real training. Synthetic work in step 4 can be
prepared in parallel conceptually, without implying multi-agent dispatch or authorization
for Plan 04 shared workflow machinery.

## Explicitly separate from this first smoke

- PANORAMA G2 gates PANORAMA/mixed-source runs; it need not precede PanTS-only training.
- Retrieval/vector DB, literature ingestion, the completed UI and a confirmed radiologist
  meeting are not prerequisites to this imaging smoke.
- The full two-stage cascade, held-out baseline and controlled model comparison come later.
- No publisher-test reads or model/threshold selection. Training smoke metrics are not
  validation/test results. Disclose historical evaluation use in later reporting.
- Plan 04 explanation is complete; coding/spike authorization is still separate. Obtain it
  before implementing workflow runners/locks/stages, including code disguised as a smoke helper.
- No paid compute, remote upload, automatic Git commit/push or all-night job is authorized here.

## Decisions not to make prematurely

Do not choose model experimentation winners, relax affine tolerances, classify the 101 size
flags as corrupt, or infer a general lesion mapping from two empty masks. Preserve the base
7,200/1,800/901 memberships even when a case is quarantined: record eligibility separately;
do not silently rebalance or replace protected members.

Before the first launch, Quinton and Codex should review the proposed scratch localizer smoke,
actual qualified cohort size, quantitative pass/stop criteria and resource estimate together.
This checklist does not reserve an experiment number or record a run as completed.

## Completion checklist

- [x] Current evidence and remaining gates consolidated against Plans 02/05/06/09/10.
- [x] Smoke scope separated from formal baseline and later integration work.
- [ ] R0–R8 supported by executable evidence and reviewed for the exact run.
- [ ] Experiment registered before compute; every attempt recorded afterward.
- [ ] Results used to choose the next experiment with explicit retained/changed factors.

Next concrete deliverable: the bounded positive-case/anomaly follow-up selection and audit
budget. No further source reads or model execution occurred while writing this checklist.
