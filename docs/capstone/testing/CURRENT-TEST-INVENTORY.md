# Current test and environment inventory

**Status:** Clean Python baseline and first contract slice verified; UI/full G0 pending  
**Observed:** 2026-09-09  
**Last reviewed:** 2026-09-19

## September 19 update

New `.venv-prowl` uses Python 3.12.13 and the exact 58-package hashed macOS-arm64 lock. All 37
historical tests were collected and passed unchanged. Thirty new contract checks plus strict pytest
configuration bring the fast suite to **67 passing tests**, zero failures/skips and two visible
upstream deprecation warnings. See [the foundation record](FOUNDATION-2026-09-19.md) for evidence,
test classification, commands, and remaining gaps. No UI, MPS, real-data, or full G0 claim is made.

The inventory and September 18 diagnostic results below are retained as the pre-foundation baseline;
claims of missing tools/configuration below refer to that historical state, not `.venv-prowl` today.

## Python tests

| File | Test functions | Historical focus | Initial classification task |
|---|---:|---|---|
| `tests/test_anatomy_loss.py` | 7 | Collapsed probabilities/Dice, gradient flow, auxiliary loss behavior | Retain scientific math intent; verify capstone label semantics |
| `tests/test_collapse.py` | 6 | Level-5-to-pancreas/lesion collapse and passthrough | Historical/optional Level 5; retain only reusable label invariants |
| `tests/test_deploy_extras.py` | 8 | Cohort counts/disjointness/overwrite and MLflow argument registration | Adapt to registered protected-cohort IDs; reject legacy list semantics |
| `tests/test_predict.py` | 7 | Recipe compatibility, metadata, JSON-safe result, unknown case | Adapt to capstone model/prediction/case-package contracts |
| `tests/test_serve.py` | 9 | FastAPI failures, catalog/result shape, path sanitization | Adapt endpoint expectations to transport-neutral contracts |
| **Total** | **37** |  |  |

No file is moved or edited before the first clean-environment collection/run is preserved.

The September 18 source inventory corrects the earlier per-file prediction/serving counts (6/10 to
7/9); the total remains 37. These are `def test_*` source counts, not pytest discovery evidence.

### September 18 bounded diagnostic checks

Both commands below ran unchanged existing CPU-only unit tests in historical `.venv312`
(Python 3.12.13), with bytecode writes disabled:

```text
PYTHONDONTWRITEBYTECODE=1 .venv312/bin/python tests/test_collapse.py
PYTHONDONTWRITEBYTECODE=1 .venv312/bin/python tests/test_anatomy_loss.py
```

- Collapse: all 6 tests passed; exit code 0.
- Anatomy loss: all 7 tests passed; exit code 0.
- No other historical tests were executed in this check. No model training, external data, MPS
  workload, dependency installation, or test-file modification occurred.
- This is a limited diagnostic, not the clean-environment baseline, complete pytest collection,
  capstone label-semantic approval, or G0-verification. No historical Level 5 recipe was adopted.
- Python 3.12.13, missing pytest/jsonschema, and Node 20.20.1 were rechecked. `.venv-prowl` does not
  yet exist, and UI `test:run`/browser scripts are not yet present.

## Python environment

| Item | Observed state | Consequence |
|---|---|---|
| System Python | 3.14.6 | Not the capstone baseline; known package compatibility risk |
| `.venv312` | Python 3.12.13 | Historical working scientific environment; contents are not a clean lock |
| `pytest` in `.venv312` | Absent | Existing tests are not currently runnable through their documented runner |
| `jsonschema` in `.venv312` | Absent | Contract validation is not committed/runnable in the project environment |
| `requirements.txt` | Broad minimum versions | Useful intent list, insufficient exact environment identity |
| Test configuration | None found | No strict markers, warnings, paths, timeouts, or result defaults |

`docs/capstone/contracts/VALIDATION.md` records a valid one-time isolated schema check. It explicitly
does not prove producer/consumer conformance and is not a substitute for the executable suite.

## UI environment

| Item | Observed state | Consequence |
|---|---|---|
| Node | 20.20.1 | EOL at the planning date; replace with supported LTS for capstone verification |
| npm | 10.8.2 | Record through the Node/toolchain lock |
| React | 18.3.1 installed | Existing application baseline |
| NiiVue | 0.69.0 installed | Existing viewer baseline |
| Vite | 5.4.21 installed | Existing build baseline |
| `package-lock.json` | Present | Reproducible npm input after supported-Node compatibility check |
| UI unit/component tests | None | Reducer/adapter/workflow changes currently lack automated checks |
| Browser tests | None | No real-browser critical-flow evidence |
| Accessibility automation | None | Plan 08 manual/automated boundary is not executable |

## Repository quality infrastructure

- No GitHub Actions workflow found.
- No test-result artifact convention found.
- No requirement/risk-to-test matrix exists yet.
- No registered marker or slow/real-data separation exists.
- No explicit flaky/skip/xfail policy exists.
- Existing tests import production modules directly and may require dependencies during collection.
- Several capstone schemas/examples exist, but their validation is not a committed test suite.

## Baseline run record to capture

After approval and environment setup, preserve:

1. exact environment and dependency identities;
2. `pytest --collect-only` result;
3. first unchanged run including every failure/error/warning/skip;
4. UI clean install and build result on supported Node;
5. old UI build result or incompatibility evidence;
6. classification of each historical test;
7. migration map to capstone test IDs.

The purpose is to know what changed, not to force the historical baseline green.
