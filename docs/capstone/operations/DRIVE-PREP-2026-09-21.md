# Drive preparation — September 21, 2026

**Status:** Mounted identity and acquisition receipts rechecked; PANORAMA ZIP directory preflight
passed; PanTS member scan and full extraction budget remain pending. No extraction authorized by
this record, no source activation, and no training readiness claim.

## Verified today

- `/Volumes/PROWL-Data` is the real mounted APFS volume, its UUID matches the ignored local root
  registry, and read-only flags are false. This was a read-only check, not a write/capability test.
- Capacity: 4,000,750,501,888 total bytes; 3,443,647,565,824 available bytes at inspection.
- PanTS: 12 expected files, 361,265,775,573 bytes, all sizes match the pinned acquisition inventory.
- PANORAMA: 5 ZIP files, 194,273,109,050 bytes. CT sizes match the publisher inventory; label ZIP
  size matches the previously recorded local acquisition size, not a publisher archive digest.
- Both September 20 terminal receipts still report `archive_queue_complete` and `source_ready: false`.
  PANORAMA has no network-deferred files. No `.part`/`.partial` files were found in either acquisition
  directory. No matching acquisition/tar/unzip processes were observed by the bounded process query.
- `scientific_runs_enabled` remains false. No root-registry changes were made.

No full payload hashes were rerun today. These checks corroborate acquisition receipts and file
presence/size, not fresh end-to-end integrity or hardware health. No old-drive/recovery files were
touched; the new drive received no writes from this preparation pass.

## PANORAMA ZIP preflight

ZIP central directories were read without extracting or decompressing image/label payloads.

| Archive | Files | Declared expanded bytes |
|---|---:|---:|
| batch_1.zip | 557 | 49,472,888,741 |
| batch_2.zip | 566 | 49,408,519,895 |
| batch_3.zip | 580 | 49,286,960,058 |
| batch_4.zip | 535 | 46,270,993,923 |
| Pinned label ZIP | 2,242 | 1,252,888,391 |
| Total | 4,480 | 195,692,251,008 |

No absolute/traversing/backslash/drive-letter/control-character paths, within-archive duplicate or
case/Unicode-normalized collisions, links/special files, encrypted entries, or file-as-parent
conflicts were detected. This does not establish cross-archive destination compatibility, CRC
validity, image geometry, target labels, or cohort eligibility. Keep each archive's extraction
staging separate until reconciliation; never merge by basename with overwrite enabled.

The expanded figures are archive-declared file sizes (including compressed NIfTI files where
present), not RAM, decompressed voxel arrays, or prepared-cache sizes.

## Budget and remaining work

### PanTS scan launched — 20:39 UTC September 21

Quinton authorized the read-only scan. `scripts/diagnostics/scan_pants_archives.py` passed eight
synthetic tests before launch. It scans all 11 tar.gz files sequentially, counts declared expanded
bytes, checks member safety and gzip integrity, and recomputes compressed SHA-256 in the same pass.
Publisher image hashes are compared; the label archive has no publisher SHA-256. Cross-archive
merge validation and extracted-content reconciliation remain separate. No extraction is performed.

Local log: `outputs/prowl/storage-prep-2026-09-21/pants-scan-active-20260921T2040.jsonl`.
Scanner PID at launch: 68883, tool session 4551 (`caffeinate -i`); verify process identity before signalling.
Progress is emitted about every 30 seconds. A local exclusive scan lock prevents duplicate scans.
A first detached-shell launch left an empty log and no live process; it did not start scanning.
The replacement runs in a retained execution session, with scan-start and first-archive events
confirmed. Idle sleep is inhibited only while the process runs. Keep the laptop powered, lid open,
and drive connected. Reboot/forced sleep/drive
disconnect is not protected; there is no automatic restart or partial-archive resume. Failure or
cancellation preserves logs and does not activate sources. Completion requires `scan_complete`,
not a launch message. No recurring monitoring or notification automation has been configured.

Existing archives are already reflected in free space; do not count them a second time as future
allocation. PANORAMA's declared output alone is about 195.7 GB additional. Retaining the approved
512 GiB free-space floor would leave about 2.70 TB for PanTS extraction, allocation overhead,
temporary workspace, and future artifacts. This is a remaining envelope, **not** an approved full
budget: PanTS expanded sizes and future cache/model allocations still need explicit bounds.

1. Perform a sequential read-only member/expanded-size scan of all 11 PanTS tar.gz archives, with
   progress, cancellation, bounded resource use, and retained evidence. Unlike ZIP directories,
   gzip-compressed tar headers require reading/decompressing through the stream; allow a longer
   drive-connected session. Inspect archive structure only, not held-out image content for selection.
2. Check archive paths, links, special entries, duplicates, case/Unicode collisions, and destination
   conflicts; preserve separation of training and publisher-test sources.
3. Finalize the combined extraction budget, including filesystem overhead, per-archive staging,
   future cache/artifact allowance, and the 512 GiB floor. Recheck mount identity/capacity before writes.
4. Use tested safe extraction into new destination-local staging, with no overwrite or archive
   deletion; validate extracted contents before publishing a source snapshot.
5. Reconcile identities, labels, geometry, duplicates, and protected cohorts before enabling sources.

Local ignored evidence: `outputs/prowl/storage-prep-2026-09-21/mount-and-receipts.json` and
`panorama-zip-preflight.json`. No images, member-name inventories, or local UUID values were added
to this document. This work is standalone data preparation, not Plan 04 implementation.
