# Current storage and environment inventory

**Status:** Scoped capability/root/backup setup passed; PanTS archive acquisition started  
**Observed:** 2026-09-19, approximately 21:21 America/Denver  
**Last reviewed:** 2026-09-19

## September 19 update

**Later approved setup:** D-258 authorized the new workspace and independent internal backup
(20 GiB cap; 100 GiB internal free-space floor). The folders and ignored roots registry now exist;
bounded filesystem checks and the synthetic independent restore passed. Controls were copied and
hash-verified on both devices. PanTS archive acquisition has started; no source is training-ready.
See [STORAGE-SETUP-2026-09-19.md](STORAGE-SETUP-2026-09-19.md) for evidence, live-receipt location,
and limits. The read-only observations below are preserved as the earlier checkpoint, not current
claims that folders remain absent or no writes have occurred.

Quinton confirms that `JHU-PanTS` permits neither reads nor writes. Treat it as unavailable with no
source/backup role; recovery is not part of the active work (D-257). No hardware diagnosis or repair
was attempted. Fresh acquisition is queued in [DATA-ACQUISITION-QUEUE.md](DATA-ACQUISITION-QUEUE.md).

Earlier today the exact `/Volumes/PROWL-Data` path was absent. Quinton then reconnected it; the
follow-up read-only check verified the actual mount and the same volume UUID observed September 18.
Encryption remains resolved under D-256. The earlier absent-mount finding is superseded, not erased.

| Follow-up observation | Result / limitation |
|---|---|
| Device and mount | Western Digital Elements 2621; physical `disk4`, store `disk4s1`, volume `disk5s1` at `/Volumes/PROWL-Data`; device numbers are session-specific |
| Stable identity | Volume UUID matches September 18; exact value remains local operational information |
| Filesystem/access | APFS, unlocked, unencrypted; media and volume read-only flags are false; no application write test performed |
| Capacity/free | Physical size 4,000,752,599,040 bytes; APFS container 4,000,750,501,888 bytes; available 3,999,212,695,552 bytes (about 4 TB decimal) |
| Existing project-adjacent files | `JHU-PanTS-recovery.img` (1,051,066,368 bytes), `JHU-PanTS-recovery.map` (27,011 bytes), `JHU-PanTS-recovery.map.bak` (26,699 bytes); names/sizes inspected only, contents not opened |
| Other root entries | `.DS_Store`, `.Spotlight-V100`, `.fseventsd`; not modified |
| Hardware health | USB SMART status unavailable; no media-health certification or filesystem repair |
| Internal SSD | 185,461,542,912 bytes available (about 173 GiB); separate mounted device from the external volume |
| Proposed setup paths | New `PROWL` folder on the external drive and `PROWL-Backups` under the user home do not already exist or resolve through symlinks; neither was created |

All existing recovery files are preserved. Their presence does not establish successful recovery,
source completeness, or a usable independent backup. No old-drive probing, external-drive writes,
format/encryption changes, downloads, or capability/restore test occurred.

The first machine-readable mount assertion expected a `Mounted` key not returned by this system's
plist. The follow-up checked the actual mount point and `Path.is_mount()` plus UUID/filesystem and
distinct device IDs successfully; no filesystem change was needed.

## Why this record exists

Storage planning must separate facts observed on the machine from facts remembered from the prior
project and intentions for new hardware. This file is updated when the drives are connected. It does
not authorize modifying either drive.

## Current read-only audit — September 18

| Item | Verified result | Consequence |
|---|---|---|
| New volume | `PROWL-Data` at `/Volumes/PROWL-Data` | Replaces the September 10 `Elements`/NTFS state |
| Filesystem/access | APFS; `Volume Read-Only: No`; unlocked | Writable according to macOS; no application write test has been run |
| Physical device | Western Digital `Elements 2621`, USB, GUID partition map | `disk4` physical / `disk4s1` store / `disk5s1` volume during this session; these identifiers can change |
| Volume identity | APFS volume UUID observed | Bind the future ignored local registry to this UUID after setup; do not rely on the display name alone |
| Capacity | Physical disk 4,000,752,599,040 bytes; APFS container 4,000,750,501,888 bytes | About 4 TB decimal / 3.6 TiB |
| Free capacity | Container reported 4,000,264,278,016 bytes free | Essentially empty; snapshot only |
| Encryption | `Encrypted: No`; `FileVault: No` | Quinton explicitly chose to retain unencrypted APFS on September 18 (D-256); no reformat/encryption action needed or taken |
| Top-level contents | `.DS_Store`, `.Spotlight-V100`, `.fseventsd` | No project directories or data visible at root |
| Hardware health | SMART not supported through the reported USB connection | No health certification from this inspection |
| Internal SSD | Approximately 191 GiB available | Candidate for bounded copies of small irreplaceable records/selected keepers, subject to capacity review |
| Old `JHU-PanTS` | Name appears under `/Volumes`, but no filesystem appears in the mount table | Remains unavailable; cause and recoverability are unconfirmed. No further probing performed |
| Retained data controls | Local manifest and base train/val/test lists still exist; all four SHA-256 values match the September 8 inventory | Reconciliation controls survive; this does not prove unavailable CT/label bytes are intact |
| Git protection | `docs/capstone/` and `src/data/` have no tracked files in this checkout | Prepare a reviewed Git checkpoint before expanding implementation |

Quinton reports the old drive may have failed and accepts redownloading the data. Old-drive recovery
is optional. The working path is fresh pinned acquisition on `PROWL-Data`, reconciliation against
the retained control records, and a healthy backup target independent of the new drive.

This audit read mount/device information and top-level contents only. It did not write to either
drive, run filesystem repair, verify all media sectors, or establish sustained read/write performance.

## Historical observed state — September 10

| Item | Observed state | Confidence/limitation |
|---|---|---|
| Git workspace | `/Users/quintonevans/Desktop/Quinn/Desktop/GitHub/Neuro-data` | Current local checkout; absolute path is not portable identity |
| Internal free space | Approximately 176 GiB available when the drives were inspected | Snapshot only; APFS shared-space reporting can change |
| Repository `outputs/` | Approximately 354 GB | Ignored historical tree; detailed keeper/cache inventory not yet done |
| `ui/public/cases/` | Approximately 201 MB | Small relative to scientific outputs; content/release status still requires audit |
| `docs/capstone/` | Under 1 MB | Appropriate for Git once reviewed |
| New 4 TB drive | `/Volumes/Elements`, 4.0 TB NTFS volume, approximately 4.0 TB free, mounted read-only over USB | Exact UUID observed and reserved for the future ignored local registry; NTFS cannot be the writable PROWL root in its current macOS mount state |
| Old `JHU-PanTS` drive | A `/Volumes/JHU-PanTS` mount point appeared, disappeared, and reappeared, but no mounted filesystem/device was present in `mount` or `diskutil`; a follow-up device query stalled | Not successfully mounted or safe to inventory yet; likely connection, power, adapter, or filesystem-recognition issue |
| Current PanTS config | Historical `/Volumes/JHU-PanTS/PanTS/data/` path in `configs/level45.yaml` | Must not be treated as a valid capstone root until resolved/verified |
| Current cache config | Historical internal-SSD comments/paths | Capstone cache root remains undecided until 4 TB setup |
| Git exclusions | Raw NIfTI/archive/checkpoint/output/environment/secret/local-reference patterns broadly ignored | Precision and ignored-source audit still required before release |

## Historical hardware assessment — September 10

| Device | Reported purpose/history | Planned default | Verification needed |
|---|---|---|---|
| New 4 TB external drive | Western Digital drive bought for this capstone; mounted as `Elements` | Candidate primary source/artifact/scratch workspace after a writable filesystem decision | Physical device `disk5`, volume `disk5s1` during this session; NTFS; 4,000,750,501,888-byte disk; 4,000,522,444,800 bytes free; USB; macOS volume read-only; SMART unavailable through the connection; capability test cannot proceed while read-only |
| Old approximately 500 GB drive | Used for the preceding project and historically held PanTS data; expected as `JHU-PanTS` | Preserve/read-only legacy/reference source; optional selective backup after inventory | Reconnect/stabilize mount first; then exact size, UUID/filesystem, PanTS paths/counts/checksums, other contents, and only-copy risks |
| 1 TB internal SSD | Code and current ignored historical outputs | Code/env/docs/small fixtures; avoid new large canonical artifacts | Current free-space baseline and historical-output classification |
| Apple M5 Pro / 64 GB unified memory | Primary development/training system | Local MPS baseline | Exact OS/Python/PyTorch/MONAI/MPS environment and representative benchmark |

User-reported information is valid planning context but does not replace a machine-readable device
inventory.

## Historical source facts to reconcile

Prior documentation reports:

- PanTS Mini at `/Volumes/JHU-PanTS/PanTS/data/`;
- 9,000 training images and 901 official test images;
- label directories for approximately 9,901 cases;
- approximately 382 GiB used and 83 GiB free on the old volume at the time;
- manifest and split generation from this source;
- occasional external-drive disconnection during evaluation.

These are historical evidence, not a current checksum assertion. Reconcile the fresh pinned source
against retained controls without trusting case counts alone; access to the old drive is not required.

## Current `outputs/` classification problem

The approximately 354 GB ignored tree includes historical caches, checkpoints, evaluation outputs,
and run archives. Before any copy or cleanup, create an exact inventory with:

- path relative to `outputs/`;
- type/category guess and owning script/run when knowable;
- byte and file count;
- last modification time as operational clue only;
- content/checksum or existing manifest identity;
- keeper/control/controlled/exploratory/cache/scratch/unknown classification;
- descendants or references found in docs/registries;
- proposed action: leave, copy-and-verify, rebuildable, quarantine, or later cleanup review.

`mtime`, directory name, `best.pt`, and largest file are never enough to identify the correct model.
Unknown means leave in place.

## Historical external-drive inventory — September 10

Complete one row per mounted volume before assigning roles:

| Field | New 4 TB candidate | Old ~500 GB drive |
|---|---|---|
| Audit timestamp | 2026-09-10 | 2026-09-10 attempted; incomplete |
| Device identifier | `disk5` / `disk5s1` during this mount; do not treat as stable | No device identifier exposed during the audit |
| Volume UUID | Observed; exact value belongs in future ignored local registry | Unknown |
| User-visible name | `Elements` | Mount-point name `JHU-PanTS`; filesystem did not remain mounted |
| Mount path | `/Volumes/Elements` | `/Volumes/JHU-PanTS` appeared as an empty/stale mount point only |
| Filesystem | NTFS (`Microsoft Basic Data`) | Unknown |
| Nominal/usable capacity | 4.0 TB / approximately 4.0 TB | Unknown; user reports approximately 500 GB |
| Free bytes | 4,000,522,444,800 | Unknown |
| Connection/bus | USB | Unknown |
| Encryption state | Not established by this audit | Unknown |
| Read-only/read-write state | Media is not hardware read-only, but macOS mounted the NTFS volume read-only | Not mounted |
| Health information available | SMART not supported through the reported connection | Unknown |
| Filesystem verification result | Not run; only read-only identity/content inspection | Not available |
| Top-level inventory hash/record | Not generated; drive contains vendor installer files and `System Volume Information` only at top level | Not available |
| Existing source/control records | None observed at top level | Not accessible |
| Known only-copy material | None observed; approximately 228 MB used, primarily vendor files | Potential historical PanTS source; preserve until proven otherwise |
| Proposed role | Candidate primary after writable filesystem decision and capability test | Legacy/reference; selective backup candidate only after successful inventory |
| Approved role/date | Not approved | Not approved |

## Inspection sequence for an additional usable drive

1. Connect one drive.
2. Confirm its device/volume identity without writing.
3. Record filesystem, capacity, free bytes, mount/read-only state, and available health information.
4. List top-level paths and measure sizes/counts without following unexpected links outside the
   volume.
5. Locate existing manifests, checksums, licenses, and known source roots.
6. Disconnect safely, then repeat for the other drive if needed.
7. Present the completed inventory to Quinton before any writable-role assignment.

Do not create a “test folder” during the read-only phase. The new drive's scoped capability test is a
separate approved step after identity and existing-content review.

## Remaining work recorded after the September 18 audit (historical checklist)

The capability/root/initial backup choices below were subsequently completed in the September 19
setup record. Full source reconciliation, real-artifact restore, and production preflight remain open.

- Complete the scoped write/read/hash/rename/append/lock test on `PROWL-Data` and record its limits.
- Freeze root assignments and register the observed APFS identity in ignored local configuration.
- Retain unencrypted APFS under Quinton's explicit D-256 decision; no encryption setup remains.
- Pin the new PanTS source revision/archive inventory and reconcile it against retained metadata and
  protected membership controls. A new download is not automatically byte-identical to the old one.
- Measure source/archive/extraction/PANORAMA space needs before scheduling the full download.
- Select a healthy independent destination for small irreplaceable records and selected keepers;
  exclude the unusable `JHU-PanTS` drive from available backup capacity.
- Classify historical laptop outputs only as needed; preserve all unknown material.

Old-drive diagnosis and recovery are outside the active work. They cannot prevent preparing the new
storage or setting up synthetic tests and fresh data acquisition.
