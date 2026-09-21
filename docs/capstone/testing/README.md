# Plan 09 testing and quality package

**Status:** Approved design; first Python foundation verified, full verification pending  
**Owner:** Quinton Evans  
**Last reviewed:** 2026-09-19

## Purpose

This package defines how PROWL proves software correctness and preserves that evidence. It keeps
fast development feedback separate from real-data, MPS, browser, scientific-evaluation, stakeholder,
and release checks without allowing any required layer to disappear through silent skipping.

## Package map

| Document | Question answered |
|---|---|
| [`CURRENT-TEST-INVENTORY.md`](CURRENT-TEST-INVENTORY.md) | What tests and environment capabilities exist now? |
| [`FOUNDATION-2026-09-19.md`](FOUNDATION-2026-09-19.md) | What passed in the first clean Python foundation, and what remains unverified? |
| [`ENVIRONMENTS-AND-COMMANDS.md`](ENVIRONMENTS-AND-COMMANDS.md) | Which environments and commands will be reproducible? |
| [`TEST-TAXONOMY-AND-GATES.md`](TEST-TAXONOMY-AND-GATES.md) | Which suites run at each point in the project? |
| [`FIXTURE-AND-ORACLE-POLICY.md`](FIXTURE-AND-ORACLE-POLICY.md) | What data and independent expected answers may tests use? |
| [`COVERAGE-AND-TRACEABILITY.md`](COVERAGE-AND-TRACEABILITY.md) | How do requirements, risks, defects, and tests remain connected? |
| [`CI-AND-REPORTING.md`](CI-AND-REPORTING.md) | What runs on GitHub versus locally, and what evidence is retained? |

The governing plan is [`../implementation/09-testing-and-quality.md`](../implementation/09-testing-and-quality.md).

## Non-negotiable rules

1. A green result identifies the exact suite, environment, fixtures, and skips.
2. Fast tests require no network, external drive, licensed data, MPS, or downloaded browser.
3. A selected real-data/release test fails when a prerequisite is absent; it does not silently skip.
4. Expected values do not come from the production function under test.
5. Software tests and scientific model evaluation remain separate.
6. Raw/restricted data and secrets never enter GitHub Actions.
7. MPS, local-real NIfTI, NiiVue, persistence, and full release checks remain local responsibilities.
8. Every fixed high-impact defect becomes a regression where feasible.
9. Flaky/xfail/skip states are visible, owned, expiring, and excluded from required pass claims.
10. High-risk requirement coverage outranks a single line-coverage percentage.

## Approval boundary

Plans 09 and 10 are approved. G0-design permits bounded foundation setup under D-255; the first
Python slice has evidence, but full G0-verification still requires the remaining checks. UI, CI,
real-data/MPS, producer/consumer conformance, and release evidence are not implied by these tests.
