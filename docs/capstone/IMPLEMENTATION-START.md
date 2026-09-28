# PROWL implementation start and prerequisite review

## Latest execution checkpoint — September 28

Read [CURRENT-CHECKPOINT](operations/CURRENT-CHECKPOINT.md) for live ownership and evidence.
The non-retrieval native Python suite passes 587 tests. The bounded five-study diagnostic
manifest remains quarantined; source qualification, frozen cohorts and training remain gated.
Plan 07 planning reconciliation/P1 are complete and Claude is working on P3. The
[first-experiment readiness checklist](operations/FIRST-EXPERIMENT-READINESS-2026-09-28.md)
defines R0–R8; its earlier audit counts and next-action prose are historical. Older dated
checkpoints below preserve history and are not current download/test/ownership status.

**Status:** Scoped Python/storage and UI build/synthetic tests passed; archives acquired; extraction/source validation and full G0 pending

**Status reconciled:** 2026-09-20 (earlier prerequisite review retained below)

**Official course start:** 2026-10-05

This is the handoff from planning to implementation, not Plan 13. It records the focused cross-plan
prerequisite review, current evidence, remaining choices, and the smallest useful starting sequence.
It does not claim a full code audit, verified drive health, clean-environment qualification, or a
ready-to-run model. The approved proposal/appendix and owning component plans remain authoritative.

## Review outcome

### September 21 drive preparation

Local Git checkpoint `f4d7109` preserves the planning/test foundation. The returned drive's identity,
capacity, archive sizes, and receipts were rechecked; PANORAMA ZIP directory checks passed.
See [drive preparation](operations/DRIVE-PREP-2026-09-21.md). Next data step: sequential PanTS
member/expanded-size scan and combined extraction budget. No extraction or source activation yet.

### Current checkpoint — September 20

Latest walkthrough update: Quinton accepted the Plan 04 explanation and Prefect/alternatives
discussion. The Prefect-first four-hour selection trial and fallback remain approved; temporary
local machinery is permitted if understood/tested, not a required managed server or cloud service.
D-201 remains open and explicit coding authorization is pending. Stakeholder preparation was
subsequently deferred at Quinton's request: radiologist contacted, reply pending. Resume tailored
questions/demo/feedback preparation when he confirms a participant or requests it, not as an
immediate development prerequisite. See Plan 11 for the current outreach record.
The checkpoints below preserve the earlier sequence and counts.

Latest: [Priority 4 contract/metric foundation](testing/CONTRACT-METRICS-2026-09-20.md) added 42
synthetic checks; the full Python fast suite now passes **147 tests** with two upstream warnings.
Four deliberate in-memory metric mistakes were caught. Production code/schemas are unchanged;
cross-record validation and the full capstone evaluator remain open. The Plan 04 walkthrough was
subsequently accepted on September 20 (D-045); orchestration implementation remains unauthorized. Earlier checkpoints below retain their historical counts.

Later September 20: the [UI foundation](testing/UI-FOUNDATION-2026-09-20.md) passed the unchanged
build, 18 unit/component tests, and one synthetic Chromium control flow. No production UI code
changed. Real viewer, full visual/accessibility qualification, and dependency-audit remediation
remain open. Next sequential work is additional contract/metric tests, not UI redesign.
The following earlier checkpoint preserves the state before that UI slice.

Both imaging archive queues completed and were verified while the drive was available. Both
receipts still state `source_ready: false`; extraction, label/ID/geometry reconciliation, protected
cohort checks, and source-alias activation remain pending. The drive is now unavailable for
away-from-home work; no drive access or new validation was performed in this documentation pass.
Latest full fast suite: **105 passed**, with two upstream warnings, following relocation fixes and
four workspace tests. These results do not close full G0, G1/G2, or training readiness.

See [the reconciled evidence and pending gates](operations/STATUS-2026-09-20.md).
Notion setup is complete. After this documentation pass, work proceeds one item at a time:
UI baseline/test foundation, additional contract/metric tests, and stakeholder
preparation. No UI implementation or Plan 04 code was started by this pass. A reviewed Git
checkpoint remains pending and must not include unrelated files or secrets.

All twelve designs have Quinton's approval. The immediate work is a clean, repeatable development
and test foundation, followed by protected data and the smallest valid imaging experiment. We do
not need more numbered implementation plans, a finished retrieval system, a radiologist appointment,
or recovery of the old drive to begin this foundation.

### Prerequisite corrections

| Finding | Reconciliation | Evidence/authority |
|---|---|---|
| G0 meant documented plans in the master plan but an already working test environment in Plan 09 | Split the checkpoint into G0-design and G0-verification; setup may create the evidence needed for the latter | Approved staged readiness, D-251, and Plan 12 approval |
| Old diagrams and Plan 05 header implied PANORAMA must precede PanTS-only training | G2 gates PANORAMA/mixed-source work; the PanTS baseline has its own G1/G3/run prerequisites | D-047, P05-03, Plan 05 fallback, Plan 06 dependencies |
| Plan 03 still named recovery/copy from the old drive as the acquisition route | Pinned fresh acquisition is valid; old-drive recovery remains optional | September 18 recovery direction and D-250 |
| Some approved design handoffs still had unchecked review boxes | Mark only demonstrably approved design facts; leave executable checks unchecked | D-209, approved Plans 09–12 |
| Plan 11/12 and Week 1 progress text lagged behind approvals | Record all design approvals; retain pending session, environment, data, and release evidence | D-253/D-254 and current user approvals |

The review inspected all twelve plan headers/readiness boundaries, the master plan, test/operations
protocols, and relevant source/test entry points. It did not revalidate every scientific detail,
source byte, schema consumer, or historical metric. Those checks remain in their owning plans.

## G0 without a prerequisite cycle

- **G0-design — satisfied for this bounded start:** approved architecture/component designs,
  authority, planned tests, known risks, and a scoped implementation order exist. This permits
  clean-environment setup, existing-code diagnostics, generated fixtures, and the contract/test
  foundation needed to prove readiness. No new scientific result is implied.
- **G0-verification — pending:** a clean supported environment installs reproducibly, the unchanged
  historical tests are collected/run/classified, core contract positive/negative fixtures execute,
  and fast Python/UI checks have retained evidence. Missing prerequisites remain failures/open work.
- **Full G0:** both checkpoints. Downstream references to "after G0" mean full G0 unless they
  explicitly name bounded foundation setup. Production component implementation and real model
  experiments additionally need the relevant component/data/storage checks.

This does not waive the explicit Plan 04 explanation/authorization gate. No Plan 04 schemas, runner,
stage wrappers, or Prefect spike begin until that gate is satisfied. Shared workflow/publication/
locking code must not be relabeled as test setup to bypass it.

## Component readiness map

| Plan | Design state | Next execution prerequisite |
|---|---|---|
| 01 Architecture | Approved / Ready design | Executable cross-record and producer/consumer tests |
| 02 Data/cohorts | Approved / Ready design | Clean tests, pinned source identity, accepted memberships and registered train-role descendants |
| 03 PANORAMA | Approved / Ready design | Actual pinned CT/label snapshots and source reconciliation; G2 remains open |
| 04 Orchestration | Walkthrough accepted; coding gated | Obtain explicit coding authorization, verify scoped operations boundaries, then run the bounded tool spike; D-201 remains open |
| 05 Imaging | Approved, gated | Tested geometry/targets, initialization audit, exact run cohort, storage/resources; G3 before expensive baseline work; G2 only for PANORAMA |
| 06 Evaluation | Approved, gated | Golden metric fixtures, run/experiment identities and resource checks; G4 before choosing the required comparison |
| 07 Retrieval | Approved, gated | Rights/query fixtures, relevant environment/storage checks and D-202 spike; no imaging dependency |
| 08 Interface | Approved, gated | Current baseline/build, validated adapters/contracts/fixtures, durable writer tests; neutral ordering until D-208 |
| 09 Testing | Approved, foundation next | Scoped clean environment and baseline evidence; production tests grow with components |
| 10 Operations | Approved, scoped storage checks passed | Source verification, production preflight/restore, complete environment evidence; no old-drive requirement |
| 11 Stakeholders | Approved, outreach active | Quinton confirms participant role/date or fallback; actual session later |
| 12 Delivery | Approved, execution later | Compatible selected artifacts and G1–G7 evidence before complete release qualification |

## September 19 implementation progress

The new `.venv-prowl` installed from an exact hashed macOS-arm64/Python-3.12 lock. All 37 historical
tests passed unchanged; adding 30 contract checks produced **67 passing tests**. Two upstream
deprecation warnings remain visible. Historical environments/source/tests and the UI are preserved.
See [the foundation record](testing/FOUNDATION-2026-09-19.md) for classification, commands, evidence,
and limitations. This is partial Python verification, not full G0 or model/data validation.

Later September 19, Quinton reconnected `PROWL-Data` and approved bounded setup under D-258.
The ignored roots registry, scoped filesystem tests, and independent synthetic backup/restore are
complete. Seven registry tests and thirteen download-guard tests bring the fast suite to **87
passes** at that checkpoint; fourteen PANORAMA guards subsequently brought the total to **101**,
with the same two upstream warnings. The internal backup has a 20 GiB cap and 100 GiB
free-space floor. Retained data controls were hash-verified and copied on both devices.

The pinned PanTS archive queue has started (metadata verified; large transfers in progress at the
recorded checkpoint). PANORAMA's separate queue subsequently started; its labels are commit-verified,
with CT batches downloading sequentially. Literature is not started. No source is registered ready
for training. See [the overnight handoff](operations/OVERNIGHT-ACQUISITION-2026-09-19.md) and
[acquisition queue](operations/DATA-ACQUISITION-QUEUE.md). Next parallel work: reviewed Git checkpoint,
supported Node/UI baseline, and remaining core cross-record tests. No Plan 04 code is authorized.

## September 18 read-only/code-health evidence (preserved history)

- `docs/capstone/` and `src/data/` are still untracked in this checkout. `.gitignore`, `AGENTS.md`,
  root `README.md`, and `docs/experiments.md` already contain local changes. Preserve all unrelated
  work; do not use `git add .` or sweep vendor/raw/generated files into a checkpoint.
- Source inspection counts 37 test functions across five files: collapse 6, anatomy-loss 7,
  deployment extras 8, prediction 7, serving 9. This is source inventory, not pytest collection.
- Historical `.venv312` reports Python 3.12.13; pytest and jsonschema are absent. Its NumPy and
  PyTorch modules are discoverable. It is not a clean capstone environment.
- Local Node is 20.20.1; the approved baseline remains Node 24. The current UI has build/dev/preview
  scripts but no `test:run` or browser test script. The build's post-processing script exists; inspect
  its side effects before using the build as a baseline.
- Two existing CPU-only test scripts were executed unchanged with bytecode writes disabled:
  collapse **6/6 passed**, anatomy-loss **7/7 passed**. See the dated test-inventory note for commands.
  These are historical-environment diagnostics, not full G0 or scientific-performance evidence.
- The historical training entry point accepts raw ID-file paths and the old config still points at
  `JHU-PanTS`. Do not launch it with a new drive path and assume capstone controls are satisfied.

## First implementation slice — clean test foundation

**Outcome:** a future session can reproduce the baseline and run meaningful fast checks without
the external datasets, a trained model, a network service, or a clinical participant.

1. Review and checkpoint the intended documentation/source files with explicit paths; verify ignores
   and scan staged changes for data, secrets, private notes, generated payloads, and vendor trees.
   Preserve the existing dirty worktree and old files. A remote push is a separate visible action;
   this handoff has neither committed nor pushed anything.
2. Use a new ignored `.venv-prowl` with Python 3.12; leave `.venv312` intact. Use standard `venv`/pip
   with reviewed direct runtime/test inputs and platform-labeled exact dependency records as Plan 10
   specifies. Do not install the broad historical requirements wholesale without dependency review.
3. Establish the approved Node 24 toolchain without changing the historical UI dependency lock
   merely to obtain a newer version. Record exact Python/Node/npm/package identities. Verify fresh
   installs; use the documented Node fallback only after a recorded compatibility failure.
4. Preserve first unchanged pytest collection/run output for all five test files, including errors,
   and the existing UI build result. Classify historical tests as retained/adapted/superseded/invalid
   before changing their assertions; do not force a green baseline by removing failures.
5. Add strict test discovery/markers and the smallest approved fast Python/UI test layer. Generated
   contract fixtures belong under `tests/fixtures/contracts/`; existing historical tests stay intact.
   Start with positive/negative schema, identity, cohort-role, duplicate and overlap controls under
   Plans 01/02/09. Do not implement Plan 04 workflow code in this slice.
6. Store only small diagnostic/test output below ignored `outputs/prowl/` during foundation setup,
   with recorded code/environment and synthetic fixture identities. No large scientific artifacts
   or fallback raw-data storage belong on the internal SSD.
7. Publish a readiness record stating what passed, what failed, and which checks still await real
   data/components. Close G0-verification only when its required evidence actually exists.

**Not in this slice:** training, source downloads, UI redesign, full DAG implementation, bulk history
migration, drive format/encryption changes, paid compute, or cloud uploads.

## Storage and acquisition branch

These tasks can proceed once their own choices are settled; they do not block generated test work.

**September 19 priority:** Quinton reports `JHU-PanTS` is broken with no read/write access. Fresh
downloads are now the active route, not a contingency. Prepare them alongside or immediately after
the clean test foundation; no old-drive recovery, finished UI, or retrieval system is required. See
[the acquisition queue](operations/DATA-ACQUISITION-QUEUE.md) for the concrete sequence and checks.
The new drive was reconnected, and D-258's scoped setup/checks have passed. The sequence below remains
the governing order; steps 1–2 passed their scoped checks, archive acquisition in step 3 completed
September 20, and extraction/source/cohort reconciliation remain open. Recheck live mount identity
before each operation after reconnection.

1. Keep the current unencrypted APFS configuration as explicitly chosen by Quinton (D-256).
   Encryption is not a prerequisite and no format change is requested. Select the independent
   backup destination; recheck live drive identity/capacity before writing. The September 18
   inventory found writable APFS and about 4 TB free.
2. Confirm exact test/root paths and a backup size budget that preserves internal-disk headroom if
   the Mac is chosen. Then run Plan 10's bounded capability and initial control-restore checks.
3. Prepare pinned, resumable PanTS acquisition with archive/checksum/extraction staging and a space
   estimate. Never blindly execute historical download scripts or automatically delete archives.
4. Reconcile new source IDs/labels/metadata against retained membership controls and register safe
   training descendants. Label partial acquisition honestly; do not claim a complete source or G1
   from a few readable cases. PANORAMA follows its own acquisition and G2 validation path.

## Before our first training experiment

Hold the experiment-strategy discussion required by Plan 06 after this prerequisite review and
before a training launch. Use the existing notebook as the starting point, not a replacement log.

Recommended question order, not registered experiments or permission to execute:

1. Can generated geometry, target, and metric fixtures expose a planted error?
2. Does one verified train-role case load and preserve its labels/grid through the proposed path?
3. Can the new pancreas-only localizer learn a tiny registered training set, save safely, and resume
   without changing its identity or selection history?
4. Can the new segmenter learn on its permitted training ROIs, and can the autonomous path restore
   predictions to source space without reference input at inference?
5. What do measured preparation/training/inference timings imply for the first useful development
   experiment and the ten-week resource budget?

Before each actual experiment, create its `CAP-EXP-NNN` plan in `docs/experiments.md`, naming the
question, prior evidence, exact data/config/initialization, smallest gate, budget, stop rule, outputs,
and what decision follows. Code prerequisites include role-valid cohort resolution, source/grid/target
checks, initialization denylist, unique run/checkpoint output, tested metrics/resume, and the relevant
preflight/resource controls. No historical trained checkpoint is capstone initialization.

Do not register an entire speculative queue with invented run IDs or thresholds now. Keep the older
ideas available and choose the next intervention from new evidence. G3 is required before expensive
baseline training; G2 is required for PANORAMA/mixed-source work, not a PanTS-only baseline.

## What remains explicitly open

- Exact independent backup target/budget, root capabilities, and live setup. Encryption is resolved:
  retain the existing unencrypted APFS configuration (D-256).
- Clean environment/locks, full historical baseline/classification, and executable G0 verification.
- Plan 04 explanation accepted September 20; explicit coding authorization and measured D-201 tool selection remain pending.
- D-202 vector tool, D-205 comparison, D-208 ordering/operating policy, and D-210 remote-compute need
  remain evidence-dependent. Their future deadlines do not block unrelated generated fixtures.
- Actual source integrity/cohort registration, stakeholder meeting, evaluation, integration, and
  release are later evidence gates, not completed by approving documentation.

This handoff is the immediate operating checklist. Update it when a step produces evidence; retain
the component plans, experiment notebook, decision register, and source-of-truth hierarchy.
