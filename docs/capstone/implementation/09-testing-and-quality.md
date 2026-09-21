# Testing and quality strategy

**Status:** Approved design; first Python foundation verified, full production acceptance gated on verification  
**Target weeks:** 1–9; required at every implementation boundary  
**Depends on:** Plan 01 contracts; informs Plans 02–08 and 10–12  
**Last reviewed:** 2026-09-19

## Outcome

Create one understandable, runnable quality system that tells Quinton what was tested, on which
environment and artifacts, with what result, and what remains untested. The system covers pure logic,
schemas, data integrity, medical-image geometry, training/inference boundaries, metrics, retrieval,
the review UI, orchestration recovery, and the final end-to-end workflow without putting protected
data or large scientific jobs into ordinary CI.

Passing tests mean the implementation behaved according to its approved contracts. They do not prove
clinical validity, diagnostic safety, or scientific superiority.

## Current implementation progress

The September 19 clean `.venv-prowl` install and hashed platform lock passed dependency checks.
All 37 historical tests passed unchanged, then 30 contract checks produced a 67-pass fast suite.
Strict pytest configuration and synthetic fixture locations now exist. Full G0, Node/UI/browser,
application-level contract enforcement, and CI remain pending. See
[the foundation record](../testing/FOUNDATION-2026-09-19.md).

## September 9 baseline (historical)

The repository currently has:

- 37 Python test functions in five files;
- historical coverage of anatomy-label collapse/loss, deployment-cohort helpers, prediction recipe
  checks, FastAPI serving behavior, and sanitization;
- no installed `pytest` or `jsonschema` in `.venv312`;
- system Python 3.14.6 and a known working project environment on Python 3.12.13;
- broad minimum-version runtime requirements rather than a capstone lock;
- no `pytest.ini`, `pyproject.toml` test configuration, marker registry, coverage configuration, or
  committed test-result protocol;
- a one-time contract validation record, but no committed executable schema suite;
- a Vite/React UI with `npm run build` but no unit/component/browser test script;
- Node 20.20.1 locally, which is end-of-life as of the current planning date;
- no GitHub Actions workflow.

The existing tests are evidence and must be classified before behavior changes. Their existence does
not satisfy G0 until a documented environment can collect and run them.

## Core mental model

```text
approved requirement / risk / contract
                |
                v
independent test oracle + controlled fixture
                |
                v
fast test | integration test | real-data/MPS test | manual review
                |
                v
machine-readable result + environment/artifact identity + explicit skips
```

A test belongs in the cheapest layer capable of finding the failure. Expensive real-data checks do
not replace unit tests, and fast mocks do not certify NIfTI geometry, MPS behavior, NiiVue rendering,
or end-to-end persistence.

## Scope

- Canonical Python and Node test environments and dependency boundaries.
- Test configuration, discovery, markers, commands, time budgets, and result artifacts.
- Inventory/migration of all existing tests.
- Unit, schema/contract, data-quality, geometry, model, metric, retrieval, service, orchestration, UI,
  persistence, regression, failure-injection, and end-to-end tests.
- Synthetic/golden/local-real fixture policy and independent scientific oracles.
- Risk/requirement-to-test traceability.
- GitHub Actions for safe public/synthetic fast checks.
- Local MPS, external-drive, real-data, browser, and release-candidate verification.
- Explicit skip, expected-failure, flaky-test, and defect handling.

## Non-goals

- Running training or full-volume publisher-test evaluation on every code change.
- Uploading CTs, masks, restricted literature, checkpoints, secrets, or private paths to GitHub.
- Declaring clinical or scientific validity from software tests.
- Maximizing a repository-wide line-coverage percentage.
- Requiring bitwise equality from stochastic/MPS operations that only promise numeric tolerance.
- Adding a large testing platform, paid service, self-hosted runner, or browser matrix without measured
  value.
- Changing product behavior merely to preserve a stale historical test.

## Proposed design decisions

| ID | Proposed decision | Why | Avoids |
|---|---|---|---|
| P09-01 | Standardize capstone verification on Python 3.12 and Node 24 LTS. Create a clean capstone virtual environment rather than treating system Python 3.14 or the historical `.venv312` contents as reproducible. Plan 10 freezes exact environment identities. | Python 3.12 is the known-compatible scientific baseline; Node 20 is now EOL. | Environment drift and accidental success from an old local install. |
| P09-02 | Keep runtime dependencies separate from development/test dependencies. The initial Python test layer uses `pytest`, `pytest-cov`, `jsonschema` with format validation, and `httpx` for HTTP tests; add plugins only for a demonstrated need. | The current requirements omit the tools needed to run the existing tests/contracts. | A bloated test environment or hidden global tools. |
| P09-03 | Capture a baseline collection/run of all 37 historical tests before reorganizing them. Classify each as retained, adapted, superseded, or invalid, with rationale; never silently delete or weaken one. | Historical regressions still matter, but some assumptions predate the capstone contracts. | Losing useful tests or treating outdated expectations as source of truth. |
| P09-04 | Register strict markers and make `fast` the ordinary default: no network, external drive, licensed data, MPS requirement, browser download, or expensive model. Unknown markers and unexpected collection warnings fail. | A predictable fast suite is the feedback loop for all implementation. | “Unit tests” unexpectedly mounting data or taking hours. |
| P09-05 | Test deterministic pure logic and JSON contracts with exact expected values, positive/negative fixtures, schema-format checking, canonical serialization, hashes, and cross-record invariants. | Identity and contract failures must fail before expensive work. | Plausible but incompatible records crossing components. |
| P09-06 | Test image geometry in layers: tiny generated NIfTI/affine fixtures in fast/integration suites, then explicit local-real overlays and round trips. The selected real-data suite fails clearly when requested prerequisites are absent; it does not silently skip. | Synthetic fixtures give exact answers; real files expose library/header/layout behavior. | Either synthetic-only confidence or a default suite dependent on 4 TB storage. |
| P09-07 | Separate software tests from scientific experiments. Tests verify training/inference executes, gradients/weights/lineage behave, outputs are finite/shaped, and controlled fixtures can overfit; model-quality thresholds belong to Plan 06 evaluation artifacts. | A stochastic Dice change is not automatically a software defect. | Brittle tests that fail whenever a legitimate model result changes. |
| P09-08 | Build hand-computed golden metric fixtures for empty, positive, negative, multi-lesion, failed, abstained, and clustered cases. Expected answers are derived independently of production metric code. | Metrics can be internally consistent and still wrong. | Testing an implementation against itself or hiding denominator errors. |
| P09-09 | Use Vitest, React Testing Library, `user-event`, and jsdom for UI reducers, adapters, contracts, and components. Mock NiiVue only at this layer and assert user-visible roles/labels/state. | The UI already uses Vite/React and needs fast behavior tests. | Coupling tests to CSS internals or requiring WebGL for every component check. |
| P09-10 | Use a small Playwright Chromium suite with axe checks for the Plan 08 critical path, plus manual Chrome/Safari NiiVue, keyboard, zoom, and alignment review. Do not run a broad browser matrix initially. | Real browser behavior and accessibility require more than DOM mocks, but the scope is a single-user Mac workstation. | Either no browser evidence or an expensive cross-browser project. |
| P09-11 | Prove transport and producer/consumer parity at every boundary: file and FastAPI case packages, Python/React schema fixtures, training/inference preprocessing, evidence response, review append/reload, and report derivation. | Shared contracts are valuable only when both sides interpret them identically. | Passing isolated components that fail when connected. |
| P09-12 | Add deterministic failure-injection tests for orchestration interruption, retry classification, stale cache, mount/disk loss, writer conflict, partial append, resume, and framework-state loss. | The DAG and artifact layer must be trustworthy when the workstation fails mid-run. | Only testing the happy path and discovering recovery flaws during long jobs. |
| P09-13 | Test retrieval in three separate layers: corpus/query/rights contracts, known-relevance retrieval metrics, and response claim/citation/refusal integrity. No live NCBI result or generative judge is a required fast-test oracle. | Retrieval errors have different causes and live sources change. | A fluent answer hiding corpus/index defects or network drift breaking CI. |
| P09-14 | Commit only generated/synthetic data and non-sensitive golden control records. Local real-data tests use root aliases and content-hashed fixture manifests; raw CTs, labels, article text, checkpoints, notes, and absolute paths stay out of Git and CI. | Testing must honor the same data/license boundaries as production. | A test fixture becoming a privacy, copyright, size, or portability incident. |
| P09-15 | Declare each assertion as exact, deterministic-with-tolerance, seeded/statistical, or manual. Store tolerance/rationale with the test and validate invariants rather than false bitwise reproducibility on MPS. | Scientific computing has multiple legitimate reproducibility levels. | Loose unexplained tolerances or impossible equality requirements. |
| P09-16 | Use risk- and requirement-based coverage as the gate: every locked requirement, high-impact risk, contract branch, and fixed high-impact defect has a named verification. Record line/branch coverage for pure capstone modules as a diagnostic and prevent unexplained decline, but do not use one repository-wide percentage as quality. | Coverage is useful for finding blind spots, not as a scientific score. | High coverage of easy code while leakage, geometry, metrics, or persistence remain untested. |
| P09-17 | Add a minimal GitHub Actions workflow only after the clean local fast suites pass. CI uses Python 3.12 and Node 24 with synthetic/public control fixtures, least permissions, locked installs, and no secrets/medical data; local Mac verification remains authoritative for MPS, real data, NiiVue, and release. | GitHub can verify portability without hosting protected artifacts. | Public CI either leaking data or pretending Linux/CPU proves Apple/MPS behavior. |
| P09-18 | Every formal test run publishes a machine-readable run record, JUnit-style results, explicit pass/fail/skip/xfail counts, durations, environment/code/config identities, and relevant fixture/artifact IDs. Unexpected skips, XPASS, collection errors, or unowned warnings fail a release audit. | “Tests passed” is not reproducible evidence without scope and identity. | Silent skips or green summaries that omit unavailable dependencies. |
| P09-19 | Apply staged gates: fast suites before a material implementation is accepted; relevant integration/real-data tests before artifact publication or expensive runs; full release matrix before G7/G8. A failing required gate blocks advancement unless a time-bounded defect record names owner, impact, and release decision. | Different work needs proportional feedback without weakening the finish line. | Running everything constantly or deferring all integration until Week 9. |
| P09-20 | Every fixed high-impact defect receives a regression test when automation is feasible. Flaky tests are defects: quarantine requires an issue, owner, deterministic reproduction effort, expiry, and exclusion from required pass claims. | Reliability improves only if failures become permanent knowledge. | Repeated rediscovery, indefinite xfails, and rerunning until green. |

P09-01 names the supported baseline rather than modifying either environment now. P09-09/P09-10
approve a minimal UI toolchain design; exact versions and lockfile changes occur only after approval and
Plan 10 environment review.

## Environment model

### Canonical local verification

- macOS/Apple Silicon workstation;
- Python 3.12 clean capstone environment;
- Node 24 LTS for UI tooling;
- pinned/locked dependency resolution under Plan 10;
- MPS fallback behavior recorded when applicable;
- external artifact/data roots declared by alias, not absolute contract fields.

### GitHub fast verification

- Linux hosted runner;
- Python 3.12 and Node 24;
- no credentials, raw/restricted content, external drive, MPS, or heavyweight training;
- synthetic/golden fixtures only;
- dependency caches contain packages only and are never artifact/test evidence.

### Local scientific/release verification

- exact source snapshot/cohort/model/index/case-package IDs;
- required external drives and capacity checks;
- MPS/CPU behavior and tolerance policy;
- real NIfTI geometry/overlay checks;
- real browser NiiVue and local writer checks;
- complete selected release matrix with every skip justified.

## Test taxonomy

| Marker/layer | Purpose | Default fast? | External requirements |
|---|---|:---:|---|
| `unit` | Pure functions/reducers/mappings/math | Yes | None |
| `contract` | JSON Schema, IDs, paths, serialization, cross-record rules | Yes | None |
| `component` | Isolated service/UI component with controlled adapters | Yes | None |
| `integration` | Two or more real components with synthetic/tiny files | Usually | Local temp space |
| `failure_injection` | Retry/resume/partial/stale/conflict behavior | Selected fast cases | Controlled temp roots |
| `browser` | Real UI critical flow | No | Playwright browser/local server |
| `network` | Approved live external-service behavior | No | Network/credentials if required |
| `mps` | Apple accelerator behavior | No | Compatible Mac/MPS |
| `licensed_data` | Pinned local real imaging/literature | No | Declared artifact roots |
| `slow` | Exceeds fast-suite budget | No | Varies |
| `release` | Required final evidence composition | No | All named release prerequisites |
| `manual` | Scientific visual/accessibility/stakeholder checklist | No | Named reviewer/environment |

Markers describe requirements, not importance. A high-impact contract test should be fast; a slow
test is not automatically stronger.

## Initial commands to implement

The exact wrapper filenames may change in Plan 10, but the user-facing contract is:

| Command intent | Required behavior |
|---|---|
| Python fast | Collect and run all tests excluding `slow`, `licensed_data`, `mps`, `network`, `browser`, and `release`; fail on unknown markers |
| Python selected integration | Run named component/contract integration with synthetic/tiny files |
| Python local real | Preflight declared roots, then run selected `licensed_data`/`mps` tests; missing prerequisites fail explicitly |
| UI unit | One non-watch command for Vitest component/reducer/adapter tests |
| UI browser | One non-interactive Playwright Chromium critical-flow command |
| UI build | Reproducible production build after unit tests |
| Full fast | One top-level command runs Python fast, UI unit, and UI build |
| Release verify | One top-level command orchestrates required fast/integration/browser/local-real/manual evidence and writes a release test record |

Human-friendly aliases must call visible underlying commands and preserve exit status. No wrapper may
turn failure into a warning.

## High-risk required tests

### Governance, identity, and data

- Subject with repeated studies cannot cross protected roles.
- Child cohort cannot escape its frozen parent.
- Publisher-test membership is refused by training/development consumers.
- Duplicate IDs/members fail; approximate duplicate candidates cannot auto-merge.
- PANORAMA exclusions, target-aware labels, method provenance, and quarantines are enforced.
- Source root changes do not change identity; content/version changes do.
- Absolute/traversal paths are rejected from portable contracts.

### Imaging and models

- Autonomous inference cannot receive labels/reference/provided ROI.
- Pancreas-only localizer target is invariant to lesion-label changes.
- Shared preprocessing produces equivalent training/inference tensors under declared tolerance.
- Forward/inverse spatial transform preserves world alignment and full source coverage.
- ROI normalization does not crop overflow or distort axes independently.
- Multiple lesions survive raw/default processing.
- Changed model/preprocessing/ROI policy changes prediction identity.
- Previous-project checkpoint hashes are rejected as capstone initialization.
- Resume retains best-run lineage and cannot overwrite another keeper.
- Every requested study receives a terminal result/failure status.

### Metrics and experiments

- Dice conventions, empty cases, completed/end-to-end denominators, sensitivity/specificity, Wilson
  intervals, clustered bootstrap, and paired deltas match independent goldens.
- Multi-lesion one-to-one matching handles splits, merges, extras, misses, and ties deterministically.
- Run class/preregistration cannot change after compute.
- Convenience first-N/path cohorts are refused.
- Publisher-test execution is blocked before candidate/policy freeze.
- Raw and derived prediction sets remain separately identified.

### Retrieval

- Rights/unknown-license states control full-text inclusion and release.
- Query builder rejects prohibited fields and is deterministic.
- Corpus/index rebuild preserves expected identities/counts under the declared policy.
- Recall@k/MRR goldens match hand-ranked examples.
- Claims cite only retrieved passages; missing/mismatched passages invalidate output.
- Empty, weak, conflicting, diagnostic, treatment, and adversarial questions follow refusal policy.

### Workflow and operations

- Scientific artifact validity does not depend on orchestration framework state.
- Interrupted writes never publish complete artifacts.
- Retry classification does not retry scientific/contract failures.
- Repeated/resumed stages reuse only derivation-matching independently valid artifacts.
- External-drive disconnect, full disk, lock conflict, and partial append fail safely.

### Interface and review

- Static/FastAPI packages map to identical scientific values.
- Invalid package/missing measurement never becomes zero or negative.
- Operational review has no reference dependency.
- Reference reveal is enforced in validation/demo mode.
- Evidence failure does not block review.
- Accept/edit/reject reason rules validate on client and writer.
- Saved state appears only after durable receipt and survives reload.
- Revision preserves history; stale review remains on old prediction.
- Late case/evidence/analysis responses cannot alter a new case.
- Critical workflow is keyboard-operable and has no newly detected A/AA violations.

## Independent oracle policy

- Hand-calculate small metric and identity examples; do not call production helpers to generate
  expected outputs.
- Use simple arrays with coordinates documented in the fixture.
- Compare one producer against a schema and independently written expectations, not another adapter
  sharing the same transformation code.
- Store expected errors/codes and failed field paths for negative tests.
- For external published evaluator comparisons, pin evaluator identity and label the compatibility
  claim precisely.
- For model-quality evaluation, use Plan 06 prediction artifacts and uncertainty—not a unit-test
  assertion embedded in training.

## Determinism and tolerance

| Class | Examples | Rule |
|---|---|---|
| Exact | IDs, JSON canonicalization, membership, hashes, labels, reason validation | Byte/value exact |
| Deterministic tolerance | Resampling, affine round trip, CPU probabilities | Fixed absolute/relative tolerance with units/rationale |
| Seeded/statistical | Training smoke, MPS kernels, bootstrap intervals | Seed/environment recorded; test invariant/distribution property, not bitwise weights |
| Manual | CT-mask overlay, NiiVue display, wording, stakeholder task | Signed checklist with exact fixture/build/environment |

Increasing a tolerance to make a failure pass requires a recorded defect/rationale review.

## Coverage and traceability

Every locked requirement and high-impact risk receives:

- stable test/check ID;
- automated/manual classification;
- fixture/oracle identity;
- command/suite;
- expected result;
- implementation status;
- most recent evidence link;
- owner/expiry if temporarily blocked.

Line/branch coverage is collected for new pure Python and UI domain/adapter modules. It is a blind-spot
diagnostic. Gaps in leakage, spatial, metric, retrieval-grounding, review persistence, and release
behavior block gates even if line coverage is high.

## Skip, xfail, warning, and flaky policy

- Ordinary fast selection excludes declared non-fast markers; that is selection, not a skip.
- A selected required test with missing prerequisites fails preflight.
- `skip` requires an issue/reason and is visible in the run record.
- `xfail` must be strict, tied to a known defect, and have an expiry/review date.
- XPASS is a failure until the expectation is reviewed and removed.
- Rerunning only failures to obtain a green release is prohibited; the original run remains evidence.
- Flaky behavior creates a defect. Quarantine cannot count toward a required gate.
- Warnings are either explicitly owned/filtered at the smallest scope or fail the formal run.

## Staged quality gates

### G0-verification / runnable foundation

G0-design permits the scoped setup that produces this evidence. Full G0 requires both checkpoints;
see [`../IMPLEMENTATION-START.md`](../IMPLEMENTATION-START.md). No full production component or model
run becomes ready merely because environment installation is permitted.

- clean environments install from documented inputs;
- all 37 historical tests are collected/classified;
- fast Python and UI unit/build commands run;
- executable contract positive/negative fixtures run;
- test traceability identifies every currently unimplemented high-risk check.

### Before component implementation is accepted

- affected fast tests pass;
- new/changed contract has positive and negative tests;
- fixed defects have regressions;
- no unexplained coverage/traceability loss.

### Before expensive data/model/index work

- relevant contract/data/geometry/preflight/invalidation tests pass;
- artifact roots, capacity, source/cohort/index identity, and failure recovery are verified;
- experiment preregistration exists when applicable.

### Before G7/G8/release candidate

- complete fast, integration, browser, local-real/MPS, end-to-end, accessibility/manual, and claim
  review matrix passes;
- every skip/xfail/warning and unresolved defect has an explicit release decision;
- result evidence is immutable and referenced by the release manifest.

## Implementation sequence

1. Approve or revise P09-01 through P09-20.
2. Freeze the current test/environment inventory and collect baseline commands/errors.
3. Have Plan 10 confirm environment names, lock strategy, artifact roots, and test-result layout.
4. Create the clean Python 3.12 capstone environment and supported Node 24 environment.
5. Add separate dev/test dependency definitions and strict pytest/UI configurations.
6. Collect/run all 37 historical tests unchanged; record every failure and dependency.
7. Classify retained/adapted/superseded/invalid tests before reorganizing directories.
8. Implement committed contract validator and positive/negative golden suite.
9. Build shared synthetic record, tiny NIfTI, metric, corpus/query, case-package, and review fixtures.
10. Add requirement/risk/test traceability and stable check IDs.
11. Fill Plan 02/03 identity, cohort, mapping, provenance, and duplicate-control tests before their code.
12. Fill Plan 04 state/retry/idempotency/failure-injection tests before orchestration code.
13. Fill Plan 05/06 spatial/model/metric/holdout/experiment tests before runs.
14. Fill Plan 07 corpus/retrieval/grounded-response tests before live corpus/index work.
15. Add Vitest/Testing Library coverage for Plan 08 reducers/adapters/components.
16. Add one Playwright+axe critical flow and manual NiiVue/accessibility checklist.
17. Add local-real/MPS preflight and explicit selected-suite commands.
18. Run the complete local fast suite from a clean environment; repair product or tests explicitly.
19. Add minimal GitHub Actions fast verification after the local baseline is green.
20. Add test-run manifest, JUnit, coverage, browser, manual, and release report generation.
21. Execute component gates continuously; never wait for Week 8/9 to discover integration failures.
22. Execute and freeze the release matrix before G8.

No tests or existing behavior are rewritten in steps 4–5 merely to create a green baseline.

## Test-run evidence record

Each formal run records:

- test-run ID, purpose/gate, start/end, terminal status;
- Git commit, dirty/source hash, branch where relevant;
- operating system, hardware, Python/Node/browser/dependency identities;
- exact command, test selection expression, configuration hashes;
- source snapshot/cohort/model/prediction/corpus/index/case-package fixture IDs where used;
- collected, passed, failed, errored, skipped, xfailed, xpassed counts;
- per-test duration and failure location;
- JUnit/result file hashes, coverage scope/summary, browser trace/screenshots where appropriate;
- manual checklist signers and stakeholder evidence references;
- known defects, unavailable prerequisites, and gate decision.

The human-readable report is derived from this record and raw runner outputs.

## Failure modes and fallbacks

| Failure | Trigger | Primary response | Fallback |
|---|---|---|---|
| Scientific dependencies make fast suite slow | Budget exceeded or imports dominate collection | Split pure contract/domain modules from ML integration; lazy test imports | Keep a smaller smoke subset while preserving named integration suite |
| Historical tests fail under clean environment | Baseline red | Classify environment defect, product defect, or stale expectation with evidence | Preserve failure and migrate deliberately; do not weaken assertion silently |
| Node 24 breaks historical Vite/NiiVue build | Clean install/build fails | Run bounded compatibility check and update supported packages under lock review | Use still-supported Node 22 LTS temporarily with recorded expiry |
| UI tooling becomes large | Browser setup dominates Plan 09 | Keep Vitest component layer and one Chromium path | Manual signed browser matrix; G7 still requires real persistence/viewer proof |
| CI cannot install heavy ML stack reliably | Time/space failures | CI only pure contract/domain/UI build suites | Local Mac remains authority; publish local evidence record |
| MPS results vary | Bitwise/probability mismatch | Test shapes/finiteness/lineage/tolerances and record environment | CPU tiny-fixture control plus manual MPS smoke; no false equality claim |
| Real data unavailable | Selected local-real suite preflight fails | Restore/mount exact root/snapshot | Run fast suite only but keep affected gate open |
| Flaky test appears | Inconsistent result under same identity | Open defect, isolate cause, preserve both outcomes | Time-bounded quarantine excluded from required pass claim |
| Golden oracle is questioned | Production and expected disagree | Recalculate by hand/independent implementation and review convention | Mark result blocked; do not choose the convenient answer |
| Release has known failing test | Required gate red | Fix or remove affected release scope with explicit impact review | Release only if requirement is nonessential/deferred and limitation is prominent |

## Plan readiness gate

Plan 09 may move to `Ready` when:

- [x] Quinton approved P09-01 through P09-20 on 2026-09-09.
- [ ] Plan 10 approves the environment/lock/artifact/evidence storage boundary.
- [ ] Python 3.12 and Node 24 compatibility checks pass or the named supported fallback is selected.
- [x] All 37 historical tests have a preserved baseline and classification record (September 19;
  unchanged tests retained, not promoted to capstone acceptance claims).
- [ ] Strict markers, commands, fixture locations, and result schema are frozen.
- [ ] Every Plan 01–08 high-impact requirement/risk has a planned automated/manual check.
- [ ] Protected-data/license rules are encoded in fixture and CI policy.

Design approval (G0-design) precedes bounded environment/fixture setup. G0-verification cannot pass
until clean installation and the required executable evidence exist. Setup must not be blocked by
the absence of evidence that setup itself must produce; unrelated production work remains gated.

## Completion gate

- [ ] Clean environment installation and lock verification pass.
- [x] One documented Python fast command passes (67 checks, September 19; scoped coverage only).
- [ ] One documented UI unit/build command passes.
- [ ] One documented browser critical-flow command passes.
- [ ] Contract positive/negative and cross-language/transport parity suites pass.
- [ ] Required data, geometry, metric, retrieval, orchestration, persistence, and stale/failure
  regressions pass.
- [ ] Selected local-real and MPS suites pass against exact prerequisites.
- [ ] Manual NiiVue, keyboard, zoom, claim, and stakeholder checks are complete.
- [ ] Every skip/xfail/warning/defect has an explicit release disposition.
- [ ] Machine-readable test evidence and derived release report are complete and immutable.
- [ ] Requirements and risks link to current passing evidence.

## Planned artifacts

- [`../testing/README.md`](../testing/README.md)
- [`../testing/CURRENT-TEST-INVENTORY.md`](../testing/CURRENT-TEST-INVENTORY.md)
- [`../testing/ENVIRONMENTS-AND-COMMANDS.md`](../testing/ENVIRONMENTS-AND-COMMANDS.md)
- [`../testing/TEST-TAXONOMY-AND-GATES.md`](../testing/TEST-TAXONOMY-AND-GATES.md)
- [`../testing/FIXTURE-AND-ORACLE-POLICY.md`](../testing/FIXTURE-AND-ORACLE-POLICY.md)
- [`../testing/COVERAGE-AND-TRACEABILITY.md`](../testing/COVERAGE-AND-TRACEABILITY.md)
- [`../testing/CI-AND-REPORTING.md`](../testing/CI-AND-REPORTING.md)
- future development/test dependency and lock inputs;
- future executable contract/golden fixtures and suites;
- future GitHub Actions workflow;
- future machine-readable test runs and release report.

## Technical references

- [pytest documentation](https://docs.pytest.org/en/stable/contents.html)
- [pytest custom marker guidance](https://docs.pytest.org/en/latest/how-to/mark.html)
- [Vitest features](https://vitest.dev/guide/features)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright installation and supported Node versions](https://playwright.dev/docs/intro)
- [Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing)
- [Node.js supported release schedule](https://nodejs.org/en/about/previous-releases)
- [GitHub Actions Python build/test guidance](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)

## Handoff

Plan 10 turns this design into reproducible environments, locks, root preflights, and test-result
storage. Every implementation plan consumes the appropriate staged gate. Plan 12 cannot call a build
a release candidate until the full release matrix and unresolved-defect record are complete.
