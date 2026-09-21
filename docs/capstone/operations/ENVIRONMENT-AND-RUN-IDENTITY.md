# Environment and run identity

**Status:** Approved Plan 10 design; first Python foundation lock/install verified; wider verification pending  
**Decisions:** P10-13 through P10-16 and P10-24  
**Last reviewed:** 2026-09-19

The first CPU/synthetic Python slice now has direct inputs, a hashed macOS-arm64/Python-3.12 lock,
an independently checked installed inventory, and 67 passing tests. See
[the September 19 record](../testing/FOUNDATION-2026-09-19.md). Node/UI, Linux, actual MPS/scientific
execution, broader component dependencies, and full environment qualification remain pending.

## Purpose

A run is reproducible only if its code, environment, inputs, configuration, and execution policy are
identifiable before the result is known. This document defines what PROWL captures and which run
classes require a clean committed revision.

## Environment layers

| Layer | What it answers | Required evidence |
|---|---|---|
| Declared inputs | What packages/tools does the project intentionally require? | Separate runtime and development/test dependency files; UI `package.json` |
| Resolved lock | What exact dependency graph was selected for a platform? | Platform-labeled Python lock/freeze with hash; `package-lock.json` hash |
| Installed inventory | What was actually present for this run? | Python package inventory, Node/npm inventory, executable paths/versions, content hash |
| Platform/device | What system executed it? | OS build, architecture, hardware, memory, MPS/CPU/CUDA, filesystem and critical flags |
| Run capture | How were those pieces used? | Run manifest with code/config/input/stage/command/timing identity |

No single layer substitutes for the others. A lockfile does not prove the current environment matches
it, and `pip freeze` alone does not explain which dependencies are intentional.

## Supported baseline

### Python

- Major/minor: Python 3.12.
- Exact patch and executable path captured per environment.
- Clean capstone environment created independently of historical `.venv312`.
- Runtime dependencies separated from development/test dependencies.
- macOS-arm64 exact resolution recorded because PyTorch/scientific wheels are platform-sensitive.
- A compatible Linux/CPU CI resolution may differ in platform wheels but must derive from the same
  reviewed direct requirements and remain explicitly separate.
- Clean installation and the Plan 09 fast/integration commands are the acceptance proof.

The historical environment remains useful for reproducing prior work but cannot define a formal
capstone run.

### JavaScript/UI

- Node 24 LTS baseline.
- Exact Node and npm versions recorded.
- Committed `package.json` plus `package-lock.json`.
- `npm ci`, unit/component tests, and production build required from a clean install.
- Node 22 LTS is a temporary recorded fallback only if the current UI/toolchain has an unresolved
  Node 24 compatibility defect; it receives an expiry and cannot be selected silently.

### System and accelerator

Capture:

- machine model and Apple Silicon architecture;
- macOS product/build version;
- CPU/GPU/Neural Engine description and unified memory;
- PyTorch device selection and MPS availability/built flags;
- relevant fallback, determinism, precision, thread, and worker settings;
- library versions that control image geometry, training, inference, metrics, retrieval, serving,
  orchestration, UI testing, and browser behavior;
- filesystem type for source, scratch, and artifact roots;
- locale and time zone;
- browser name/version for browser or stakeholder evidence.

MPS and CUDA environments are different reproduction classes. A remote CUDA environment gets its own
lock/inventory and matched validation; it never inherits the local environment ID.

## Proposed dependency artifacts

Exact filenames may be reconciled with the current repository during implementation, but the roles
must remain distinct:

```text
requirements/
├── runtime.in                   reviewed direct runtime requirements
├── dev.in                       reviewed test/development additions
└── locks/
    ├── macos-arm64-py312.txt    exact resolved local environment
    └── linux-cpu-py312.txt      exact CI-compatible environment

ui/
├── package.json
└── package-lock.json
```

If a lock-generation tool is introduced, it must be recorded and the generated files remain
reviewable. The project does not adopt a new environment manager merely for style; the simplest
approach that produces a clean repeatable install is preferred.

## Environment record

Each formal environment record includes:

- environment ID/schema version/status;
- created/verified timestamps;
- role: local MPS, local CPU control, Linux CI, or approved remote CUDA;
- Python/Node/npm executable versions and normalized locations;
- direct-input hashes, resolved-lock hashes, installed-inventory hash;
- installed packages and versions;
- OS/hardware/device/filesystem facts;
- relevant environment variable **names** and redacted presence state;
- container/image ID if a remote provider happens to use one;
- clean-install commands and their result artifact IDs;
- known limitations, fallback behavior, and expiry if temporary;
- Plan 09 test-run IDs that certify it.

Absolute executable paths can appear only in the local operational record. They are redacted from a
public release while version and content identities remain.

## Code identity

Every run records:

- Git repository identity and commit SHA;
- branch/reference as convenience context only;
- clean/dirty state determined before execution;
- entry point and component/contract versions;
- submodule or external source dependency identities when used;
- exact resolved config and content hash;
- source patch/untracked-source inventory for a permitted dirty run;
- code capture timestamp before compute;
- run class and promotion restriction.

Branch name is not scientific identity because it can move. Commit SHA and captured dirty change
identity are.

### Dirty source capture

For allowed smoke/diagnostic/exploratory runs:

1. record the base commit;
2. capture staged and unstaged textual diffs into a run-scoped source record;
3. inventory/hash untracked source/config/schema files in approved code paths;
4. exclude raw data, outputs, environments, secrets, binaries, and caches;
5. hash the complete source-capture manifest;
6. mark the run non-promotable.

If an ignored or untracked file affects behavior and is not captured as configuration/artifact/source,
the run cannot support a claim.

## Run classes and promotion

| Class | Purpose | Clean revision? | Preregistration? | Can select a release? |
|---|---|:---:|:---:|:---:|
| Smoke | Prove one path executes | Optional with capture | No | No |
| Diagnostic | Isolate a defect or mechanism | Optional with capture | Usually no | No |
| Exploratory | Generate a future hypothesis | Optional with capture | Logged intent | No |
| Controlled | Test a frozen comparison | Required | Required under Plan 06 | Eligible evidence |
| Confirmatory | Repeat/verify a selected result | Required | Required | Eligible evidence |
| Publisher-test | One final untouched evaluation | Required | Frozen candidate/policy | Yes, under Plan 06 |
| Stakeholder | Record a representative review session | Required | Frozen session build/tasks | Yes, usability evidence |
| Release | Produce/audit delivery package | Required | Frozen release candidate | Yes |

A favorable dirty or exploratory result cannot be “cleaned up” into formal evidence after the output
is seen. Re-run the frozen design from a clean revision.

## Configuration identity

The run stores:

- user-supplied configuration sources and hashes;
- defaults and overrides;
- fully resolved typed configuration in canonical form;
- redacted operational root aliases rather than absolute paths;
- seed set and deterministic/tolerance policy;
- source/cohort/model/index/prediction/evaluation policy IDs;
- hardware-sensitive choices such as device, precision, workers, cache state, and ROI tensor policy;
- forbidden or irrelevant values excluded from a component's derivation identity with rationale.

CLI arguments are parsed into the resolved config; a human-readable command is useful evidence but is
not the sole configuration authority.

## Command and event capture

Record commands in structured form:

- executable/component intent;
- redacted argument vector;
- working-directory alias/repository-relative path;
- environment identity;
- start/end/exit status;
- stdout/stderr log references and hashes;
- signal/interruption/retry state;
- parent and output artifact IDs;
- stage attempt and orchestrator metadata as secondary evidence.

Secret values never appear in the argument vector or logs. Prefer environment/credential lookup over
secret command-line flags. User-specific absolute paths are translated to root aliases in portable
evidence.

## Randomness and reproducibility classes

Each relevant result declares one of:

| Class | Expected reproduction |
|---|---|
| Exact deterministic | Same canonical bytes/IDs/hashes |
| Deterministic within tolerance | Same structured result under named numerical tolerance |
| Seeded stochastic | Same design and seed with expected distribution/tolerance; bitwise equality not promised |
| Statistical replication | Same frozen design and comparable aggregate result with uncertainty |
| Manual observational | Signed checklist/screenshot/session evidence; not algorithmically replayable |

MPS training is generally seeded stochastic/statistical, not promised bitwise. Contract
serialization, cohort membership, source inventories, review events, and release checksums should be
exact deterministic.

## Secret and path policy

- Secrets live in an ignored local file or macOS credential storage and are supplied as environment
  variables at runtime.
- Commit a `.env.example`-style name/description file only where helpful; never example real values.
- Manifests record whether a required credential was available, not its value or irreversible hash.
- Logs redact access tokens, API keys, authorization headers, signed URLs, and query-string secrets.
- Screenshots and error messages undergo the same audit.
- Absolute user/mount paths can remain in local diagnostics but are replaced by aliases in
  scientific/release records.
- A suspected leak stops the operation, rotates/revokes the credential where applicable, removes
  exposed public artifacts, and records an incident.

## Minimum run record extensions

The existing Plan 01 run-manifest schema is the starting point. Plan 10 must add or link:

- run class and promotion eligibility;
- failure-domain/root alias references;
- expanded code capture and dirty-source record;
- environment ID plus lock/installed inventory references;
- redacted structured command;
- complete config and seed policy;
- stage retry/resume/reuse events;
- resource estimates and actual measurements;
- retention/keeper classification;
- test/preflight evidence IDs;
- terminal selection/decision/evaluation references.

Large details should live in linked immutable records rather than making one JSON file unbounded.

## Required tests

- clean environment matches lock and runs required commands;
- undeclared/global-only dependency is detected;
- changed lock or installed inventory changes environment identity;
- Node `npm ci` reproduces dependency tree/build;
- clean/dirty classification is correct before compute;
- dirty capture includes staged/unstaged/untracked source but excludes secrets/data/outputs;
- dirty controlled/publisher-test/stakeholder/release run is rejected;
- changed relevant config changes derivation ID; irrelevant mount path does not;
- secret values and absolute paths are absent from portable records/log controls;
- environment, code, config, inputs, and terminal outputs cross-validate.
