# Manifest assembly checkpoint — September 28, 2026

Status: in-memory manifest assembler implemented; real manifest publication and frozen
cohort packages are not yet implemented. G1 remains open.

Follow-up: [source evidence adapter and real sample](SOURCE-EVIDENCE-2026-09-28.md)
implemented; missing spatial units surfaced in four of six sampled files. Resolve with
explicit evidence before claiming millimetre geometry or freezing real cohorts.

## Code and guarantees

`src/data/manifest_records.py` assembles canonical subjects, studies, annotations and
issues JSONL plus a schema-complete manifest control record. It validates the approved
schemas/formats and cross-record identities, source snapshots, issue references,
annotation links, PanTS publisher partition and unique target statuses. It rejects
unsafe relative paths and non-finite numeric serialization.

Record order is canonical. Derivation includes record content hashes, snapshot records,
configuration and component/code identity; manifest creation time does not determine
scientific identity. Dirty builds require a diff hash. Caller input is not mutated.
Incomplete/discovered or quarantined inputs cannot produce a complete manifest.

This is not an evidence producer or trusted ingestion API. The caller must supply
measured source-file hashes, geometry, version evidence and justified status/provenance.
The assembler does not inspect image bytes, validate annotation semantics or authorize
training. Full issue entity validation, source inventory checks, eligibility rules and
consumer enforcement remain necessary before production publication.

## Why no real frozen cohorts yet

Study and annotation schemas require full file hashes. Reconciled studies require
geometry. The source files have not yet received complete per-file evidence collection;
the publisher-test CT archive remains intentionally unextracted. An extracted archive's
hash is not interchangeable with each study file's hash. Unknown fields must not be
replaced with invented hashes or eligibility claims to satisfy a schema.

Build real evidence and reconciliation first. Then implement cohort package creation,
full parent/ancestor checks, atomic publication, completion markers and registry-only
consumer verification. Until then, the verified legacy membership is a migration input,
not a frozen capstone cohort.

## Tests

Full suite: **290 tests passed**, with two upstream torch deprecation warnings.

Thirteen synthetic cases cover repeatability, input preservation, duplicate identities,
missing subjects/annotations, publisher-test relabeling, incomplete-state handling,
duplicate targets, path safety, dirty-code evidence, timestamp-independent identity and
snapshot evidence changes. Examples are synthetic schema controls, not real measurements.

The existing study example uses PanTS_00009005 with publisher_train; tests explicitly
correct it to publisher_test and verify the runtime mismatch is rejected. Historical
examples were not silently rewritten.

## Next bounded step

Implement the read-only source evidence adapter: approved-root resolution, stable file
hash/size capture, NIfTI header geometry, source metadata joins and unresolved-issue
records. Start with an explicitly selected training-only sample, test against independent
expectations, then plan a full scan. Keep publisher-test inventory structurally separate
and do not use labels or test images for model selection. No source aliases or scientific
run flags should be enabled by this work.
