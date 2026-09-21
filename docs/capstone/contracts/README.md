# PROWL contracts

These contracts define meaning independently from Python, FastAPI, React, storage services, or an
orchestration framework.

## Governing contracts

- [`identity-and-versioning.md`](identity-and-versioning.md) — stable logical identity, derivation
  keys, content hashes, versions, and invalidation.
- [`artifact-layout.md`](artifact-layout.md) — file-first local artifact layout and publication rules.
- [`run-manifest.schema.json`](run-manifest.schema.json) — workflow execution and stage state.
- [`case-package.schema.json`](case-package.schema.json) — transport-neutral UI package.
- [`review-event.schema.json`](review-event.schema.json) — append-only accept/edit-required/reject
  event.
- [`source-snapshot.schema.json`](source-snapshot.schema.json) — pinned imaging-source version,
  license, root alias, inventory, and assurance.
- [`subject-record.schema.json`](subject-record.schema.json) and
  [`study-record.schema.json`](study-record.schema.json) — protected grouping identity and one-exam
  imaging identity.
- [`annotation-record.schema.json`](annotation-record.schema.json) — structure-specific annotation
  provenance, encoding, validation, and allowed use.
- [`data-issue.schema.json`](data-issue.schema.json) — exclusion/quarantine/adjudication evidence.
- [`manifest.schema.json`](manifest.schema.json) — unified record collections and reconciliation.
- [`cohort.schema.json`](cohort.schema.json) and
  [`cohort-member.schema.json`](cohort-member.schema.json) — parentage, protected role, selection,
  freezing, and canonical membership.
- [`VALIDATION.md`](VALIDATION.md) — schema and documentation verification record.

Synthetic examples are in [`examples/`](examples/). Their repeated placeholder hashes demonstrate
shape only and are not project artifact identities.

## Contract rules

1. JSON schemas use JSON Schema Draft 2020-12.
2. Files conforming to a schema carry `schema_version`.
3. Scientific artifacts carry derivation identity and content integrity separately.
4. Paths inside contracts are relative POSIX-style artifact URIs, never local absolute paths.
5. A schema change that breaks a consumer requires a major schema-version change or adapter.
6. Examples and golden fixtures will be added under `tests/fixtures/contracts/` during Plan 09.

The current synthetic examples validate against their Draft 2020-12 schemas. This confirms the
architecture contract itself; it does not replace the application-level tests required by Plan 09.
