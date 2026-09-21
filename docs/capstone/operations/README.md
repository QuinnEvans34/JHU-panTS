# Plan 10 reproducibility and operations package

**Status:** Approved design; scoped storage/Python checks passed; full operations qualification pending  
**Owner:** Quinton Evans  
**Status reconciled:** 2026-09-20

## Purpose

This package turns the file-first architecture into a safe workstation operating model. It explains
where PROWL data belongs, how paths are resolved without becoming scientific identity, what must be
captured for a run, how interrupted writes and backups are verified, and what evidence would justify
rented compute.

The package is deliberately more detailed than the proposal. The proposal commits to outcomes; these
documents prevent storage, environment, and recovery details from being invented during a long run.

## Read in this order

1. [`../implementation/10-reproducibility-and-operations.md`](../implementation/10-reproducibility-and-operations.md)
   — governing decisions, sequence, gates, and fallbacks.
2. [`CURRENT-STORAGE-INVENTORY.md`](CURRENT-STORAGE-INVENTORY.md) — what is known, observed, and
   still unknown about the laptop and both drives.
3. [`STORAGE-ROOTS-AND-ARTIFACTS.md`](STORAGE-ROOTS-AND-ARTIFACTS.md) — physical roles, aliases,
   publication, hashing, and filesystem boundary.
4. [`ENVIRONMENT-AND-RUN-IDENTITY.md`](ENVIRONMENT-AND-RUN-IDENTITY.md) — Python/Node/code/config
   capture and clean-versus-dirty run rules.
5. [`BACKUP-RETENTION-AND-RECOVERY.md`](BACKUP-RETENTION-AND-RECOVERY.md) — what is retained,
   copied, restored, or safely rebuildable.
6. [`PREFLIGHT-MIGRATION-AND-REPRODUCTION.md`](PREFLIGHT-MIGRATION-AND-REPRODUCTION.md) — checks and
   exact non-destructive setup sequence.
7. [`COMPUTE-DECISION-PROTOCOL.md`](COMPUTE-DECISION-PROTOCOL.md) — local measurements, schedule
   projection, and D-210 remote-compute gate.

Current execution: [fresh acquisition queue](DATA-ACQUISITION-QUEUE.md) and
[first Python foundation evidence](../testing/FOUNDATION-2026-09-19.md), followed by
[storage/restore and acquisition-start evidence](STORAGE-SETUP-2026-09-19.md).

Latest checkpoint: [September 20 status](STATUS-2026-09-20.md). Both archive queues completed;
extraction and source validation remain pending. The drive is unavailable during away-from-home
work. UI foundation is next; full operational qualification remains open.

## Governing boundaries

- `PROWL-Data` was reconnected and verified on September 19. D-258 then authorized the scoped
  filesystem/root setup and independent internal backup (20 GiB cap, 100 GiB free-space floor).
  Bounded filesystem/restore checks passed. Both archive queues completed September 20;
  source aliases remain disabled pending extraction and source reconciliation.
- Quinton reports the old drive cannot read/write. Treat it as unusable with no source/backup role;
  recovery is outside the active work. Fresh pinned acquisition is the working route (D-257).
- A physical drive's volume name or absolute path never defines a source or artifact identity.
- Code and small permitted controls belong in GitHub; raw imaging, article text, checkpoints, and
  large artifacts do not.
- Copying a file does not create a verified backup; a checksum and restore drill do.
- A rebuild recipe does not create a backup; it is a different recovery mechanism.
- Same-drive folders are one failure domain even when they serve different logical roles.
- No drive reformat, bulk migration, deletion, paid compute, or remote upload follows merely from
  approving this design.

## Plan 10 review checklist

- [x] Accept the intended roles of the internal SSD, 4 TB drive, and old 500 GB drive.
- [x] Accept the five root aliases and ignored-local/committed-example registry pattern.
- [x] Accept the APFS preference and capability-test-first rule for an existing filesystem.
- [x] Accept same-filesystem atomic publication and completion-marker rules.
- [x] Accept SHA-256/derivation identity and write-time inventory policy.
- [x] Accept retention classes, 14-day quarantine default, and exact-list cleanup authorization.
- [x] Accept tiered backup and the requirement that restoration be tested.
- [x] Accept clean-code rules for controlled, publisher-test, stakeholder, and release runs.
- [x] Accept the fail-closed preflight and sequential MPS/writer defaults.
- [x] Accept local-first compute and the measured D-210 remote-compute trigger.
- [x] Accept the four bounded reproduction recipes with branch-specific startup and full pre-G8 checks.
- [x] Keep `docs/experiments.md` active: plan before every experiment, record every attempt, and
  explain evidence-based follow-ups.
- [x] September 18 read-only inventory completed; September 19 update records the needed new-drive
  remount and unusable old drive. No drive-health certification is implied.
- [x] Complete scoped new-drive capability/root checks and select the independent internal backup
  target (September 19 evidence; not a drive-health certification or full restore qualification).
- [x] Quinton chose to keep the current unencrypted APFS configuration (D-256, 2026-09-18).
- [x] Confirm the independent backup target and size budget before bulk acquisition (D-258:
  20 GiB cap, 100 GiB internal free-space floor).

## What approval means

Approval locks the design decisions but does not claim the physical setup exists. The package remains
gated despite the completed scoped root checks: production preflight, verified source aliases,
real-artifact restore, and full reproduction evidence remain pending. Recovery of the old drive is
outside the active work. Scoped foundation setup produces only its bounded evidence;
it does not wait for a trained model or completed retrieval/UI. Expensive work requires its own
experiment-readiness checks; all four reproduction recipes are required before G8. See the governing
plan's staged-readiness section. Plan 10 remains `Approved design; gated`, not `Complete` or globally
`Ready`.

## Update rule

Material changes to a physical role, root alias, environment baseline, backup tier, retention rule,
publication protocol, or compute platform require:

1. a decision update;
2. affected risk and requirement updates;
3. migration/compatibility impact;
4. a test or restore consequence;
5. Quinton review before the new rule governs formal runs.
