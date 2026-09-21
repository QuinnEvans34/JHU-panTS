# Storage setup and acquisition start — September 19, 2026

**Status:** Scoped filesystem/restore checks passed; PanTS archive acquisition started; no source ready for training.  
**Authority:** Quinton's approval of the bounded setup, D-258.  
**Local date:** September 19, America/Denver; machine-readable records use September 20 UTC.

This is the earlier setup/start checkpoint. The later
[overnight handoff](OVERNIGHT-ACQUISITION-2026-09-19.md) supersedes its live queue status: PANORAMA
has also started, its label ZIP is verified, and the current fast suite passes 101 tests.

## Completed

- Confirmed the intended external APFS volume UUID, actual mount, and separate internal backup
  failure domain. Kept the external drive unencrypted under D-256.
- Created the approved `PROWL` workspace with `sources/pants`, `sources/panorama`, `artifacts`,
  `artifacts/quarantine`, and `scratch`. Existing recovery image/map files were left in place;
  their sizes and modification times were unchanged. Their contents were not validated.
- Registered local roots/volume identities in ignored `configs/local/roots.yaml`. The reviewable
  example and setup-only schema are under `configs/local/`. Both scientific source paths and
  snapshot IDs remain null; `scientific_runs_enabled: false`.
- Established the internal `PROWL-Backups` destination: **20 GiB cap**, **100 GiB internal free-space
  floor**, selected controls/keepers only, no automatic deletion. This is not an off-site backup
  or a complete dataset mirror. A recurring backup service has not been implemented.
- Passed the small diagnostic: write/fsync/read/hash, same-volume rename, two schema-valid review
  appends, competing-process advisory lock rejection/release, partial-versus-complete selection,
  long/Unicode names, case behavior, and symlink-boundary observation.
- Copied generated JSON, review JSONL, and a tiny NumPy array to the internal backup; verified hashes;
  restored from those backup bytes and loaded them through schema/array consumers. A deliberately
  corrupted copy was detected. This is **not** a trained-checkpoint restore drill.
- Copied the retained manifest, base train/validation/test lists, acquisition inventory, and local
  roots registry to both a new external controls directory and internal backup directory. All six
  copy hashes matched. The four retained scientific-control hashes still match the September 8 audit.

## Evidence and limits

The diagnostic used a unique directory with less than 16 MiB of generated content. Evidence is
retained, not deleted. Exact device identities/absolute paths remain in ignored local configuration
and on-device reports rather than portable scientific identities.

| Evidence | Location / result |
|---|---|
| Diagnostic source | `scripts/diagnostics/storage_setup.py` |
| Diagnostic report | `PROWL/.storage-check-ccxb3p02/report.json` on the external drive |
| Independent synthetic backup/catalog | `PROWL-Backups/storage-check-ccxb3p02/` on the internal SSD |
| Verified controls | External `PROWL/artifacts/setup-controls-2026-09-19/` and internal `PROWL-Backups/setup-controls-2026-09-19/` |
| Baseline controls | Hashes in [CURRENT-INVENTORY.md](../data/CURRENT-INVENTORY.md) reconfirmed before copying |
| Registry tests | 7 new offline tests; 74 total passed at that checkpoint |
| Download guards | 13 new offline tests; **87 total passed**, 2 visible upstream PyTorch deprecation warnings |
| Latest test evidence | Ignored `outputs/prowl/testing/foundation-2026-09-19/acquisition-guards-01.xml` |

The primary had 3,999,211,560,960 bytes free after the diagnostic; the internal SSD had about
185.5 billion bytes free. Free space changes during acquisition. macOS reports ownership disabled
on the external APFS volume: mode bits are not an enforced source-immutability boundary. Hardware
health, power-loss durability, safe disconnection/reconnection, production path resolution and
publication, trained-model restore, and full G0/G8 reproduction are **not** certified by this test.
No Plan 04 code/spike is authorized or implemented by these standalone operational tools.

## Publisher inventory and capacity boundary

The public [acquisition inventory](../data/acquisition-2026-09-19.json) pins:

- PanTS Mini Hugging Face revision `3b1cd61108116b58ea5c1ddb3512c1847d965f96` and its 11 LFS
  file sizes/SHA-256 values; metadata, nine training archives, and the opaque publisher-test archive.
- PanTS's separate JHU label archive: 15,561,944,549 bytes with ETag/Last-Modified evidence.
  This URL is mutable and has **no known publisher SHA-256**. Acquisition requires its matching
  entity validator and records a local SHA-256; this is weaker than a publisher-authenticated digest.
- PANORAMA's four versioned Zenodo CT records, file sizes and publisher MD5 values, plus a fixed
  label-repository commit. PANORAMA downloads have **not** started.

Known CT archives, PanTS labels, and PanTS metadata total **555,447,458,163 bytes** across both
sources; the compressed PANORAMA label snapshot is additional and not yet measured. The current
PanTS queue is **361,265,775,573 bytes** (about 361 GB decimal). No extraction is included.

The standalone downloader reserves **512 GiB** free on the external volume, checks the conservative
whole PanTS queue before starting, and rechecks the mount/remaining space during transfers. The
remaining multi-terabyte space is not a promise that arbitrary extraction/caches will fit. Before
extraction, inventory archive members and expanded bytes, reject unsafe paths/links, and budget
expanded sources + simultaneous temporary files + future cache/artifacts + the free-space reserve.
Do not auto-extract or delete archives to make that budget fit.

### Rights discrepancy requiring later reconciliation

The pinned [PanTS GitHub license](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/LICENSE)
is labeled CC-BY-NC-ND-4.0; the pinned [Hugging Face card](https://huggingface.co/datasets/BodyMaps/PanTSMini/blob/3b1cd61108116b58ea5c1ddb3512c1847d965f96/README.md)
is labeled CC-BY-NC-SA-4.0. Preserve both, restrict this acquisition to local noncommercial research,
and resolve applicability before public redistribution/derived release. This record does not grant
permission to publish data or settle legal interpretation. PANORAMA CT records identify CC-BY-NC-4.0;
label/code/data terms remain source-specific release checks.

## Running acquisition

`scripts/acquisition/download_pants.py` is a standalone download-only utility, not the workflow
orchestrator, generic artifact writer, cohort registrar, or training launcher. It retains `.part`
files, rejects an ignored/mismatched range request, checks exact size and available publisher hashes,
and records local SHA-256 receipts. It does not extract, delete, activate source aliases, inspect
publisher-test cases, or change historical configs. The advisory lock only prevents duplicate
download processes in this one acquisition directory.

Started at **21:39:58 MDT** (03:39:58 UTC). Metadata downloaded and passed publisher SHA-256.
The first large transfer is the JHU label archive, followed by the image archives. This is an
in-progress observation, **not** completion of the 12-file queue. Live bytes/events are in:

`PROWL/sources/pants/acquisition-3b1cd6110811/attempt-20260920T033958365521Z.jsonl`

Use the `attempt-*.jsonl` entries in that directory if a later restart creates a new attempt.
Only `verified_download`/`verified_existing`
events with matching payload hashes describe completed files; `.part` is never a complete source.

Resume after an interruption with the same pinned inputs (never launch a second copy while one runs):

```sh
.venv-prowl/bin/python scripts/acquisition/download_pants.py \
  --inventory docs/capstone/data/acquisition-2026-09-19.json \
  --roots configs/local/roots.yaml
```

Keep the drive connected and the Mac awake. Network failures retain partial bytes; integrity failures
stop for investigation. Do not swap inventory revisions underneath an active transfer.

## Next

1. Complete and verify the PanTS archive queue; prepare the separate PANORAMA queue.
2. Inspect safe archive structure/expanded-space requirements, then extract into pinned staging.
3. Reconcile metadata, IDs, labels/geometry, and protected memberships before registering sources/cohorts.
4. In parallel, finish the supported Node/UI baseline and reviewed Git checkpoint. No training starts
   simply because bytes have arrived. Plan 04's explanation/explicit coding authorization remains.
