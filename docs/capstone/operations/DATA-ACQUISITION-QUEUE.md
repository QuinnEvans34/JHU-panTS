# Fresh data acquisition queue

**Status:** PanTS/PANORAMA archives acquired; extraction and source reconciliation pending; drive currently unavailable  
**Updated:** 2026-09-20  
**Authority:** Quinton's direction; D-257/D-258; approved Plans 02, 03, and 10

## Decision

Quinton reports that `JHU-PanTS` is broken and permits neither reads nor writes. Treat it as
unavailable, with zero usable source or backup capacity. Do not wait for recovery or attempt repair
as part of PROWL setup. The working route is fresh downloads to the verified `PROWL-Data` drive.
This records the user's report, not an independent hardware diagnosis.

The retained repository manifest and protected base-split hashes remain reconciliation controls.
They do not prove that a newly downloaded publisher revision matches the unavailable old bytes.
Historical experiment results remain historical; no old trained model becomes capstone initialization.

## Order and overlap

| Order | Work | Completion evidence |
|---|---|---|
| Foundation (scoped checks passed) | Clean Python test foundation using generated inputs | Exact dependencies and unchanged historical test results |
| Alongside foundation | Prepare storage and acquisition inventory | Mounted primary identity; approved independent backup target/budget; capability and small control-restore checks |
| First imaging source | Pin and acquire PanTS metadata, labels, and image archives | Publisher/revision/rights inventory, expected sizes and checksums where available, verified completed files |
| Second imaging source | Pin and acquire PANORAMA CT and labels under its own terms | Separate source identity and Plan 03 mapping/integrity evidence |
| After each verified batch | Reconcile IDs, labels, geometry, exclusions, and protected memberships | Honest partial/complete status; registered eligible cohorts before training |

Download preparation does not wait for retrieval, UI redesign, a stakeholder meeting, or the entire
orchestration implementation. Large transfers may overlap synthetic tests/documentation once their
own storage and source checks pass. Acquiring data does not authorize training or inspecting the
publisher test set for model selection. PANORAMA acquisition is not required for a PanTS-only
baseline that meets its own prerequisites.

## Before starting bulk transfer

- [x] September 19 follow-up: verified the actual mounted `PROWL-Data` UUID, writable flags, contents,
  and space. Recheck before writes; never create a fallback directory if the mount is absent.
- [x] Register exact source/staging/artifact roots in ignored local configuration; confirm bounded
  temporary capability-test paths before writing.
- [x] Select an independent backup target and explicit budget for manifests, records, and selected
  keepers; perform the initial small control-restore test. A second folder on the primary drive does
  not count. A full mirror of downloadable raw data is not required.
- [x] Verify official source locations, access/usage terms, exact publisher revisions, file inventory,
  compressed sizes, and publisher hashes where supplied. Record absent publisher hashes honestly.
- [ ] Budget compressed archives + extracted images/labels + temporary extraction + future cache/
  artifacts + safety headroom across both sources. Do not reuse historical size estimates as an
  exact forecast. Archive-only acquisition was separately bounded and has completed; no extraction
  occurs until expanded-size/safe-member review. See the setup record for the capacity boundary.
- [x] Use resumable partial downloads, with completion verified before publication; never interpret
  a partial file as a completed archive. Pin source revisions rather than mutable `main` URLs.
- [ ] Check archive members for unsafe paths/links before extraction, preserve source separation,
  and avoid blind execution of historical GNU-only download/extraction scripts on macOS.
- [x] Preserve archives until integrity, extraction, and retention decisions are recorded. No
  automatic archive deletion or cleanup of historical laptop outputs is authorized.
- [x] Keep publisher-test data protected from development and preserve source-specific provenance.
  Its archive is acquired opaquely, not opened for model selection; no source alias is enabled.

## Current operational facts

Quinton approved the scoped setup under D-258. The folders and ignored registry now exist, the
filesystem checks and initial independent synthetic restore passed, and six retained controls were
copied/hash-verified on both devices. The acquisition checkpoint passed **101 tests**; relocation
and workspace checks subsequently brought the latest full fast suite to **105 passes**, with two
upstream warnings. See [relocation verification](RELOCATION-2026-09-20.md) and
[the storage/acquisition record](STORAGE-SETUP-2026-09-19.md) for evidence and limitations.

The [publisher inventory](../data/acquisition-2026-09-19.json) pins exact image archive revisions and
hashes. Both archive queues completed September 20: PanTS at 08:33:43 UTC and PANORAMA at
21:05:11 UTC. PANORAMA labels were checked against pinned Git blobs and all four CT batches
passed publisher checksum verification. See [the completion checkpoint](STATUS-2026-09-20.md)
for receipt references and evidence limitations; the [overnight handoff](OVERNIGHT-ACQUISITION-2026-09-19.md)
preserves the September 19 startup history. The drive is currently unavailable and was not reread
for this update. Both queues recorded `source_ready: false`; extraction/reconciliation and alias
activation remain pending. Archive completion is not a ready training snapshot. PanTS label hashing
is local (publisher digest unavailable), and the PanTS license discrepancy remains a release concern.

Literature is not in the overnight queue: its exact search/cutoff, contact configuration and
rights-tested acquisition remain the next small preparation task under Plan 07. Model/embedding
weights remain subject to exact model selection/pinning; no historical model is reused.

Existing recovery files, historical environments/models/configs, and previous proposal versions are
preserved. Keep unencrypted APFS as chosen; no formatting or repair is requested.

## Approved bounded setup — executed September 19

- Keep all new external work inside `/Volumes/PROWL-Data/PROWL/`, separate from the existing recovery
  files. Use `sources/pants/` and `sources/panorama/` for pinned snapshots, `artifacts/` for outputs,
  and `scratch/` for downloads-in-progress/cache. Source aliases resolve to verified snapshot roots,
  not an ambiguous mixture of versions. Quarantine belongs under `artifacts/quarantine/`.
- Use a unique `.storage-check-<id>/` directory inside that new `PROWL/` folder for a small generated
  filesystem diagnostic (under 16 MiB). No production workflow writer/runner code or Plan 04 spike
  is included. Do not touch the recovery image/maps or simulate disconnection without separate
  agreement.
- Approved independent backup: `/Users/quintonevans/PROWL-Backups/` on the internal SSD, capped at
  **20 GiB**, with operations refusing to reduce internal free space below **100 GiB**. Back up
  selected manifests, experiment/review records, and selected keeper checkpoints, not raw datasets
  or caches. This is a local second-device copy, not an off-site backup. Never delete evidence
  automatically to fit the cap; revise the budget/target when needed.
- Scoped checks and the small restore are complete. Evidence is retained; no power-loss test,
  trained-model restore, production source immutability, or full G0/G8 qualification is implied.
  Source aliases remain disabled pending archive/extraction and Plan 02/03 reconciliation.
