# GitHub CI and test reporting

**Status:** Approved design; workflow creation remains gated  
**Decision:** P09-17 through P09-20  
**Last reviewed:** 2026-09-09

## CI purpose

GitHub Actions verifies that public/synthetic fast logic can install and run outside Quinton's
workstation. It does not certify Apple MPS, external data, NiiVue visual quality, licensed literature,
full inference, stakeholder usability, or the release candidate by itself.

## Initial workflow

Use least-privilege read-only repository permissions and cancellation for superseded branch runs.
After the local clean baseline is green, run two bounded jobs:

### Python fast

- Python 3.12;
- locked fast/test dependency input;
- contract/unit/component and selected synthetic integration/failure tests;
- JUnit and scoped coverage outputs;
- no service secrets or network-dependent tests.

### UI fast

- Node 24 LTS;
- `npm ci` from `ui/package-lock.json`;
- Vitest non-watch run;
- production build;
- optional Chromium critical flow only after runtime/budget is measured.

Do not add an operating-system or language-version matrix initially. The approved runtime identities
are a reproducibility choice, not a compatibility-product promise.

## CI safety

- Never upload or cache raw CT, labels, checkpoints, restricted article text, local notes, secrets,
  external-root manifests containing private paths, or release artifacts.
- Dependency caches are untrusted acceleration only; a cold run must work.
- Artifacts contain test reports/logs that have been screened for identifiers.
- Pull-request workflows receive no sensitive credentials.
- CI cannot access local artifact roots; a test attempting to do so is a defect.
- Workflow/action versions are pinned according to Plan 10's dependency policy.

## Formal test-run artifact layout

Conceptual layout under the governed artifact root:

```text
tests/runs/<test-run-id>/
  test-run.json
  COMPLETE.json | FAILED.json
  python/junit.xml
  python/coverage.xml
  ui/junit.xml
  ui/coverage/
  browser/results.json
  browser/traces/
  manual/checklists/
  logs/
  checksums.sha256
```

CI artifacts are convenience copies. The release manifest references the governed immutable local
test-run artifact and content hashes.

## Test-run status

| Status | Meaning |
|---|---|
| `passed` | All selected required checks passed and no disallowed skip/xfail/warning occurred |
| `failed` | At least one required check failed/errored or evidence could not publish |
| `blocked` | Preflight prerequisite absent for a selected suite; not a pass |
| `cancelled` | Run interrupted; partial evidence preserved, not a result |

The report separately lists excluded marker classes so `fast passed` cannot be read as `release
passed`.

## Release quality report

Derive a readable report containing:

- release/build/test identities;
- suites required and executed;
- pass/fail/error/skip/xfail/xpass totals and durations;
- requirements/risks verified and still open;
- local-real/MPS/browser/manual environments;
- failure-injection and recovery results;
- known defects with severity and disposition;
- evidence links/hashes;
- explicit statement that software testing is not clinical validation.

Quinton approves the release disposition of every unresolved defect. A green CI badge cannot make
that decision automatically.

## References

- [GitHub Actions: building and testing Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [GitHub Actions dependency caching and security](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching)
- [pytest marker guidance](https://docs.pytest.org/en/latest/how-to/mark.html)
- [Vitest coverage guidance](https://vitest.dev/guide/coverage)
- [Playwright best practices](https://playwright.dev/docs/best-practices)
