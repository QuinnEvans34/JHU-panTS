# Contract validation record

**Validated:** 2026-09-08  
**Scope:** Architecture and Plan 02 contract set version 1.0.0

## Checks completed

- Every JSON schema and example parses as valid JSON.
- Each schema passes JSON Schema Draft 2020-12 schema validation.
- The run-manifest example validates against `run-manifest.schema.json`.
- The case-package example validates against `case-package.schema.json`.
- The review-event example validates against `review-event.schema.json`.
- The source-snapshot, subject, study, annotation, data-issue, manifest, cohort, and cohort-member
  examples validate against their respective Draft 2020-12 schemas.
- Contract path guards reject Unix absolute paths, Windows drive-letter paths, `file:` URIs, leading
  parent traversal, and nested parent traversal.
- The case-package schema rejects a package that supplies only the shortened ID and omits the full
  derivation hash.
- Plan 02 negative checks reject a fallback subject presented as directly verified, an absolute
  source path, an unknown target status paired with positive evidence, a positive/negative target
  paired with unavailable evidence, a training cohort carrying a validation role, a frozen cohort
  without members, a non-source cohort without a parent, and a complete manifest with unresolved
  blocking issues.
- The target-aware Plan 03 example validates `pdac=negative` and
  `pancreatic_lesion=unknown` on one study without coercing the latter to negative.
- Every local Markdown link under `docs/capstone/` resolves.
- Code fences in the architecture and contract Markdown files are balanced.

## Validator

Validation used Python `jsonschema` with `Draft202012Validator` and format checking in an isolated
temporary environment. No project dependency or runtime environment was changed.

## Not yet claimed

This record validates the designed contracts and examples. It does not yet prove that Python,
FastAPI, or React producers/consumers conform to them. Plan 09 will add committed golden fixtures,
positive and negative schema tests, transport parity tests, and application round trips.

## September 19 executable foundation

Thirty schema/format checks now run in `.venv-prowl` via `tests/test_contracts.py`, alongside the
37 unchanged historical tests. See [the foundation record](../testing/FOUNDATION-2026-09-19.md).
This adds repeatable checks for ten existing contracts and hand-authored cohort/review fixtures;
it does not establish runtime producer/consumer, cross-record, or transport conformance. No schema
was changed. Plan 04 run-manifest code/tests remain outside this slice pending its coding authorization.
