# Python test foundation — September 19

**Status:** First Python slice verified; full G0-verification remains open  
**Scope:** Non-promotable CPU/synthetic diagnostics, not training or clinical validation

## Completed

- Created new ignored `.venv-prowl` with Python 3.12.13; preserved `.venv312` and legacy requirements.
- Reviewed direct imports and separated `requirements/runtime.in` from `requirements/dev.in`.
- Resolved 58 packages with pip 26.1 and installed the exact macOS-arm64 lock with wheel SHA-256
  verification. `pip check` passed. The independently read installed inventory matches the 58
  resolved packages exactly, plus pip itself.
- Collected all 37 unchanged historical tests before adding any new test/configuration.
- Ran all 37 unchanged tests: **37 passed, zero failed/skipped, 2 warnings, 2.23 seconds**.
- Added strict pytest configuration and 30 offline schema/format checks for existing Plan 01/02
  contracts, including synthetic cohort/review controls. Combined first run:
  **67 passed, zero failed/skipped, 2 warnings, 2.88 seconds**.
- No historical test, production Python source, UI source/lock, trained checkpoint, or raw data was
  modified. No workflow/Prefect code or Plan 04 run-manifest test was added.

## Environment and source identity

| Item | Identity |
|---|---|
| Platform | macOS 27.0, build 26A428, arm64 |
| Python / pip | 3.12.13 / 26.1 |
| Test tools | pytest 9.1.1; pytest-cov 7.1.0; jsonschema 4.26.0 with format dependencies; httpx 0.28.1 |
| Selected scientific imports | PyTorch 2.13.0; MONAI 1.6.0; NumPy 2.5.1; SciPy 1.18.0 |
| Base Git revision | `8c3686284cb86225d3c5695982a6e2da82595c7e` |
| Source state | Dirty; planning files and `src/data/` remain untracked. Local hashes capture the tested files. No clean-revision/formal scientific claim |
| Lock SHA-256 | `525f827150da4bfbc727e317c6646c80bd00f464ac604f9e9d4e128828ffedfb` |

See [dependency inputs and reproduction](../../../requirements/README.md). This lock is for the CPU
test foundation, not proof of a complete training, MPS, retrieval, serving, or Linux environment.
Upgrades/extensions require reviewed direct inputs, a new exact lock, and affected tests.

## Commands and retained evidence

The initial unchanged collection ran before `pytest.ini` existed, with no external pytest plugins:

```sh
env -u PYTHONPATH -u PYTHONHOME PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest --collect-only tests -q
```

It collected all 37 tests in 18.05 seconds, exit 0, with two upstream deprecation warnings.
The unchanged run and first combined run used the same environment flags, `-q`, and unique
`--junitxml` paths. Ordinary fast checks now use:

```sh
env -u PYTHONPATH -u PYTHONHOME PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q
```

`pytest.ini` registers markers, fails unknown markers/configuration, treats unexpected xfail passes
as failures, and excludes slow/real-data/MPS/network/browser/release tests from ordinary fast runs.
Warnings remain visible; none was suppressed to make the suite pass. Both warnings are PyTorch's
`torch.jit.interface` deprecation reached during MONAI imports. They are not numerical failures and
do not justify a dependency upgrade without its own compatibility tests.

Local evidence directory: `outputs/prowl/testing/foundation-2026-09-19/`.

- `resolve-02.json`, `install.json`: resolver and actual install reports.
- `source-before.json`: historical runtime/test/direct-input hashes before the baseline.
- `environment.json`: independent installed inventory, platform, and input/lock hashes.
- `foundation-inputs.json`: new test/config/fixture/schema hashes.
- `historical-baseline.xml` and `.log`: first unchanged run.
- `fast-foundation-01.xml` and `.log`: first combined run; later checks use separate filenames.

The repeat check after completing marker registration also passed all 67 tests (two warnings,
1.80 seconds); its separate record is `fast-foundation-02.xml`.

Setup corrections are preserved here rather than hidden: the initial resolver dry-run failed to
write its report because the new evidence directory did not yet exist; it installed no packages.
Creating that exact directory fixed the second attempt. The first one-line inventory check had a
quoting SyntaxError; its corrected read-only check passed. Neither event required changing package
versions, production behavior, or test assertions.

## Historical test classification

All historical assertions remain intact. No test is deleted, weakened, or silently treated as a
capstone acceptance test.

| Tests | Classification | Interpretation / future work |
|---|---|---|
| All 6 in `test_collapse.py` | Retain historical regression | Preserve label/probability arithmetic; no Level 5 commitment implied |
| All 7 in `test_anatomy_loss.py` | Retain historical regression | Preserve loss/gradient/empty-class mathematics; validate any future capstone recipe separately |
| Seven cohort/write tests in `test_deploy_extras.py` | Retain historical; add capstone adapter tests later | Count, disjointness, duplicate/missing-ID, and overwrite guards remain useful; they do not enforce registered cohort ancestry |
| `test_register_mlflow_args` | Retain historical mocked integration | Confirms function-call arguments only; no real MLflow installation/server/registration was tested |
| All 7 in `test_predict.py` | Retain historical; add autonomous-contract tests later | Existing recipe/JSON/mocked-prediction checks do not establish autonomous spatial correctness |
| All 9 in `test_serve.py` | Retain historical; add case-package/review transport tests later | Existing endpoint/sanitization checks avoid lifespan model loading and do not prove the new shared contract |

## New contract coverage and limits

The 30 checks validate ten existing schemas/examples, two hand-authored controls, eleven invalid
single-field cases, two omitted identities, and five forbidden resource paths. They cover invalid
train roles, missing/duplicate parent IDs, duplicate manifest IDs, frozen member requirements,
hash shape, honest fallback identity assurance, date-time format, review revision references,
review-action vocabulary, required prediction/full-derivation identity, and absolute/parent paths.

These are schema-level guards only. They do **not** establish biological patient uniqueness,
cross-cohort overlap detection, actual content/derivation hash correctness, target-aware source
mapping, disk-path containment, producer/consumer parity, or append-only persistence. Those need
real application implementations and independent tests. A path-pattern test is not a secure
filesystem resolver. Placeholder hashes are not scientific artifact identities.

## Remaining and next

1. Complete the reviewed Git checkpoint of intended documentation/source; do not sweep unrelated
   documents, vendor repositories, binaries, or raw data into Git. No commit or push occurred here.
2. Verify Node 24/npm and a clean unchanged UI build, then the small UI test layer. The existing
   build post-script was read: it writes inside `ui/dist`; it was not executed in this slice.
3. Implement the scoped identity/cohort cross-record checks and remaining core fixtures. No Plan 04
   workflow code until its walkthrough and explicit authorization.
4. In parallel, reconnect/verify `PROWL-Data`, settle the independent backup target/budget, test
   storage/control restoration, and proceed with the [fresh acquisition queue](../operations/DATA-ACQUISITION-QUEUE.md).

No data downloads, training, UI deployment, remote upload, or drive writes occurred. Full G0,
Plan 09 completion, and Plan 10 operational readiness remain open.
