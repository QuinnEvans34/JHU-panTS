# Extraction budget and destination review — September 22, 2026

Status: capacity and isolated destination design pass; extraction has not started. No source
activation, training, archive deletion, or cross-archive merge is authorized by this evidence alone.

## Evidence

The September 21 PanTS scan completed at 21:34:19 UTC: all 11 archives, 297,029 files,
397,622,006,473 declared expanded bytes, no flagged member issues, and 10 matching publisher
image SHA-256 hashes. Labels have a local SHA-256 but no publisher digest. PANORAMA ZIP directory
preflight adds 195,692,251,008 bytes. No NIfTI voxel decompression or cache-size inference is implied.

September 22 read-only diskutil inspection confirms APFS, writable media/volume, and the registered
volume UUID. The sandbox initially blocked DiskManagement/process queries; the approved read-only
retry succeeded. No matching scan/download processes were observed. No drive writes occurred.

## Conservative allocation

| Additional allocation / reservation | Bytes |
|---|---:|
| Extracted payloads, both sources | 593,314,257,481 |
| Filesystem/allocation allowance, 10% of payload | 59,331,425,749 |
| Single sequential archive retry allowance, 64 GiB | 68,719,476,736 |
| Future cache/artifact reservation, 1 TiB | 1,099,511,627,776 |
| Operational free-space floor, 512 GiB | 549,755,813,888 |
| Required free before extraction | 2,370,632,601,630 |
| Available at conservative statvfs check | 3,440,640,000,000 |
| Remaining unallocated | 1,070,007,398,370 |

Existing archives are already reflected in available space and are retained. Destination-local
staging becomes the extracted copy; no second full extracted copy is budgeted. The largest archive
expands to 52,020,675,883 bytes, within the 64 GiB retry allowance. A second retained partial beyond
that allowance requires rebudgeting; never silently delete it or retry indefinitely. The 1 TiB
reservation is a planning allowance, not a measured cache requirement or authorization to create
one. Capacity must be rechecked before launch and during writes; a low-space condition stops work.

## Destination isolation

These candidate roots do not exist; parents resolve without symlinks on the registered source drive:

- `sources/pants/extraction-3b1cd6110811-20260922/`
- `sources/panorama/extraction-bf1d6ba3230f-20260922/`

Under each, give every archive its own child named from its filename without `.tar.gz` or `.zip`.
All 16 child destinations are unique after case/Unicode normalization. Preserve archive-relative
member paths inside those children. The PanTS publisher-test archive remains in its own child;
shared label-source content does not grant permission for test-driven model selection.

This prevents cross-archive overwrite by construction; it does not establish shared case identities,
semantic uniqueness, or compatibility for merging. No flattening or merge is planned. Training
inputs must later resolve explicit files through reconciled manifests, not basename guesses.

## Execution prerequisites / next action

Build and test a bounded standalone extractor, not a Plan 04 workflow runner. Require exclusive
destination creation, per-member path/type/collision validation, no overwrite/link restoration,
byte ceilings, streamed file integrity evidence, mount/capacity checks, and interrupted-write tests.
Recheck archive identity during extraction and record completion only after verification. Preserve
all partials on failure. Begin with one small archive as a controlled pilot before the bulk queue.
No raw member inventories, scans, or labels enter Git. Keep source aliases and scientific runs
disabled until extraction and Plan 02/03 reconciliation pass.
