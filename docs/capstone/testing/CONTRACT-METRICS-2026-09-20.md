# Contract and metric foundation — September 20, 2026

**Status:** Priority 4 bounded synthetic-test slice complete; not full G0 or Plan 06 qualification.
**Owner:** Quinton Evans. **Scope:** Plans 01/06/09 foundation, while away from the data drive.

## Outcome

Added 25 contract cases and 17 metric cases. Targeted run: **72 passed** (including the existing
30 contract cases). Full Python fast suite: **147 passed**, no failures/skips/xfails, two existing
upstream `torch.jit.interface` deprecation warnings. No production code, schemas, dependencies,
historical experiment entries, or data artifacts were changed. No training/evaluation run on scans
occurred; these are software checks, not model experiments.

## Checks and independent oracles

| Check family | Executable evidence | Oracle / planted error |
|---|---|---|
| T-DATA-FOUNDATION-NESTED | `test_case_package_rejects_malformed_nested_value` | Existing schemas reject invalid versions, enums, hashes, confidence, boxes, sizes, dimensions, spacing, counts, volumes, scores, provenance, and commit IDs |
| T-UI-FOUNDATION-PREDICTION | Completed-mask and failed-output controls | Successful statuses need both masks; a failed prediction may explicitly omit outputs and measurements |
| T-UI-FOUNDATION-REVIEW | Correction, reason-code and extra-field controls | Both transports accept the same correction shape; revision 2 needs predecessor identity; no browser mask-edit requirement; empty/duplicate/unknown reasons rejected |
| T-MET-FOUNDATION-DICE | `test_metric_goldens.py` Dice controls | Hand counts: perfect 1, disjoint 0, partial 1/2, missed voxel 2/3, extra voxel 4/5, empty positive 0; empty references NaN |
| T-MET-FOUNDATION-TARGET | Parenchyma/region swap | Swapping class 1 and lesion yields parenchyma 1/2, full region 1, lesion 0; these targets must not share an ambiguous name |
| T-MET-FOUNDATION-AUC | AUC goldens and paired permutation | Four positive/negative pairs with two wins, one tie, one loss give 2.5/4 = 0.625; perfect/reversed/all-tied and missing-class cases also checked |
| T-MET-FOUNDATION-THRESHOLD | Boundary/fallback control | Equality included; background/pancreas tie selects pancreas; raising threshold changes only the expected labels; inputs remain unchanged |

These IDs describe this foundation slice, not the complete owning requirement. Tests are deterministic,
CPU-only, hand-authored, and require no scans. Their status is passing at this checkpoint. The metric
tests call the existing pure functions in `scripts/evaluate.py`; they never invoke its `main()`.
The import requires the locked scientific environment but does not load datasets or checkpoints.
They do **not** qualify `src/training/metrics.py` or the historical evaluation CLI for capstone use.

## Mutation challenge

Four temporary in-memory replacements were each rejected by the actual test assertions:

1. Dice formula missing its factor of two.
2. Empty reference incorrectly awarded perfect Dice.
3. AUC tied scores incorrectly awarded full credit.
4. Threshold comparison changed from inclusive to exclusive.

Each replacement was restored in a `finally` block; no production source was edited. This is a
bounded assertion challenge, not a repository-wide mutation score. The malformed contract controls
likewise begin from a validated positive example before corrupting the target field.

## Reproduce and evidence

From the canonical PROWL checkout using its locked `.venv-prowl` Python 3.12 environment:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv-prowl/bin/python -m pytest tests/test_contracts.py tests/test_metric_goldens.py -q -p no:cacheprovider
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

Local ignored evidence: `outputs/prowl/testing/contracts-metrics-2026-09-20/`:
`targeted-first.txt`, `full-suite.txt`, `mutation-controls.txt`. The workspace check passed before
writes; `git diff --check` passed after the tests. Existing unrelated modifications are preserved;
no commit, push, or cleanup was performed.

## Still open — do not infer these from green tests

- Schema checks establish record shape, not runtime producer/consumer validation, actual content
  hashes, safe path resolution, source-space alignment, or cross-record consistency.
- Review predecessor existence, matching prediction/case identity, sequential revisions, and
  append-only persistence still require a real validator/writer and integration tests.
- Cohort subject leakage, parent membership, immutable references, and eligible-reference joins
  still require cross-record validation.
- The full capstone evaluator still needs explicit eligibility/denominators, failed/abstained case
  accounting, confusion matrices, Wilson intervals, clustered/paired bootstrap, component matching,
  geometry, subgroup reporting, and validation of malformed numerical inputs. These legacy helper
  tests are not permission to reuse the historical evaluation workflow wholesale.
- No new metric version or operating point was selected, and no held-out data was accessed.

Next in the agreed away-from-drive sequence: **Plan 04 plain-language walkthrough**. Explain its
function to Quinton before any orchestration code or tool spike; obtain explicit authorization.
