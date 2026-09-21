# Preflight, migration, and reproduction protocol

**Status:** Approved Plan 10 design, 2026-09-18; scoped execution prerequisites remain  
**Decisions:** P10-01 through P10-12, P10-17 through P10-19, and P10-24  
**Last reviewed:** 2026-09-18

## Purpose

Turn storage setup and long-run preparation into explicit, testable steps. This is the operational
checklist a future implementation session should follow before touching either drive or launching an
expensive workflow.

## Authorization boundaries

| Action | Allowed during current planning? | Later requirement |
|---|:---:|---|
| Read repository/storage metadata | Yes | Non-mutating only |
| Mount/connect a user-selected drive | User action | Confirm which drive before inspection |
| Read-only device/top-level inventory | After drive is connected | Record evidence; no test folder |
| Scoped capability test on new drive | No, until inventory reviewed | Quinton approves writable test target |
| Create PROWL root directories | No | Approved volume/root design |
| Bulk copy/migration | No | Exact source/destination/bytes and verification plan approved |
| Reformat/partition/encrypt drive | No | Separate destructive decision and verified preservation |
| Delete/move historical content | No | Exact cleanup manifest and explicit Quinton approval |
| Rent compute/upload data | No | D-210 trigger plus cost/license/provider approval |

## Drive setup procedure

### Checkpoint 1 — identify devices

For each available drive assigned an active role, capture without writing. As of September 18,
`PROWL-Data` is available; `JHU-PanTS` is excluded as unavailable and its recovery is optional.
Fresh source acquisition does not require a migration copy from that drive. Capture:

- OS device identifier and physical-store relationship;
- stable volume UUID and user-visible volume name;
- mount point and read-only/read-write state;
- filesystem and encryption state;
- nominal/usable capacity and current free bytes;
- connection type and available health information;
- top-level directory names, sizes, and counts;
- existing checksums/manifests/licenses/source roots;
- unexpected links/mounts or only-copy content.

Update `CURRENT-STORAGE-INVENTORY.md`, then stop for Quinton review.

### Checkpoint 2 — assign roles

Agree on:

- exact 4 TB paths for source, artifact, scratch, and quarantine roles;
- the pinned fresh PanTS source-acquisition destination on `PROWL-Data`;
- a healthy independent target for selected backup copies, excluding the suspect old drive;
- headroom reserve after measured source/PANORAMA/output estimates;
- whether the existing filesystem can be tested as-is.

The encryption choice is settled: Quinton explicitly chose the current unencrypted APFS setup
(D-256). Record that state without changing it. Confirm the independent backup target and bounded
size budget before bulk acquisition; no volume encryption/reformat action is requested.

Role assignment does not authorize format changes or bulk migration.

### Checkpoint 3 — capability test

In a newly scoped temporary directory on the approved new-drive target:

1. create a deterministic control payload and hash;
2. write/read/flush/reopen and compare hash;
3. rename within the volume and verify old path absent/new path correct;
4. append two independently valid JSONL records under the proposed lock;
5. attempt a competing lock/writer and confirm refusal;
6. simulate an incomplete artifact without a completion marker and confirm discovery ignores it;
7. validate long safe IDs, case behavior, permissions, and symlink/realpath boundary;
8. unmount/remount only through a controlled user-approved step if disconnect recovery is tested;
9. remove only the exact temporary test directory after its evidence is captured.

If the test fails, the drive is not approved as the canonical artifact writer until the failure is
understood. No automatic reformat occurs.

### Checkpoint 4 — create roots and controls

- create only approved exact directories;
- create ignored local root registry and committed example/schema;
- generate root/failure-domain IDs;
- test read-only source enforcement and controlled artifact writer;
- publish one tiny control artifact;
- create one backup catalog/restore drill on an independent approved target;
- record actual free capacity after setup.

## Run preflight levels

### Level 0 — read-only inspection

For reports, inventory, or diagnostics:

- resolve required read aliases;
- validate source/artifact records requested for inspection;
- record environment/code identity where result will be retained;
- do not acquire a mutating writer role.

### Level 1 — small synthetic/local operation

Adds:

- destination and temp capability;
- expected derivation/output collision check;
- environment/test gate;
- exact small-space estimate;
- writer lock.

### Level 2 — source-derived or expensive local run

Adds:

- source snapshot and license/access state;
- protected cohort role/access check;
- full space budget/reserve;
- MPS/device lock and expected fallback policy;
- checkpoint/resume path and tested recovery;
- backup/keeper plan;
- long-run power/mount stability warning/requirement;
- formal run class and promotion eligibility.

### Level 3 — publisher-test, stakeholder, or release

Adds:

- clean committed revision and exact environment lock;
- all prerequisite gate/test records;
- frozen candidate/policy/session/release identity;
- no unexpected skip/warning/known-defect disposition;
- release/sensitivity/license/path/secret audit;
- verified Tier A/B backup/restore state;
- prohibition on new result-changing choices.

### Level 4 — remote/rented compute

Adds:

- D-210 trigger evidence and Quinton-approved provider/spend ceiling;
- source terms/privacy/data-upload approval;
- exact encrypted/minimized transfer list and hashes;
- matched local/remote smoke plan;
- remote environment and storage/teardown plan;
- local destination capacity and backup before cloud deletion.

## Machine-readable preflight record

Required fields:

- preflight ID/schema/version/time/status;
- requested run/stage/class and intended output derivation;
- code/environment/config identities;
- root aliases, expected/current volume UUIDs, filesystems, and failure domains;
- source/cohort/parent IDs/hashes/roles/completion state;
- access/read-write/realpath-overlap checks;
- capacity inputs, formula, reserve, available bytes, and pass/fail;
- resource locks and ownership;
- device/network/credential-presence checks;
- required test/gate evidence IDs;
- warnings with explicit policy disposition;
- failure reason and zero-mutation confirmation when blocked.

The human summary is derived from the record. A terminal command transcript alone is insufficient.

## Capacity estimation

Every producing component supplies or measures:

- expected final member count/bytes;
- worst-case uncompressed/intermediate bytes;
- simultaneous temporary/copy/checkpoint bytes;
- retry/resume duplication allowance;
- log/test/trace allowance;
- operational headroom.

For case-scaled work, estimate from a representative sample using a conservative high percentile or
maximum rather than only the mean. Record compression behavior. If the projection is uncertain, run
a smaller smoke cohort and update the estimate before proceeding.

No preflight deletes files to make itself pass.

## Migration protocol

### Migration record

Each migration names:

- old root/path/failure domain and classification;
- new root/path/failure domain and intended status;
- source controlling record or generated inventory ID;
- copy tool/version/options;
- expected members/bytes/hashes;
- actual members/bytes/hashes and errors;
- representative consumer/load checks;
- source retention hold and backup state;
- whether the artifact remains historical or has a separately validated capstone import;
- approval and completion timestamps.

### Historical output triage

Classify in this order:

1. known source/control records and license evidence;
2. named decision-relevant/keeper checkpoints with run identity;
3. controlled/negative experiment evidence;
4. final prediction/evaluation/report inputs;
5. rebuildable caches;
6. exploratory/unidentified payloads;
7. obvious partials only after proving they are not descendants/keepers.

Unknown content is retained. File age and size may prioritize review but cannot decide deletion.

### Copy verification

- freeze source inventory before copy;
- copy, never move;
- compare file count and total bytes;
- verify every declared member hash;
- validate JSON/schema/checksum records;
- load representative NIfTI/checkpoint/index/case package;
- verify no absolute-path assumptions were introduced;
- publish migration record;
- retain original until the specified hold and restore condition pass.

## Reproduction protocols

### When these recipes are required

Foundation setup uses small generated control artifacts and a synthetic review-event snapshot for
its initial restore drill; it does not require a working UI, retrieval index, or trained model.
Before an expensive experiment, pass the relevant branch's bounded smoke/reproduction checks and
its Plan 05/06/09 prerequisites, and record its game plan in `docs/experiments.md`. Early imaging
work does not require R2 or R3. All four completed recipes and actual release-critical restore checks
are required before G8. The Plan 04 explanation/authorization gate is unchanged.

### Recipe R1 — tiny imaging branch

Inputs:

- committed generated NIfTI/label fixture or approved tiny local control;
- exact manifest/cohort/control model fixture;
- locked environment and resolved configuration.

Actions:

1. resolve roots/preflight;
2. build/validate manifest and protected cohort;
3. preprocess through the shared transform;
4. run tiny model/training-or-inference smoke;
5. restore source-space prediction;
6. compute golden metrics;
7. package one UI case.

Pass:

- deterministic control IDs/hashes/counts match;
- geometry/labels/lineage pass;
- numerical values meet declared exact/tolerance policy;
- output is published only after validation.

### Recipe R2 — retrieval branch

Inputs:

- small permitted frozen corpus with rights records;
- fixed development questions/relevance goldens;
- approved index candidate/config/environment.

Actions:

1. normalize works/representations/passages;
2. build lexical and vector candidate;
3. close/reopen persistent index;
4. issue fixed structured queries;
5. produce ranked records and recall/MRR;
6. produce supported extract/refusal fixtures.

Pass:

- work/passage/index identities and counts reconcile;
- passage locators resolve;
- metric goldens and claim/citation/refusal checks pass;
- no restricted text enters Git/release.

### Recipe R3 — review branch

Inputs:

- validated synthetic representative case package;
- local writer and empty controlled event log.

Actions:

1. load static and FastAPI transports into the same view model;
2. inspect prediction/evidence states;
3. submit each valid action/reason combination across fixtures;
4. verify durable receipt/read-back;
5. append revision and derive current state;
6. reload UI/history.

Pass:

- exact package/prediction/evidence/review identities match;
- transport parity holds;
- failed append never displays saved;
- event history remains immutable and ordered.

### Recipe R4 — release audit

Inputs:

- frozen clean release candidate and release manifest.

Actions:

1. verify Git revision, environments, tests, defects, and gate evidence;
2. validate every artifact/checksum/reference/license/sensitivity field;
3. scan for raw imaging, restricted article text, secrets, absolute paths, unsupported claims, and
   unapproved dependencies;
4. reconstruct permitted package in an empty destination;
5. start/run the bounded demo and documentation walkthrough;
6. compare final checksums.

Pass:

- all included files are declared/permitted/verified;
- no prohibited material is present;
- demo/user/developer path works from documented prerequisites;
- final manifest reproduces exactly.

## Failure and resume discipline

When a preflight or run fails:

1. stop mutation and retain original error output;
2. record terminal attempt state and actual written paths/bytes;
3. do not write a completion marker;
4. quarantine/validate partials;
5. identify last valid parent/stage;
6. fix through a new code/config/environment identity when material;
7. resume only if the component's resume contract proves compatibility;
8. otherwise create a new attempt and reuse only independently valid parents;
9. add a regression/failure-injection test for high-impact defects.

The orchestrator may coordinate this sequence but never overrides artifact validation.
