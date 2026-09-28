# Extraction run procedure — September 22, 2026

**Status:** Tooling written and unit-tested; no real archive has been extracted.
**Design:** [`EXTRACTION-DESIGN-2026-09-22.md`](EXTRACTION-DESIGN-2026-09-22.md)
**Budget and destinations:** [`EXTRACTION-BUDGET-2026-09-22.md`](EXTRACTION-BUDGET-2026-09-22.md)

Extraction produces *extracted-but-unreconciled* sources. It does not enable a source alias, does
not satisfy G1 or G2, and does not authorize training.

## Before anything touches a real archive

Run the fast suite in `.venv-prowl` from the repository root. Extraction is not authorized until it
passes.

```sh
.venv-prowl/bin/python -m pytest -q
```

Expected: **207 passing** — 155 pre-existing plus 52 new. The new files are
`tests/test_member_safety.py` (28) and `tests/test_extraction.py` (24), split 37 `unit`,
13 `component`, 2 `failure_injection`.

(The suite is larger than the 101 recorded on September 19; `tests/test_archive_scan.py` and
others were added on the 21st. The count here is what the September 22 local run reported.)

These tests were authored under CPython 3.11 and 3.12 in a Linux container, not in `.venv-prowl`
on macOS. **Re-running them locally is a required step, not a formality.** The first local run
found a real ordering defect that both container versions had passed — see the design document.

## Paths

| Role | Path |
|---|---|
| PanTS archives | `/Volumes/PROWL-Data/PROWL/sources/pants/acquisition-3b1cd6110811` |
| PANORAMA archives | `/Volumes/PROWL-Data/PROWL/sources/panorama/acquisition-2026-09-19-bf1d6ba3230f` |
| PanTS destination | `/Volumes/PROWL-Data/PROWL/sources/pants/extraction-3b1cd6110811-20260922` |
| PANORAMA destination | `/Volumes/PROWL-Data/PROWL/sources/panorama/extraction-bf1d6ba3230f-20260922` |
| tar expectations | `outputs/prowl/storage-prep-2026-09-21/pants-scan-active-20260921T2040.jsonl` |
| ZIP expectations | `outputs/prowl/storage-prep-2026-09-21/panorama-zip-preflight.json` |
| Local lock and logs | `outputs/prowl/extraction-2026-09-22/` (git-ignored) |

## 1. Pilot — PANORAMA labels

The smallest pinned archive at 1.25 GB expanded across 2,242 files. It exercises the ZIP path,
per-member CRC validation, the oracle, and promotion, and it measures both raw throughput and
per-file creation cost on this drive.

```sh
mkdir -p outputs/prowl/extraction-2026-09-22

.venv-prowl/bin/python -m scripts.acquisition.extract_sources \
  --registry configs/local/roots.yaml \
  --expectations outputs/prowl/storage-prep-2026-09-21/panorama-zip-preflight.json \
  --source-dir /Volumes/PROWL-Data/PROWL/sources/panorama/acquisition-2026-09-19-bf1d6ba3230f \
  --dest-root /Volumes/PROWL-Data/PROWL/sources/panorama/extraction-bf1d6ba3230f-20260922 \
  --lock outputs/prowl/extraction-2026-09-22/extract.lock \
  --archive panorama_labels-bf1d6ba3230f6b093e7ea959a4bf5e2eba2e3665.zip \
  | tee outputs/prowl/extraction-2026-09-22/pilot-panorama-labels.jsonl
```

**Pass condition:** an `archive_extracted` event with `files: 2242`, the declared byte total, and a
promoted directory with no sibling `*.partial-*`. Anything else stops the queue for review.

Record `throughput_bytes_per_second` and `elapsed_seconds` from that event.

### Decision rule, set before the measurement

`PanTSMini_Label.tar.gz` is the interruption-cost worst case: 287,128 files, 19,802 directories,
52,020,675,883 bytes. Project its runtime from the pilot's per-file and per-byte rates.

| Projection | Action |
|---|---|
| Under 45 minutes | Per-archive atomicity is sufficient. Proceed; no further work. |
| 45 minutes to 2 hours | Still sufficient. An interruption is inconvenient, not expensive. |
| Over 2 hours | Open a decision record for finer-grained recovery before the bulk queue. Directory-level promotion is preferred over a per-member journal; see the design document's rejected alternatives. |

This rule exists so the choice is made against a number rather than against how the night is going.

## 2. Bulk queue

Order, following the acquisition handoff. Labels first because everything downstream needs them and
they are the slowest per byte.

1. `PanTSMini_Label.tar.gz`
2. `PanTSMini_ImageTr_00000001_00001000.tar.gz` — stop here and record throughput
3. The remaining eight `ImageTr` shards
4. The four PANORAMA `batch_*.zip` files
5. `PanTSMini_ImageTe_00009001_00009901.tar.gz` — the publisher test archive, extracted last and
   kept protected; it is never opened for model selection

With no `--archive` flags the tool extracts every pinned archive present in the source directory, in
inventory order. Prefer explicit `--archive` flags per stage so each step is a deliberate act.

```sh
.venv-prowl/bin/python -m scripts.acquisition.extract_sources \
  --registry configs/local/roots.yaml \
  --expectations outputs/prowl/storage-prep-2026-09-21/pants-scan-active-20260921T2040.jsonl \
  --source-dir /Volumes/PROWL-Data/PROWL/sources/pants/acquisition-3b1cd6110811 \
  --dest-root /Volumes/PROWL-Data/PROWL/sources/pants/extraction-3b1cd6110811-20260922 \
  --lock outputs/prowl/extraction-2026-09-22/extract.lock \
  --archive PanTSMini_Label.tar.gz \
  | tee -a outputs/prowl/extraction-2026-09-22/pants.jsonl
```

For an unattended run, keep the machine powered with the lid open and the drive connected, and
inhibit idle sleep for that process only:

```sh
caffeinate -i -w $!
```

## Behaviour to expect

| Situation | What happens |
|---|---|
| Archive already extracted | `archive_already_extracted`, skipped. Re-running the queue is safe and idempotent. |
| Interrupted with Ctrl-C or killed | `extraction_cancelled`. The partial directory remains; the final name was never created. |
| A previous partial exists | Refuses and names it. Inspect, then re-run with `--allow-existing-partial` to extract into a fresh attempt directory. The old attempt is never reused or deleted. |
| Counts or bytes disagree with the pinned scan | Refuses to promote. The partial is retained as evidence. |
| Archive digest disagrees | Same. Do not retry blindly — investigate the archive. |
| Free space nears the floor | Stops with `extraction_failed` before breaching 512 GiB. |
| Volume disappears mid-write | Stops. No fallback directory is ever created on the internal disk. |

There is no automatic resume. An interrupted archive is re-run from the start; completed archives
keep their promoted names, so the queue itself resumes at archive granularity.

## Re-checking a promoted tree

```sh
.venv-prowl/bin/python -m scripts.acquisition.extract_sources ... --verify
```

Walks each promoted directory and compares file count and total bytes against the pinned
expectations. Metadata only, no file contents re-read. Directory counts are reported rather than
enforced, because an archive may omit explicit directory entries whose parents still get created.

Use this if a promotion may have coincided with a power loss — the one narrow window the design
document records as an accepted residual risk.

## What to check afterwards

- Every intended archive has an `archive_extracted` event, and no `*.partial-*` remains.
- Free space still comfortably exceeds the floor, and the 1 TiB cache reservation is intact.
- `configs/local/roots.yaml` still shows `path: null` for both sources and
  `scientific_runs_enabled: false`. **Extraction must not change these.**
- Archives are all still present. Nothing is deleted.

## What comes next, and what it is not

Extraction completion is not source readiness. Still open, owned by their plans: observing the real
on-disk layout and recording it, case identity and cross-source collision analysis (Plan 02),
PANORAMA label mapping, exclusions and duplicate controls (Plan 03, G2), geometry and target
validation (Plan 05), and registered cohort membership (G1).

The immediate next task after a clean extraction is to **observe and document the actual layout**
before any code is written against it. Every downstream component depends on that being real rather
than assumed.
