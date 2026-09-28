# Extraction tooling design — September 22, 2026

**Status:** Design approved by Quinton 2026-09-22; implementation in progress.
**Scope:** A standalone, safe archive extractor for the pinned PanTS and PANORAMA snapshots.
**Not in scope:** Plan 04 orchestration, source activation, cohort reconciliation, training,
archive deletion, cross-archive merging, or any scientific claim.

This document records what the extractor does, which threats it controls, the decisions taken and
the alternatives rejected. It is the review surface for that implementation. Extraction is a
deterministic data operation, not an experiment: it produces an operational receipt here, never an
entry in `docs/experiments.md`.

## Objective

Convert verified archives into extracted, per-archive-isolated directory trees on `PROWL-Data`,
with evidence sufficient to prove each extraction is complete and faithful. Completion of this work
establishes *extracted-but-unreconciled* state. It does not establish source readiness, case
identity, semantic compatibility, or permission to train.

## Inputs already established

| Evidence | Location | What it pins |
|---|---|---|
| Publisher inventory | `docs/capstone/data/acquisition-2026-09-19.json` | Archive names, compressed bytes, publisher SHA-256 where supplied |
| PanTS structural scan | `outputs/prowl/storage-prep-2026-09-21/pants-scan-active-20260921T2040.jsonl` | Per-archive file count, directory count, expanded bytes, local SHA-256, zero member issues |
| PANORAMA ZIP preflight | `outputs/prowl/storage-prep-2026-09-21/panorama-zip-preflight.json` | Per-archive file count, directory count, declared expanded bytes |
| Capacity and destinations | `EXTRACTION-BUDGET-2026-09-22.md` | Reserves, floors, isolated destination naming |
| Storage registry | `configs/local/roots.yaml` (ignored) | Mount path, volume UUID, failure domains |

The September 21 scan is the single most valuable input: it gives an **independent expected value**
for every PanTS archive. The extractor asserts against it rather than trusting a clean process exit.

## Decision: per-archive atomic promotion

Each archive extracts into a uniquely named partial directory. Only after every verification passes
is that directory renamed to its final name.

```
<destination-root>/<archive-stem>.partial-<UTC timestamp>/   # during extraction
<destination-root>/<archive-stem>/                           # after verification only
```

`os.rename` within one filesystem is atomic, so the final name appears in one step or not at all.

**The completeness invariant is structural, not asserted.** The presence of the final directory is
itself proof that extraction finished and verified. No consumer has to read a status flag, parse a
log, or understand a recovery protocol to know whether a tree is trustworthy. A partially extracted
tree cannot occupy the name a downstream reader looks for.

### Alternatives considered and rejected

**Per-member write journal with `--resume`.** Record each member after it is written and fsync'd;
on resume, re-stat journaled entries and skip matches. Rejected for four reasons.

1. *Sync ordering cost.* Correctness requires fsync on the file, the journal, and the journal's
   directory — roughly three syncs per member, or ~860,000 for `PanTSMini_Label.tar.gz` alone. That
   overhead can plausibly exceed the cost of simply redoing an interrupted archive.
2. *Weak resume check.* Matching size does not prove matching content; a torn write can produce the
   correct length with corrupt bytes. An honest resume re-hashes, which re-reads most of what it
   saved.
3. *It reintroduces the bug class atomicity removes.* A directory that looks complete but is not,
   plus a sidecar naming the trustworthy subset, means every downstream reader must understand the
   sidecar. Missing that produces a manifest over partial data and plausible-looking numbers from an
   incomplete dataset — the same silent-wrongness shape as the 2026-07-19 validation-leakage defect.
4. *Worst-exercised path at the worst time.* Resume logic runs after a failure, typically unattended
   and out of hours, and is the least tested code in the tool.

**Directory-level checkpointing.** Promote each case directory independently, preserving the
existence-proves-completeness invariant at finer grain. Viable and attractive, but it depends on
members arriving grouped by directory, which the scan deliberately did not record. Deferred; the
pilot can settle member ordering cheaply if a future measurement justifies revisiting this.

### Cost accepted

An interruption discards that archive's progress. Blast radius is bounded by the **largest single
archive**, never the whole job, because completed archives keep their promoted names. The projected
worst case is `PanTSMini_Label.tar.gz`: 287,128 files, 19,802 directories, 52,020,675,883 bytes.

Actual runtime on this drive is unmeasured. The pilot measures it. See the run document for the
pre-registered rule that decides whether finer-grained recovery is ever added.

## Threat model and controls

| Threat | Control |
|---|---|
| Path traversal, absolute paths, drive letters, backslash separators, control characters | Shared member predicate rejects before any write; extraction aborts |
| Symlink, hardlink, device, FIFO, socket members | Rejected as link-or-special; never materialized |
| ZIP symlinks encoded in `external_attr` | Unix mode checked explicitly; `zipfile` cannot report these through `is_dir()` alone |
| Sparse or negative-size members | Rejected |
| Duplicate paths, case-only and Unicode-normalization collisions | NFD-casefold key set; collision aborts |
| A file member shadowing a directory in another member's path | Parent-chain check |
| Overwriting existing data | Files opened `O_EXCL`; the kernel enforces it, not a check-then-write test |
| Overwriting a previous extraction | Final destination must not exist; a pre-existing partial is preserved, never reused or deleted |
| Escaping the destination after path construction | Resolved target asserted to remain inside the partial root |
| Decompression bomb | Per-member write aborts if bytes exceed the declared size; archive-level member and byte ceilings |
| Corrupt or truncated archive | tar: compressed stream hashed during extraction and compared to the pinned digest before promotion. ZIP: per-member CRC-32 validated on read |
| Data appended after the tar end | Total decompressed bytes compared against the offset where the last member actually ends (see finding below) |
| Archive mutated during extraction | `stat` identity compared before and after |
| Wrong or vanished volume | `mounted()` re-verified on every progress tick, as the scan does |
| Filling the drive | Free space re-checked on every progress tick against the 512 GiB floor |
| Silent partial extraction | Counts, directory counts and total bytes asserted against pinned evidence before promotion |
| Member paths leaking into logs or Git | Only aggregates are emitted, matching existing tooling |

## Finding: the existing trailing-data check is inert

`scan_pants_archives.py` ends with a drain loop that reads the gzip stream after the tar closes and
rejects any leftover bytes. **That check cannot fire.** `gzip.GzipFile` concatenates gzip members
transparently, and `tarfile`'s stream mode consumes its source to EOF, so by the time the loop runs
there is nothing left to read. Verified: a `.tar.gz` with a second gzip member appended passes
`scan()` with no error and correct-looking counts.

The same code was written into the first draft of the extractor and its test caught it.

*Risk in context: low.* Ten of eleven PanTS archives matched a publisher SHA-256, which proves
byte-exactness and rules out appended data outright. `PanTSMini_Label.tar.gz` has no publisher
digest, so its local digest pins it against change since the September 21 scan but could not have
detected data appended before it.

*Fix in the extractor:* total decompressed bytes are counted and compared against
`last_member.offset_data + padded size + 1024`, rounded up to tar's 10,240-byte blocking factor.
Using tar's own stream offsets rather than reconstructed header arithmetic makes this exact for
ustar, GNU and PAX archives alike, so a legitimate 35 GB extraction cannot be rejected by a header
format the check failed to anticipate. Verified against all three formats, with and without long
names, detecting an append as small as 8 bytes.

*`scan_pants_archives.py` is deliberately left unchanged* — its output is cited evidence. The
inert check there is recorded here and in `tests/test_extraction.py` rather than silently patched.
A future session may fix it, which would require re-running the scan and re-citing its evidence.

## Finding: path-length validation ran after the filesystem walk

`target_for()` built a member's destination, walked the parent chain for symlinks, and only then
checked the constructed path length. On macOS `PATH_MAX` is 1024, so `lstat()` on an over-long
path raised a bare `OSError(ENAMETOOLONG)` from inside `pathlib` before the explicit check could
fire. Linux's 4096-byte limit meant the same code passed in the container.

Behaviour was still fail-closed — an over-long path was always refused — but with an opaque errno
instead of a message naming the cause, after pointless syscalls on a path already known to be
invalid.

*Fixed:* the length check now precedes `under()`. `under()` additionally converts any unexpected
`OSError` while probing the chain into an explicable refusal rather than surfacing a raw errno.

*Regression test:* `test_path_length_is_checked_before_the_symlink_walk` patches `under()` to fail
if it is reached, asserting the ordering directly rather than relying on a platform limit. Verified
to fail against the old ordering and pass against the new one.

This is the argument for running the suite on the target platform. Both CPython 3.11 and 3.12 in a
Linux container passed the original code; the first macOS run did not. Real member paths are
roughly 160 bytes, so this defect was never going to fire on the pinned archives — but the same
class of platform divergence is exactly what the extraction tooling exists to catch.

## One definition of an unsafe member

`scripts/acquisition/member_safety.py` holds the predicate. `extract_sources.py` imports it.

`scan_pants_archives.py` is deliberately **not** refactored to use it: its output is already cited
as evidence in the budget document, and changing the code that produced that evidence would
invalidate it. Instead a test asserts the **superset property** — every issue the existing scan
raises on an adversarial corpus is also raised by the shared module. The new module may be stricter
(it adds component-length limits, which matter only when writing). It may never be more permissive.

## Verification before promotion

All must pass, in order:

1. Every member classified safe.
2. Every file's written byte count equals its declared size.
3. tar: the compressed stream is fully consumed and its SHA-256 matches the pinned scan digest.
4. Extracted file count, directory count, and total bytes equal the pinned expectations.
5. Target tree confirmed within the partial root.

Any failure leaves the partial in place for inspection and aborts. Partials are never deleted
automatically; deletion of evidence is not authorized.

## Residual risk, stated honestly

`rename` is atomic for metadata, but file data may still be in the page cache at promotion time.
A process kill is safe — the kernel still flushes. A **power loss or kernel panic in the window
between promotion and flush** could leave a promoted directory whose contents are incomplete.

Mitigations: `os.sync()` is issued before promotion, and `--verify` re-checks any promoted
directory against the pinned expectations without re-reading file contents. This is a narrow window
on a machine that stays powered, not an eliminated risk, and it is recorded rather than hidden.

## Test matrix

| Area | Marker | Cases |
|---|---|---|
| Member safety | `unit` | Traversal, absolute, drive letter, backslash, control character, empty name, over-long component, duplicate, case collision, Unicode NFD collision, file-as-parent, symlink, hardlink, FIFO, device, sparse, negative size |
| Scan agreement | `unit` | Superset property across the adversarial corpus |
| ZIP specifics | `unit` | `external_attr` symlink detection, directory entries, zero-length files |
| Extraction success | `component` | tar and ZIP round-trip, byte-exact content, counts matching the oracle, promotion occurs |
| No overwrite | `component` | Existing destination refused; existing partial preserved and not reused |
| Integrity | `component` | Truncated archive, wrong pinned digest, member exceeding declared size, trailing data after tar end |
| Oracle mismatch | `component` | Count or byte mismatch refuses promotion and leaves the partial |
| Interruption | `failure_injection` | Abort mid-stream leaves only the partial; the final name never appears |
| Capacity and mount | `failure_injection` | Simulated free-space breach and volume change abort cleanly |
| Verify mode | `component` | Detects a promoted tree that no longer matches expectations |

## Files added

```
docs/capstone/operations/EXTRACTION-DESIGN-2026-09-22.md   this document
docs/capstone/operations/EXTRACTION-RUN-2026-09-22.md      operating procedure and evidence
scripts/acquisition/member_safety.py                       shared member predicate
scripts/acquisition/extract_sources.py                     extractor CLI
tests/test_member_safety.py                                predicate and agreement tests
tests/test_extraction.py                                   extraction behaviour tests
```

No existing file is modified. No raw data, member inventory, or local configuration enters Git.

## What this does not establish

Extraction completion is not source readiness. After every archive is extracted and verified, these
remain open and are owned by their plans: case identity and cross-source collision analysis
(Plan 02), PANORAMA label mapping, exclusions and duplicate controls (Plan 03, G2), geometry and
target validation (Plan 05), and registered cohort membership (G1). Source aliases stay `null` and
`scientific_runs_enabled` stays `false` until those pass.
