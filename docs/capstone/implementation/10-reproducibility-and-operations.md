# Reproducibility, storage, and compute

**Status:** Approved design — P10-01 through P10-24 approved 2026-09-18; physical setup and execution gates remain
**Target weeks:** 1–9; required before derived-artifact migration or expensive runs  
**Depends on:** Plan 01 artifact contract; Plan 04 state model; Plan 09 evidence contract  
**Last reviewed:** 2026-09-18

## Outcome

Make every meaningful PROWL result recoverable, attributable, and reproducible without turning the
capstone into an infrastructure project. A future session should be able to identify the correct
source snapshot, cohort, code, environment, configuration, model, prediction, evaluation, evidence
index, case package, and review history; determine which physical storage contains them; and rebuild
or restore them using a documented procedure.

The design is local-first and tailored to Quinton's single-user Apple Silicon workstation. The new
4 TB drive is the intended primary scientific-storage candidate, the old approximately 500 GB drive
is unusable per Quinton with recovery outside the active work, and GitHub remains the authority for code and small
permitted documentation. Rented compute remains an evidence-triggered option, not an assumed part of
the architecture.

## Current facts and constraints

The following is a planning snapshot, not a permanent hardware record:

- Quinton reports one older approximately 500 GB external drive containing the prior PanTS data and
  one new 4 TB external drive intended for the capstone.
- On 2026-09-18 the new drive was verified as `PROWL-Data`, writable APFS, USB/GUID, with about 4 TB
  free. It is unencrypted; scoped capability checks/root setup subsequently passed September 19. This
  supersedes the September 10 NTFS/read-only finding.
- On September 19 Quinton confirmed `JHU-PanTS` permits neither reads nor writes. Treat it as
  unusable with no source/backup role; fresh acquisition is now the active route (D-257). Retained
  local manifest and base split hashes match the prior audit; new raw sources must be pinned and
  reconciled. Recovery is outside the active work and cannot block it.
- The expected `PROWL-Data` path was initially absent September 19, then reconnected/verified.
  D-258's root setup, small filesystem tests, and independent synthetic restore passed. Internal
  backup is capped at 20 GiB with a 100 GiB free-space floor. PanTS archives are downloading; sources
  are not activated. See [the setup record](../operations/STORAGE-SETUP-2026-09-19.md).
- The first clean Python foundation passed 67 checks; registry/download guards bring the current
  suite to 87 CPU/synthetic passes with an exact hashed lock. The
  [foundation evidence](../testing/FOUNDATION-2026-09-19.md) and subsequent setup record do not imply
  full operations readiness.
- The historical PanTS root was `/Volumes/JHU-PanTS/PanTS/data/`; that path is deployment history,
  not a capstone identity.
- The internal filesystem reported approximately 191 GiB available on September 18.
- The repository's ignored `outputs/` tree was approximately 354 GB at the September 9 audit, dominated by historical caches
  and checkpoints. It is not migrated, renamed, or deleted by this plan.
- `ui/public/cases/` is approximately 201 MB and `docs/capstone/` is under 1 MB.
- The current `configs/level45.yaml` contains the historical absolute PanTS volume path and cache
  assumptions. Those settings are historical until migrated through a reviewed capstone config.
- Raw NIfTI files, archives, checkpoints, output trees, environments, secrets, and local reference
  material are already broadly excluded from Git; Plan 10 must verify that the rules are precise.
- The workstation is a 64 GB Apple M5 Pro Mac. MPS is the primary accelerator; it is not CUDA and
  cannot be assumed equivalent to a rented GPU.

No storage operation should infer that a drive is safe merely because its user-facing volume name
matches an old path.

## Core mental model

```text
GitHub: code + schemas + small permitted documentation
                         |
                         v
local root registry --> immutable source snapshots
                         |
                         v
             run-scoped temporary work
                         |
        validate + hash + complete marker
                         |
                         v
              published PROWL artifact
                  |               |
                  v               v
             restore copy     rebuild recipe
```

Three different assurances must not be conflated:

1. **Traceable** means the artifact names its source, code, environment, configuration, and parents.
2. **Rebuildable** means the retained recipe and inputs can recreate it within its declared
   reproducibility class.
3. **Restorable** means a separately stored verified copy has actually been restored successfully.

An ignored file is none of these by itself.

## Scope

- Physical storage roles for the internal SSD, new 4 TB drive, and old 500 GB drive.
- Logical root aliases and local path resolution.
- Canonical artifact layout, identity, hashing, publication, and immutability.
- Environment, code, command, configuration, and run capture.
- Backup tiers, retention, recovery, restore testing, and safe cleanup boundaries.
- External-drive, capacity, collision, lock, and partial-write preflight.
- Non-destructive migration of selected historical artifacts.
- Local MPS timing and evidence-based D-210 compute selection.
- Rented-compute authorization, licensing, transfer, and teardown boundary if triggered.
- Small-run reproduction recipes and release exclusion audit.

## Non-goals

- Reformatting, erasing, moving, or reorganizing either external drive during planning.
- Treating the new 4 TB drive as both a primary and an independent backup.
- Backing up every disposable cache or intermediate checkpoint.
- Putting raw images, licensed article text, models, or large outputs in GitHub.
- Adding a relational database, managed artifact store, Kubernetes, Airflow, or a cloud control plane.
- Requiring Docker for the local MPS workflow.
- Promising bitwise model equivalence across Apple MPS and CUDA.
- Buying compute, opening a paid account, or uploading data without Quinton's explicit authorization.

## Approved design decisions

| ID | Approved decision | Why | Avoids |
|---|---|---|---|
| P10-01 | After a non-destructive inventory and filesystem/write/recovery check, use the new 4 TB drive as the primary capstone source/artifact workspace. Keep code, environments, schemas, and small active documents on the internal SSD. | The internal disk is too constrained for the existing 354 GB output history plus two imaging sources and new experiments. | Internal-disk exhaustion and uncontrolled duplication. |
| P10-02 | Preserve the unavailable old drive for optional recovery. Reacquire pinned source data on `PROWL-Data` and reconcile it against retained controls; do not require the old drive to return or count it as a backup. | Quinton's September 18 direction permits redownload and removes old-drive availability from the critical path. | Blocking the project on suspect hardware or asserting unverified source equivalence. |
| P10-03 | Resolve physical paths through five logical aliases: `pants_source`, `panorama_source`, `prowl_artifacts`, `prowl_scratch`, and `prowl_backup`. Store local absolute paths plus expected volume UUID/filesystem in ignored `configs/local/roots.yaml`; commit a path-free example. | A volume path is deployment configuration, not scientific identity. | Hardcoded `/Users`/`/Volumes` paths and accidentally resolving the wrong same-named drive. |
| P10-04 | Make the external `prowl_artifacts` root authoritative for capstone-scale artifacts after verification. Reserve repository `outputs/prowl/` for synthetic/small development artifacts unless explicitly redirected; do not use a symlink or `latest` pointer as scientific authority. | It preserves the Plan 01 logical layout while keeping large data off the laptop. | Broken symlinks, hidden storage, and convenience paths becoming lineage. |
| P10-05 | Keep source roots logically immutable and separate source, artifact, scratch, and backup directories even when some live on the same 4 TB device. Record physical failure domains explicitly. | Logical separation prevents writes to sources; physical separation determines whether a backup is real. | Calling two folders on one disk “two copies.” |
| P10-06 | Use tiered backup: GitHub plus local copies for permitted irreplaceable records; verified second-media copies for keeper models/reviews/releases; rebuild recipes rather than full duplication for caches; and source checksums plus retained/downloadable source media as available. | The 500 GB drive cannot be assumed to hold a full 4 TB mirror. | An impossible all-or-nothing backup promise. |
| P10-07 | Historical migration is always inventory → copy → checksum/record-count verification → representative open/load test → retention hold. Never move in place or delete the source as part of migration; cleanup requires a later explicit reviewed list and Quinton authorization. | Current `outputs/` contains valuable but nonconforming history. | Destructive migration and silent relabeling of old evidence. |
| P10-08 | Prefer APFS for the canonical Mac-only artifact volume. If the new drive already uses another filesystem, do not reformat it automatically; first test atomic rename, append/locking, filename behavior, permissions, and disconnect recovery, then accept it or present a separate destructive reformat decision. | File-first integrity depends on filesystem behavior, while reformatting destroys data. | Assuming exFAT or another format has the required semantics, or erasing a drive without approval. |
| P10-09 | Write temporary output on the same destination filesystem, validate it, generate checksums, and publish with an atomic rename or final completion record written last. Downstream readers consume only complete artifacts. | Same-filesystem publication avoids cross-volume partial moves. | Interrupted files appearing valid. |
| P10-10 | Use SHA-256 content hashes and canonical derivation hashes. Compute file hashes during creation/copy where possible; source snapshots, contracts, cohorts, keeper models, evaluations, reviews, and releases receive complete inventories, while cache manifests record every written member and recipe identity. | Hashing is cheapest and most reliable at the moment bytes are already being written. | Repeated multi-hour rescans or weak filename identity. |
| P10-11 | Apply explicit retention classes: permanent source/control/release/review evidence; keeper; reproducible derived; exploratory pending decision; disposable scratch; and quarantined partial. No automated broad deletion is allowed. | Storage can be reclaimed without losing scientific decisions. | Either keeping everything forever or deleting the only useful copy. |
| P10-12 | Retain quarantined partials for a default 14-day diagnostic window and delete only from a generated, exact-path cleanup manifest after ownership/keeper checks and Quinton review. | Failures are useful briefly but should not consume storage indefinitely. | Immediate evidence loss or unsafe wildcard cleanup. |
| P10-13 | Expand each formal run's identity to include exact Python/Node/package locks, OS and hardware, PyTorch/MONAI/MPS details, locale/time zone, Git commit, dirty diff identity, entry point, resolved config, seeds, parent artifacts, commands, durations, and terminal state—never secret values. | Reproduction requires more than a checkpoint and a YAML file. | “Works on my machine” results and leaked credentials. |
| P10-14 | Smoke/diagnostic/exploratory runs may use dirty code only if a diff/untracked-source manifest is captured; controlled, confirmatory, publisher-test, stakeholder, and release artifacts require a clean committed revision. Dirty exploratory output cannot be promoted retroactively. | Early iteration remains fast while formal claims remain reproducible. | Losing useful exploration or presenting uncommitted code as a release. |
| P10-15 | Use Python 3.12 and Node 24 as approved in Plan 09. Keep declared runtime and test inputs separate, create a fully pinned macOS-arm64 Python environment record plus a compatible CI resolution, retain `package-lock.json`, and verify fresh installs with `npm ci` and a clean Python environment before G0. | Platform-specific scientific wheels and JavaScript dependencies both need exact evidence. | A vague minimum-version list or stale virtual environment becoming the lock. |
| P10-16 | Keep secrets outside manifests and Git in environment variables backed by a local ignored file or macOS credential storage. Commit only variable names/examples; redact values and user-specific absolute paths from logs, commands, screenshots, and release packages. | NCBI or future provider credentials are operational inputs, not scientific artifacts. | Credential leakage and nonportable documentation. |
| P10-17 | Every expensive or mutating run performs a fail-closed preflight for the expected volume UUID, filesystem capability, source readability, destination writability, free-space budget, lock ownership, source/artifact separation, configuration/schema validity, and required device/network/credential state. | Long jobs should fail before consuming hours or writing to the wrong place. | Mid-run disk failures and accidental fallback to an internal path. |
| P10-18 | Default to one MPS job and one writer per artifact family/root. Locks name owner/run/host/start/heartbeat; stale-lock takeover requires terminal-state and artifact validation rather than age alone. | Unified memory and file-first append/publish paths are shared resources. | Competing jobs destabilizing MPS or corrupting output. |
| P10-19 | A backup counts only after checksum verification and a scoped restore drill. Run drills after initial storage setup and before G8, including one keeper model/control artifact and one review-event snapshot. | A copy command does not prove recovery. | Discovering unreadable or incomplete backups during Week 9. |
| P10-20 | Keep local MPS as the default compute path. Resolve D-210 only after representative local timings and schedule projection; do not rent merely because CUDA may be faster. | Local execution minimizes transfer, licensing, cost, and environment variance. | Premature cloud scope. |
| P10-21 | Benchmark uncached/cached preparation, representative training, full-volume cascade inference, evaluation, retrieval build/query, artifact write/hash, and resume overhead. Record warm-up, sample/cohort, device, environment, bytes, peak memory, failures, and a schedule estimate with 25% contingency. | The critical path may be storage, CPU, MPS, or orchestration—not just training steps. | Choosing compute from one flattering microbenchmark. |
| P10-22 | Consider rented CUDA only if local correctness fails on a required operation, memory cannot support the approved workload, repeated MPS instability survives a bounded diagnosis, or the measured critical-path projection misses its gate with the 25% contingency. Provider and spend ceiling require separate Quinton approval. | This is the proposal's evidence-based escape hatch. | Hidden spending and an unjustified platform migration. |
| P10-23 | Before any remote upload, verify source terms and data boundary, run a matched synthetic/small smoke, encrypt transfer/storage where available, minimize uploaded artifacts, disable public sharing, capture the remote environment, download and verify keepers locally, and document deletion/teardown. The remote copy is never authoritative. | Public/de-identified research imaging can still carry use and storage obligations. | Data/license exposure, cloud-only results, and unreproducible CUDA claims. |
| P10-24 | Maintain executable reproduction recipes for one tiny imaging workflow, one retrieval build/query, one review append/reload, and the final release audit. Recipes verify expected IDs/hashes rather than merely completing without error. | Each major branch needs a bounded proof that its lineage is sufficient. | Discovering missing inputs only during final packaging. |

P10-01 does not authorize writing to the new drive. P10-07/P10-08 explicitly keep every current
file and filesystem intact until the drives are mounted, identified, and separately approved for
any material operation. P10-22 does not authorize a purchase or upload.

### September 18 approval and implementation boundary

Quinton approved the full Plan 10 design, including the staged-readiness refinement below, on
2026-09-18. This records design approval, not completed implementation. At that checkpoint exact
roots, capability tests, backup target/budget, and clean-environment verification remained pending.
Quinton subsequently explicitly chose to keep the drive unencrypted
(D-256, 2026-09-18). Encryption is no longer an open setup choice; no encryption/reformat action is
requested. On September 19, D-258 approved bounded root/capability setup and the internal backup
target/budget; those scoped checks and an initial synthetic restore passed. See the dated setup
record above. Source activation, real-artifact restore, production preflight, UI baseline and full
qualification remain pending; Plan 10 as a whole is not complete.

Quinton also confirmed that [`../../experiments.md`](../../experiments.md) remains the living
experiment notebook. Every experiment gets a written plan before compute, every attempt gets an
outcome, and every follow-up names the evidence and retained settings that motivate it. Link the
notebook to immutable Plan 06 experiment/run/evaluation records. Successful experiments inform new
designs; nulls, failures, and limitations remain equally visible.

### Staged readiness, not an all-components startup gate

1. **Foundation:** complete the relevant G0 design review, confirm the scoped setup targets and
   operational choices, then establish storage capabilities, roots, clean environments, synthetic
   contract tests, and an initial control-artifact backup/restore drill. These bounded setup steps
   produce readiness evidence; they do not require completed imaging, retrieval, or UI systems.
2. **Experiment readiness:** the intended run must have verified source/cohort roles, a pre-run
   notebook plan, tested code/configuration, run/checkpoint identity, relevant preflight/recovery
   checks, and measured resource headroom. Apply G1 and the relevant Plan 05/06/09 gates; G2 applies
   to PANORAMA work and G3 to expensive baseline training. Exercise the relevant imaging path before
   expensive imaging work, but do not require the completed retrieval/review recipes first.
3. **Delivery readiness:** before G8, complete the imaging, retrieval, review, and release recipes
   and the full release-critical restore/exclusion checks. Week 9 remains stabilization-only and
   Week 10 delivery-only.

The Plan 04 walkthrough and explicit implementation authorization remain prerequisites to its code
or Prefect spike. Plan 10 approval does not waive any scientific, holdout, or operational gate.

## Intended storage topology

```text
Internal Mac SSD
├── Git checkout and Git history
├── Python/Node environments and source code
├── small synthetic fixtures and active documents
└── optional bounded scratch only

New 4 TB external drive — candidate primary after verification
└── PROWL/
    ├── sources/        immutable pinned source snapshots or source registrations
    ├── artifacts/      canonical Plan 01 artifact tree
    ├── scratch/        run-scoped temporary and rebuildable work
    ├── quarantine/     incomplete/corrupt attempts pending review
    └── backup-staging/ copies awaiting verification; never called backup yet

Old ~500 GB external drive — optional recovery; unavailable
├── historical PanTS/source material
└── excluded from current backup capacity

GitHub
└── code, schemas, small configs/examples, documentation, and permitted control records only
```

The final directory names are recorded only after the actual drives are inventoried. Source and
artifact directories on the same 4 TB drive are separate logical roots but one physical failure
domain. The project does not claim an off-site backup unless one is actually configured and tested.

## Root registry contract

The proposed ignored local file `configs/local/roots.yaml` contains deployment information only:

- schema version;
- root alias;
- absolute local path;
- intended role and read/write policy;
- expected volume UUID and filesystem;
- optional source snapshot ID;
- verified-at timestamp and verification tool/version;
- minimum free-space/reserve policy;
- notes that are safe to keep locally.

The committed `configs/local/roots.example.yaml` contains fake/example paths and no volume UUIDs,
usernames, secrets, or institution-specific information. Scientific records persist only the alias,
source-relative path, snapshot identity, and content/derivation hash. Resolution must reject:

- an absent alias;
- an unexpected volume UUID even if the volume name matches;
- a writable source when read-only was required;
- a path outside the declared root after symlink/realpath resolution;
- `..`, absolute contract references, drive-letter paths, or URI scheme changes;
- two aliases that unexpectedly resolve to the same prohibited directory.

## Artifact publication and identity

The Plan 01 layout remains the logical baseline. Plan 10 adds operational areas without changing the
scientific meaning of existing IDs:

```text
<prowl_artifacts>/
├── sources/ manifests/ cohorts/ cache/ workflows/ models/
├── predictions/ evaluations/ retrieval/ case-packages/ reviews/ releases/
├── tests/runs/             immutable formal test evidence
├── environments/           dependency/platform identities and lock hashes
├── benchmarks/             D-210 timing/resource evidence
├── backup-catalogs/        what was copied, verified, and restored
└── quarantine/             invalid or incomplete attempts; never discoverable as valid
```

An artifact has two identities:

- **derivation identity:** canonical component version, relevant configuration, ordered parent IDs
  and hashes, and deterministic-policy inputs;
- **content identity:** SHA-256 over the canonical control record or file bytes, with a checksum
  inventory for a multi-file directory.

The derivation identity prevents accidental reuse after a meaningful input change. The content
identity detects collision, corruption, or nondeterministic output. If one derivation identity yields
different complete content, publication stops with a collision defect; it does not overwrite either
version.

### Publication sequence

1. Resolve aliases and validate inputs.
2. Acquire the appropriate resource/artifact-family lock.
3. Estimate output, temporary, checkpoint, and reserve space.
4. Create a run-scoped attempt below the destination filesystem.
5. Write records and compute member hashes as bytes are finalized.
6. Validate schema, counts, scientific constraints, and parent references.
7. Write `checksums.sha256` and the frozen controlling record.
8. Atomically rename the validated directory or write the completion record last.
9. Read back the completion record and a representative payload.
10. Release the lock and append the terminal run/stage event.

Readers require the controlling record, valid completion evidence, and matching identity. Directory
existence, a filename called `best.pt`, or an orchestration success badge is insufficient.

## Storage and retention matrix

| Class | Examples | Primary retention | Backup/rebuild policy | Cleanup boundary |
|---|---|---|---|---|
| Source/control permanent | Source snapshots, licenses, manifests, cohorts, mappings, question sets, schemas | Project life and final archive | Complete checksums; small permitted controls in Git; source media or redownload record | Never automatic |
| Review permanent | Append-only events, receipts, content-hashed snapshots | Project life and final archive | Snapshot after a review session/material change; verified second-media copy | Never delete individual events |
| Release evidence | Final models, selected predictions/evaluations, test reports, corpus/index manifest, case packages, docs | Project life and final archive | Verified second-media copy plus checksum/restore drill | Only through superseding release policy |
| Keeper | Best/decision-relevant checkpoint, preregistration, run manifest, logs/metrics | At least through final archive | Copy to independent available media; verify load and hash | Never until a newer retained keeper is approved |
| Controlled/confirmatory | All terminal evidence needed to support a comparison, including negative result | Through reporting and final audit | Keep small evidence permanently; preserve model if needed to reproduce claim | Explicit post-report review only |
| Exploratory | Diagnostic runs and candidate predictions | Until decision and weekly evidence consolidation | Manifest/metrics required; checkpoint optional by decision | Exact reviewed cleanup list |
| Reproducible derived | Prepared caches, regenerated meshes, nonkeeper prediction sets, rebuildable index | While useful/performance-saving | Retain recipe and parents; selective backup only | Delete only after rebuild proof and no descendant dependence |
| Scratch | Temporary arrays, downloads-in-progress, browser traces not used as evidence | Active attempt only | None | Run-scoped cleanup after terminal validation |
| Quarantined | Interrupted/corrupt/collision output | Default 14 days | None unless needed for defect evidence | Exact manifest after defect/ownership review |

Intermediate epoch checkpoints are not all keepers. A training run preserves its selected/best,
terminal, and any explicitly decision-relevant checkpoint; other epochs may be reclaimed after the
experiment decision and descendant audit. A model's manifest, metrics, config, environment, and run
record remain even if a nonkeeper binary is removed.

## Backup and restore policy

### Backup tiers

1. **Tier A — irreplaceable/small:** Git history, documentation, schemas, decisions, manifests,
   cohort definitions, experiment registry, review records, release controls, and license metadata.
   Use GitHub where permitted plus local verified copies.
2. **Tier B — expensive keepers:** selected model checkpoints, final prediction/evaluation evidence,
   corpus/index release snapshot, case packages, and presentation assets. Keep the primary plus a
   verified second-media copy when capacity permits.
3. **Tier C — reproducible large:** caches, exploratory predictions, and nonkeeper checkpoints.
   Preserve recipe/parents and selectively copy only high-cost artifacts.
4. **Tier D — disposable:** run scratch and verified-invalid partials after the diagnostic window.

The old drive is excluded from available backup targets while its reliability is uncertain. Bounded
copies of small controls/selected keepers on the internal SSD are a candidate independent destination
after capacity review; larger needs require another healthy medium. This does not require mirroring
all raw data or caches before synthetic work can begin. If a source remains
available from its publisher, the project retains exact acquisition metadata and checksums; it does
not pretend redownloadability is identical to a tested local backup.

### Restore drill

For each drill:

1. select a backup-catalog entry without reading from the primary payload;
2. restore into a new scoped temporary directory;
3. validate member count, bytes, hashes, schemas, and parent references;
4. load/use the artifact in its smallest real consumer;
5. record duration, result, source/destination failure domain, and tool versions;
6. remove the drill copy only after its evidence record is complete.

Initial drills use a small control artifact and a synthetic review-event snapshot (or a verified
keeper if available); a working review UI or new trained model is not required. Pre-G8 drills cover
the release candidate's critical Tier A/B set and actual produced review evidence.

## Environment and run identity

### Supported local baseline

- macOS on Apple Silicon;
- exact Python 3.12 patch release recorded per environment;
- Node 24 LTS with `npm ci` from the committed UI lockfile;
- exact installed Python package inventory and hash;
- PyTorch, MONAI, NumPy, nibabel, MLflow, orchestration, retrieval, test, and browser-tool versions;
- MPS availability, fallback setting, device selection, and relevant framework flags;
- machine model, CPU/GPU/unified memory, OS build, filesystem types, locale, and time zone;
- environment-variable names that affect behavior, with sensitive values omitted.

The environment record distinguishes declared dependencies, resolved lock evidence, and the actual
installed inventory. Passing only one of those checks is insufficient.

### Run code classes

| Run class | Dirty code allowed? | Promotion |
|---|:---:|---|
| Smoke/diagnostic | Yes, with diff and untracked-source inventory | Cannot become a scientific claim |
| Exploratory | Yes, with complete capture | Informs a new future controlled design only |
| Controlled/confirmatory | No | Eligible after preregistration and required gates |
| Publisher-test | No | One frozen execution under Plan 06 |
| Stakeholder/release | No | Requires clean revision and release matrix |

For a permitted dirty run, capture the Git base commit, patch hash/file, untracked source file hashes,
entry point, and configuration before compute begins. Binary outputs, raw data, environments, and
ignored scientific artifacts are not swept into a source bundle. If source capture is incomplete,
the run is diagnostic only.

## Preflight contract

The preflight produces a signed-off machine-readable record and stops before mutation when a hard
check fails.

### Required checks

- expected aliases exist and resolve within the expected volume UUID;
- filesystem and tested capabilities match the root registry;
- source root is readable and its controlling snapshot/checksum is present;
- artifact/scratch roots are writable and not inside a source root;
- requested parents are complete and hashes/config/schema versions match;
- cohort role permits the requested operation;
- output derivation ID is unoccupied or exactly reusable under policy;
- no conflicting accelerator, writer, run, or artifact-family lock exists;
- required free space exceeds planned outputs + worst-case temporary bytes + checkpoint reserve +
  operational headroom;
- Python/Node/environment identity matches the requested run class;
- MPS/CPU/CUDA device behavior is explicit;
- required network/license/credential state exists for acquisition tasks only;
- Mac is on reliable power and the external volume is stable for long work, reported as warnings or
  hard requirements according to run class.

Operational headroom begins as the larger of 100 GiB or 10% of the artifact volume. The preflight
also uses a component-specific estimate; if an estimate is unavailable, a smoke run must measure it
before the full run. Quinton may revise the reserve after the 4 TB inventory, but a run cannot silently
consume it.

## Non-destructive storage setup and migration

### Phase A — identify, do not write

1. Mount one external drive at a time when practical.
2. Record device identifier, volume UUID, volume name, filesystem, capacity, free bytes, and whether
   the drive reports hardware health information.
3. Inventory top-level paths, counts, sizes, existing source manifests/checksums, and obvious partials.
4. If the old drive becomes available, optionally compare it with historical PanTS documentation
   without assuming a path match proves content identity. Its recovery is not a setup prerequisite.
5. Review the inventory with Quinton before assigning writable roles.

### Phase B — verify the 4 TB candidate

1. Run a scoped temporary write/read/hash/rename/append/lock/disconnect-recovery test.
2. Confirm usable capacity after the headroom reserve and expected PanTS/PANORAMA/artifact footprint.
3. If the filesystem does not pass, stop and present alternatives; do not reformat automatically.
4. Create only the approved root directories and registry entries.
5. Run a small publication and restore-control test before any bulk copy.

### Phase C — migrate selected history

1. Create a frozen source inventory of each selected historical tree.
2. Copy into a clearly labeled `historical-import` or staging area; never label it capstone-conforming
   merely because it was copied.
3. Compare total bytes, file counts, complete checksum inventory, and representative application
   loads.
4. Write a migration record linking old and new locations by content identity.
5. Hold the source intact through at least the next verified backup/restore point.
6. Propose any later cleanup as exact paths and bytes with keeper/descendant checks; require separate
   Quinton authorization.

The current 354 GB `outputs/` tree remains untouched until an inventory distinguishes irreplaceable
keepers, controlled evidence, rebuildable caches, and disposable partials.

## Compute benchmark and D-210

### Benchmark workloads

| Workload | Representative measurement |
|---|---|
| Source/read path | Sequential and case-wise reads from the selected external source; record cold/warm distinction |
| Preparation | Fixed train-role study sample through uncached then cached preprocessing |
| Training | Warm-up followed by a fixed timed iteration window using the approved baseline tensor/loader shape |
| Inference | Full autonomous cascade on a fixed development sample containing positive, negative, and difficult cases |
| Evaluation | Metric and report generation from a fixed prediction set |
| Retrieval | Corpus normalization/index build plus fixed query set, recording persistence and reopen |
| Artifacts | Write, hash, publish, validate, and reopen representative model/prediction/index packages |
| Recovery | Resume from a controlled interruption and measure lost/repeated work |

Each result names the exact code, environment, data/cohort, cache state, drive/root, device, batch and
worker settings, start/end time, wall time, throughput, memory, bytes read/written, failures/fallbacks,
and repeated-run variability. Projections include planned run count and 25% contingency.

### Decision rule

Remain local when the approved baseline, required controlled comparison, evaluation, and integration
work fit the gate schedule with contingency and no correctness/memory blocker. Open a rented-compute
proposal only when one P10-22 trigger occurs. That proposal must state:

- the blocked/late workload and local benchmark evidence;
- proposed provider/hardware and matched smoke design;
- expected wall time, transfer/storage time, and total cost under a Quinton-approved ceiling;
- source license/privacy authorization and exact upload set;
- environment/seed/comparability plan;
- artifact retrieval, checksum, teardown, and fallback;
- what happens if the remote result differs from MPS.

A CUDA result is a distinct environment, not a faster continuation of an MPS run. The comparison
records hardware as a factor and does not demand bitwise equality.

## Reproduction recipes

Four bounded recipes become executable evidence:

1. **Tiny imaging:** synthetic/pinned tiny scan → manifest/cohort → preprocessing → model smoke →
   prediction/evaluation package, with expected IDs and invariants.
2. **Retrieval:** pinned small permitted corpus → lexical/vector candidate → fixed queries → ranked
   passage/evaluation record, with expected counts/identities and tolerance class.
3. **Review:** case package → load → accept/edit-required/reject append → durable receipt → reload and
   revision-chain verification.
4. **Release audit:** clean revision → dependency/secret/license/path scan → checksum validation →
   permitted package reconstruction and independent manifest verification.

The recipes do not need to recreate a week-long stochastic model bit-for-bit. They must recreate the
declared deterministic artifacts exactly and verify numerical outputs under the approved Plan 09
tolerance/statistical class.

## Implementation sequence

1. Record approval of P10-01 through P10-24 and staged readiness (completed 2026-09-18).
2. Inventory the new 4 TB drive; record the old drive as unavailable/optional and use pinned fresh
   source acquisition as the recovery route.
3. Retain unencrypted APFS under D-256. Confirm the exact writable test/root targets, independent
   backup target and size budget; test capability before creating the local root registry/example.
4. Extend artifact/run/test schemas for operational identity and backup catalogs.
5. Build root resolver, preflight, scoped locks, atomic publication, and quarantine behavior with
   synthetic temporary roots.
6. Establish clean Python 3.12/Node 24 environments and dependency lock evidence.
7. Baseline/classify the Plan 09 test suite, then run storage/identity/failure tests.
8. Create backup catalogs and pass the initial restore drills.
9. Inventory selected historical outputs; copy only approved keepers/control evidence if needed.
   Optional historical migration cannot block a fresh-data start.
10. Explain Plan 04 to Quinton, obtain explicit implementation authorization, and only then perform
    its bounded orchestration spike against these contracts.
11. Run local storage/compute benchmarks and resolve or retain D-210.
12. Register the next experiment's plan in `docs/experiments.md`, satisfy its own prerequisites, and
    execute the relevant bounded reproduction/smoke checks before expensive work in that branch.
    Imaging experimentation does not wait for a completed retrieval or review system.
13. Complete all four reproduction recipes and repeat release-critical restore/exclusion checks
    before G8. Record every experimental attempt and its next decision in the living notebook.

Steps 2–3 are user-visible checkpoints. No bulk migration, reformat, deletion, paid compute, or remote
upload is implicit in design approval.

## Test matrix

| Test | Expected result |
|---|---|
| Alias absent | Fails before work and names the missing alias; no fallback to repository/internal disk |
| Same volume name, wrong UUID | Fails closed |
| Source/artifact alias collision | Fails before mutation |
| Symlink/path traversal escape | Rejected after real-path resolution |
| Filesystem capability control | Write/read/hash/rename/append/lock/reopen succeeds or volume is rejected for that role |
| Low capacity | Run blocks before allocation and reports estimate/reserve/available bytes |
| Same derivation, different content | Collision quarantined; existing complete artifact untouched |
| Interrupted write | Attempt remains incomplete/quarantined and undiscoverable to readers |
| Competing writer/MPS job | Second owner fails or waits under explicit policy; never writes concurrently by accident |
| Stale lock | Takeover requires terminal/artifact validation and records the decision |
| Source/config/code change | New derivation identity; prior artifact remains immutable |
| Dirty controlled run | Rejected before compute |
| Dirty exploratory run | Complete diff/source inventory captured and promotion prohibited |
| Secret/path redaction | Manifest/log/release contains names/aliases only, never secret values or user-specific absolute paths |
| Backup copy | Hash/catalog validation plus consumer-level restore succeeds from separate media |
| Corrupt backup member | Restore fails clearly; primary remains untouched |
| Historical migration | Counts/bytes/hashes/load test match while original remains in place |
| Missing external drive mid-run | Terminal failure/partial state recorded; complete publication impossible; valid resume path remains |
| Clean environment install | Python and UI fast suites run from locks without undeclared global packages |
| Matched MPS benchmark | Complete environment/data/cache/timing record and schedule projection produced |
| Remote-compute proposal | Cannot execute without license boundary, spend ceiling, explicit Quinton approval, and teardown plan |
| Restricted release member | Release audit fails and names the prohibited artifact/path |
| Reproduction recipe | Expected identities, counts, hashes, and declared tolerance checks pass |

## Failure modes and fallbacks

| Failure | Trigger | Primary response | Fallback |
|---|---|---|---|
| 4 TB drive has incompatible filesystem | Capability test fails | Present preserve/copy/reformat alternatives with data-loss implications | Use it for transport/backup only; choose another verified canonical root |
| 4 TB drive lacks expected free space | Inventory/projection fails reserve | Reduce retained caches/intermediates after exact cleanup review | Add separate storage; do not consume safety reserve silently |
| Old drive unavailable | Missing usable mount or user reports failure | Preserve it for optional recovery and reacquire a pinned publisher snapshot | Reconcile fresh sources with surviving local controls; select a healthy independent backup target |
| Hardware health data unavailable over USB | SMART unavailable | Rely on read verification, checksum inventory, filesystem check, and backup | Replace suspect drive if I/O errors occur |
| Full hashing is initially slow | Source/copy inventory takes hours | Hash while copying/writing and checkpoint inventory progress | Use publisher checksums plus explicitly labeled provisional assurance; no formal descendant until complete |
| External disconnect occurs | I/O/mount identity changes | Fail run, quarantine partial, verify volume and parents, then resume from last complete stage | Rebuild affected stage only |
| Backup does not restore | Hash/load failure | Mark backup invalid, recopy from verified primary, repeat drill | Rebuild from source if primary is already unavailable |
| Locked Python graph fails | Fresh install conflict | Diagnose the smallest incompatible direct dependency and create a reviewed lock revision | Use named supported Python 3.12 patch/platform fallback; keep G0 open |
| Node 24 incompatibility appears | `npm ci`/build/test fails | Update supported dependencies under a lock revision | Use supported Node 22 LTS temporarily with an expiry and compatibility record |
| MPS workload misses schedule | Projection with contingency exceeds gate | Open D-210 remote proposal and compare transfer/compute costs | Reduce experimental horizon/cohort honestly if remote path is not approved |
| Remote upload is not permitted | License/privacy review fails | Keep processing local | Reduce scope or use permitted synthetic/public benchmark; no upload workaround |
| CUDA and MPS differ materially | Matched smoke outside tolerance | Treat hardware as experimental factor and validate selected platform end-to-end | Keep local MPS authority or rerun the full controlled comparison on one platform |
| `outputs/` migration is ambiguous | Keeper/parent status unknown | Leave it untouched and classify incrementally | Import only named verified artifacts; no bulk relabel |
| Week 9 storage crisis | Reserve trigger reached | Delete only pre-approved disposable/rebuildable members from exact manifest | Add storage; do not improvise destructive cleanup |

## Plan readiness gate

Plan 10 may move to `Ready` when:

- [x] Quinton approved P10-01 through P10-24 and staged readiness on 2026-09-18.
- [x] `PROWL-Data` was inventoried read-only on September 18; old-drive recovery is optional under
  Quinton's direction and its availability is excluded from prerequisites.
- [ ] The 4 TB drive's volume identity, filesystem capability, usable capacity, and assigned roots are
  approved.
- [x] Old drive is recorded as unavailable; no source-byte integrity or backup reliability is claimed.
- [ ] Root aliases, artifact root, scratch root, and backup failure domains are frozen.
- [x] Environment/lock strategy and run-class policy are approved; Python evidence exists, UI/full verification remains pending.
- [x] Retention, backup, restore, cleanup, and migration policies are approved; scoped backup target/budget resolved under D-258.
- [x] Preflight, benchmark, and D-210 decision protocols are approved; D-210 itself remains evidence-dependent.
- [ ] No open decision can change the storage or environment architecture of an imminent run.

Design approval precedes physical setup. Bounded foundation setup can produce the missing readiness
evidence after its scoped targets and G0/design prerequisites are confirmed; it does not require all
completion evidence first. Plan 10 is not globally `Ready` yet, and expensive capstone runs remain
gated by the experiment-readiness stage above.

## Completion gate

- [ ] Root registry resolves exact expected volumes and fails closed on mismatch.
- [ ] Canonical 4 TB artifact/scratch layout passes the filesystem capability test.
- [ ] Clean Python 3.12 and Node 24 environments install and pass their Plan 09 gates.
- [ ] Artifact publication, collision, lock, disconnect, partial-write, and resume tests pass.
- [ ] Initial Tier A/B backup catalogs and restore drills pass from a distinct available medium.
- [ ] Selected historical keepers/control records are copied and verified without changing originals.
- [ ] One imaging, retrieval, and review recipe reproduces its expected evidence.
- [ ] Local resource benchmark and schedule projection are immutable and D-210 is recorded.
- [ ] Any approved remote run satisfies license, cost, environment, retrieval, and teardown evidence.
- [ ] Release audit rejects raw/restricted/secret/absolute-path material and validates every included
  checksum.

## Planned artifacts

- [`../operations/README.md`](../operations/README.md)
- [`../operations/CURRENT-STORAGE-INVENTORY.md`](../operations/CURRENT-STORAGE-INVENTORY.md)
- [`../operations/STORAGE-ROOTS-AND-ARTIFACTS.md`](../operations/STORAGE-ROOTS-AND-ARTIFACTS.md)
- [`../operations/ENVIRONMENT-AND-RUN-IDENTITY.md`](../operations/ENVIRONMENT-AND-RUN-IDENTITY.md)
- [`../operations/BACKUP-RETENTION-AND-RECOVERY.md`](../operations/BACKUP-RETENTION-AND-RECOVERY.md)
- [`../operations/PREFLIGHT-MIGRATION-AND-REPRODUCTION.md`](../operations/PREFLIGHT-MIGRATION-AND-REPRODUCTION.md)
- [`../operations/COMPUTE-DECISION-PROTOCOL.md`](../operations/COMPUTE-DECISION-PROTOCOL.md)
- ignored setup-only `configs/local/roots.yaml`, reviewable example/schema, with source activation pending;
- Python environment locks/installed records; Node/UI evidence remains pending;
- future immutable preflight, benchmark, migration, backup, restore, and reproduction records.

## Handoff

All twelve designs are approved and the focused prerequisite review is recorded in
[`../IMPLEMENTATION-START.md`](../IMPLEMENTATION-START.md). Scoped Python, filesystem/root, and
initial synthetic backup/restore checks passed on September 19; PanTS archive acquisition started.
Continue source/extraction reconciliation, Node/UI verification, and production preflight/restore
qualification before declaring full operational readiness. Old-drive recovery is optional. Real-data
runs require fresh pinned and verified source snapshots. Plan 10 supplies the boundaries needed to
make Plans 04–09 executable. Plan 11 may continue as a planning document in parallel; Plan 12 uses
the same backup, reproduction, clean-code, and release-exclusion rules for G8/G9.
