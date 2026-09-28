# Codex handoff — adversarial review request

**From:** Claude (Cowork session, 2026-09-22 → 2026-09-28)
**To:** Codex
**Purpose:** Review the extraction and inventory tooling and the conclusions drawn from it.
**Authorized by:** Quinton, 2026-09-28.

This is a review request, not a status report. Sections 1–2 give the context you need; section 3
is the actual ask. Please attack the claims rather than confirm them.

`AGENTS.md` has deliberately **not** been updated with this work yet. Quinton wants your review
first, so the shared context file does not absorb conclusions you have not checked.

## 1. What happened while you were out

Between September 22 and 28, acting on your controlled-extraction handoff:

- **Extraction tooling built and tested**, then run. **15 of 16 archives extracted**: 300,608
  files, 565,327,340,747 bytes, 4.68 hours wall clock. Every PanTS archive matched its pinned
  SHA-256; every PANORAMA member passed CRC-32 and its declared size. `PanTSMini_ImageTe` is
  deliberately unextracted.
- **Inventory tooling built and run** against every extracted tree.
- **`docs/capstone/data/OBSERVED-LAYOUT-2026-09-28.md` written** as the reviewed record of what
  the data actually looks like. It changes what Plans 02, 03 and 05 can assume.
- **Four defects found in my own tooling**, all by running against real data rather than by
  tests. One further defect found in yours (section 4).

Source aliases remain `null`, `scientific_runs_enabled` remains `false`, no Plan 04 code exists,
and nothing has been committed. The work is untracked in the working tree.

## 2. What was added

| File | Purpose |
|---|---|
| `docs/capstone/operations/EXTRACTION-DESIGN-2026-09-22.md` | Safety model, atomicity decision record, rejected alternatives, threat table, residual risk |
| `docs/capstone/operations/EXTRACTION-RUN-2026-09-22.md` | Operating procedure, evidence locations, recovery semantics |
| `scripts/acquisition/member_safety.py` | Shared unsafe-member predicate |
| `scripts/acquisition/extract_sources.py` | Extractor CLI |
| `scripts/diagnostics/inventory_sources.py` | Structural inventory |
| `tests/test_member_safety.py`, `tests/test_extraction.py`, `tests/test_inventory.py` | ~140 tests |
| `docs/capstone/data/OBSERVED-LAYOUT-2026-09-28.md` | The reviewed record |

Ten governance documents were also corrected where they still said the Plan 04 walkthrough was
pending; it was accepted 2026-09-20 under D-045. Coding authorization remains required and no
wording was weakened. Dated records were left unedited.

## 3. Review targets, highest risk first

### 3.1 The extractor writes to the only copy of 600 GB

`scripts/acquisition/extract_sources.py`. Claims to attack:

- **No-overwrite is kernel-enforced.** Members are written with `open(path, 'xb')`. Is `O_EXCL`
  sufficient here, and is there any path where a member is written without it?
- **Partial-then-rename atomicity.** Extraction goes to `<stem>.partial-<ts>/`, verifies, then
  `os.rename`. The claimed invariant is that the final name existing *is* proof of a verified
  extraction. Find a sequence where the final name appears without full verification.
- **The `os.sync()` before rename.** The design document admits a residual window: power loss
  between rename and flush could promote an incomplete tree. Is `os.sync()` the right call, is the
  window characterised correctly, and is `--verify` an adequate mitigation?
- **Resource ceilings.** `MAX_EXPANDED` 4 TiB, member cap 2,000,000, `MAX_PATH_BYTES` 1000. Are
  these defensible, and can any be evaded by a crafted archive?

### 3.2 The oracle may inherit defects from the scan

The extractor verifies extracted counts and bytes against the September 21 scan output from your
`scan_pants_archives.py`. **This is circular if that scan has defects** — and it has at least one
(section 4). The publisher SHA-256 match is independent and strong for 10 archives; the Label
archive has no publisher digest, so its verification rests entirely on your scan's local digest
plus my count check.

Ask: what else could the scan have gotten wrong, and what would that make the extractor miss?

### 3.3 The member-safety superset claim

`tests/test_member_safety.py::test_shared_module_is_a_superset_of_the_existing_scan` asserts that
every issue `scan_pants_archives.inspect_member` raises is also raised by the new shared module.
**It asserts this over an adversarial corpus I chose.** If the corpus is inadequate the property
is vacuous. Please attack the corpus, not the assertion.

### 3.4 The trailing-data rewrite

Your scan's "Unexpected data after tar end" check cannot fire (section 4). I replaced it with
total-decompressed-bytes compared against `last_member.offset_data + padded size + 1024`, rounded
to tar's 10,240-byte blocking factor. Verified against ustar, GNU and PAX, with and without long
names, detecting an 8-byte append.

The failure mode that would hurt: a **false positive** rejecting a legitimate 35 GB extraction
after the work is done. Is there a real archive shape where decompressed bytes legitimately exceed
that bound?

### 3.5 The conclusion Plan 02 will act on

`OBSERVED-LAYOUT-2026-09-28.md` states: *"On this evidence Plan 02 needs no exclusion rule for the
structures PROWL segments."*

That rests on a chain worth breaking:

1. 101 cases are small in one or two structures while otherwise normal.
2. Of **50 sampled**, the affected structures are liver (20), lung_left (14), colon (12), and four
   singletons. None is pancreatic.
3. I interpret that as field-of-view truncation of peripheral organs.
4. Therefore pancreatic structures are unaffected.

Step 2 samples half. Step 3 is my inference, not a measurement. If those are genuine label
defects rather than cropping, the conclusion inverts. **File sizes cannot settle it** — that needs
voxels, which is Plan 05.

### 3.6 The PANORAMA channel-suffix rule

Claim: strip one trailing `_NNNN` component from PANORAMA CT filenames to join to labels. Verified
at 2,238 matched, 0 unmatched either way. All 2,238 CT files end `_0000`.

Is stripping the *last* underscore component right in general, or does it only work because this
snapshot happens to be single-channel? What happens on a future multi-channel release?

### 3.7 My fixtures were too clean, repeatedly

Four defects reached real data because my synthetic fixtures were unrealistic:

| Defect | Why tests missed it |
|---|---|
| Trailing-data drain outside the gzip context | Caught by tests, but only after I wrote it |
| Path-length check ordered after `lstat` | Linux `PATH_MAX` 4096 hid what macOS 1024 exposed |
| Case-level size threshold blind to one bad file among 29 | Fixture used toy byte sizes |
| Single-structure sources counted in both populations | Fixture had four structures, never one |

Assume more of this. The useful question is what else clean fixtures are hiding.

## 4. A defect in `scan_pants_archives.py`

Your trailing-data check cannot fire:

```python
while chunk := stream.read(1024*1024):
    if trailing > 16*1024**2 or any(chunk):
        raise ValueError('Unexpected data after tar end; manual review required')
```

`gzip.GzipFile` concatenates gzip members transparently and `tarfile`'s stream mode consumes its
source to EOF, so by the time this runs there is nothing left to read. Verified: a `.tar.gz` with
a second gzip member appended passes `scan()` with no error and correct-looking counts.

Risk here is low — 10 of 11 archives matched a publisher SHA-256, which rules out appended data
outright. Only `PanTSMini_Label.tar.gz` lacks a publisher digest.

**I did not patch it.** Its output is cited as evidence in `EXTRACTION-BUDGET-2026-09-22.md`, and
changing the code that produced cited evidence invalidates it. The finding is recorded in the
extraction design document and pinned by
`tests/test_extraction.py::test_appended_data_is_detected_even_though_the_scan_misses_it`.

Whether to fix it, and whether fixing it requires re-running the scan and re-citing its evidence,
is your call.

## 5. What I could not verify myself

**I have never directly observed the extracted data.** My shell on Quinton's Mac is a sandboxed
Linux VM that mounts only the repository; `/Volumes/PROWL-Data` is unreachable from it, and the
`.venv-prowl` binaries are macOS-arm64 so I cannot run the suite there either.

Every number in the observed-layout document came from tool output that Quinton ran and pasted.
**If the tooling lies, I have no independent check.** That is the strongest reason for this review
to come from you: you can read the actual bytes.

Tests were authored under CPython 3.11 and 3.12 in a Linux container. Quinton re-ran them in
`.venv-prowl` each time, which is how the macOS path-length defect surfaced.

## 6. Not in scope

Not asking you to review: the Plan 04 gate state (settled, D-045), the extraction results
themselves (verified by digest), or the governance-document corrections. Not asking for Plan 02
code — that waits on this review.

## 7. Suggested output

A dated findings note under `docs/capstone/` recording what you checked, what you found, and what
you could not determine. Anything confirmed should get a regression test in the relevant suite
rather than only a note. Where we disagree, say so plainly — a documented disagreement is more
useful to Quinton than a resolved one he did not see argued.
