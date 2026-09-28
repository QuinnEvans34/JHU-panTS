# Observed-layout inventory — procedure

**Status:** Tooling written and tested; no extracted tree has been inventoried yet.
**Tool:** `scripts/diagnostics/inventory_sources.py`
**Tests:** `tests/test_inventory.py` (19)

## Why this runs before any Plan 02 or Plan 03 code

Every downstream component encodes assumptions about the data's shape: how a case is identified,
where its image and labels live, what a complete case contains, and whether two sources can share
one identifier namespace. Those assumptions are currently unverified. The previous project's two
most expensive defects — the validation-leakage bug and the EXP-11 train/eval mismatch — were both
assumptions about data nobody had inspected, and neither announced itself as an error.

This step converts assumption into recorded observation. It is deliberately the first thing that
happens after extraction and before the data layer is written.

## What the tool does, and what it refuses to do

It walks extracted trees reading **directory entries and file sizes only**. It never opens a file,
reads a NIfTI header, or touches voxels. It follows no symlinks and writes nothing into a source
tree.

It reports:

| Output | Question it answers |
|---|---|
| Layout shape | Is this directory-per-case or file-per-case? Inferred from evidence, not assumed |
| Identifier patterns | Digit-masked shapes, e.g. `PanTS_#`, with counts and examples |
| Structural fingerprint | Every distinct path-within-case and how many cases have it |
| Complete combination | The majority file set, and how many cases match it |
| Incomplete cases | Which cases deviate, named |
| Zero-byte files | Present-but-empty, which the previous project confirmed as genuine source defects |
| Size outliers | Cases at 10x or 0.1x the median, which is how corrupt oversized masks previously surfaced |
| Identifier overlap | Pairwise intersection between sources |

It establishes **no** claim about geometry, label semantics, annotation quality, patient
uniqueness, source eligibility, or cohort membership. Those belong to Plans 02, 03 and 05.

## The overlap result is the one to read carefully

A non-zero intersection between PanTS and PANORAMA identifiers does not prove the two sources
describe the same subject. It proves the identifiers cannot be merged into a single namespace
without an explicit disambiguation rule, because a naive merge would silently treat two subjects
as one — or one as two. Plan 02 owns that rule.

A zero intersection is equally not proof of subject disjointness. Two sources can describe the same
patient under different identifiers, which is a duplicate-control problem that Plan 03 owns and
that no filesystem inventory can answer.

## Running it

Point `--source NAME=PATH` at each promoted extraction directory; repeat per tree.

```sh
.venv-prowl/bin/python -m scripts.diagnostics.inventory_sources \
  --source pants-labels=/Volumes/PROWL-Data/PROWL/sources/pants/extraction-3b1cd6110811-20260922/PanTSMini_Label \
  --source pants-train-01=/Volumes/PROWL-Data/PROWL/sources/pants/extraction-3b1cd6110811-20260922/PanTSMini_ImageTr_00000001_00001000 \
  --source panorama-labels=/Volumes/PROWL-Data/PROWL/sources/panorama/extraction-bf1d6ba3230f-20260922/panorama_labels-bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665 \
  --out outputs/prowl/inventory-2026-09-22/inventory.json \
  --summary outputs/prowl/inventory-2026-09-22/OBSERVED-LAYOUT.md
```

Add each extracted tree as it completes; the tool is read-only and safe to re-run.

**Keep the publisher-test tree out of the first run.** Inventorying `PanTSMini_ImageTe_*` is
structurally harmless, but do it as a deliberate separate act so no habit forms of sweeping the
held-out set into routine commands.

## Cost

Measured at roughly 17,000 files per second on local storage. The 287,128-file label tree projects
to about 17 seconds there, and a few minutes over USB. The JSON record is about 250 KB at full
PanTS scale, because output is aggregated by structural pattern rather than listed per file.

## Afterwards

The JSON and generated Markdown land under ignored `outputs/`. **Neither is the record.** Review
the digest, confirm it against a manual spot-check of two or three real cases, then write the
reviewed findings into `docs/capstone/data/OBSERVED-LAYOUT-<date>.md` as the citable artifact,
noting anything the tool surfaced that needs a decision.

Findings that will need decisions rather than documentation:

- identifier overlap between sources, if any;
- incomplete cases, and whether they are excluded or repaired;
- zero-byte and oversized files, which the previous project resolved with a union-based mask
  resolver and a 300 mL guard — that resolution is prior art to re-derive, not to assume;
- any layout that contradicts what Plans 02, 03 or 05 currently assume, which requires amending
  the plan rather than quietly coding around it.
