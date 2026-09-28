# Bounded positive-case and size-flag follow-up

Execution follow-up: the exact selection completed; see
[VOXEL-FOLLOWUP-RESULTS-2026-09-28.md](VOXEL-FOLLOWUP-RESULTS-2026-09-28.md).
Scaled lesion foreground and an empty pancreas were found; no eligibility promotion.
The prepared/not-started wording below preserves the pre-run plan.

Status: selection and budget prepared; **voxel execution not started**.
Owner: Codex. Diagnostic work under Plan 02, not a CAP-EXP training experiment.

## Questions

1. What foreground values, occupancy and geometry do source-positive lesion cases have?
2. Are pancreas/lesion files readable and paired on the selected size-flagged studies?
3. What do the actual flagged liver/lung masks contain? Empty, small, or unusual content
   does not by itself prove corruption, field of view, annotation accuracy or eligibility.

## Deterministic selection and provenance

Use the exact approved training membership through accepted_pants_members, never merely
the publisher's 1–9000 range. Sort canonical IDs lexically. Select the first three whose
pinned metadata source_tumor_status is positive. Then select the first two distinct training
IDs in the retained structure-specific anomaly sample, excluding the first selection.
No replacement based on voxel results. Stop and document a changed input or missing member.

Inputs checked on September 28:

- Training membership SHA-256:
  `bfc827ac52346e4636ed3a58581d5f55a9f1e80983bbfd6228c928babd519fc8`.
- Pinned metadata.xlsx SHA-256:
  `4bcbf14a31b1ca9441af051a104702e7a832391f47d3af5f493048ec813283e3`.
- Inventory: outputs/prowl/inventory-2026-09-27/full-v4.json, SHA-256
  `b8f561d2fdf7506673f6e29da75c6c879b96dae0ba7cb88add9f1649caca25e5`.

The inventory reports 101 structure-specific flags but retains details for only 50.
This selection is from that retained sample, not all 101 and not a representative sample.
Its compressed-size interpretations are provisional; only recorded flags are reused.

| Study | Selection reason | Metadata row | CT bytes | Pancreas bytes | Lesion bytes | Additional flagged mask |
|---|---|---:|---:|---:|---:|---|
| PanTS_00000003 | Source tumour flag positive | 4 | 6,829,413 | 33,214 | 30,594 | None |
| PanTS_00000026 | Source tumour flag positive | 27 | 16,396,154 | 72,389 | 67,458 | None |
| PanTS_00000031 | Source tumour flag positive | 32 | 9,679,636 | 45,682 | 39,052 | None |
| PanTS_00000078 | Retained structure-size flag; source tumour flag negative | 79 | 5,842,835 | 22,384 | 22,390 | liver.nii.gz: 22,390 bytes |
| PanTS_00000266 | Retained structure-size flag; source tumour flag negative | 267 | 5,251,708 | 22,295 | 18,185 | lung_left.nii.gz: 19,320 bytes |

These are observed compressed sizes, not checksums or voxel-quality findings. Source flags
select candidates; they are not verified diagnoses or reference-negative eligibility.

## Exact file scope

Diagnostic extraction root from the registered acquisition parent:
`extraction-3b1cd6110811-20260922/`. Resolve against the verified registered volume;
do not activate production aliases or fall back to another drive.

For EACH of the five explicit IDs above, read only:

- PanTSMini_ImageTr_00000001_00001000/{ID}/ct.nii.gz
- PanTSMini_Label/{ID}/segmentations/pancreas.nii.gz
- PanTSMini_Label/{ID}/segmentations/pancreatic_lesion.nii.gz

Additionally read only:

- PanTSMini_Label/PanTS_00000078/segmentations/liver.nii.gz
- PanTSMini_Label/PanTS_00000266/segmentations/lung_left.nii.gz

Total: **17 unique files, 12 explicit CT/mask pairs**. The two nonpancreatic masks are
diagnostic probes only, not new training targets or scope expansion. No combined labels,
additional structures, validation/test cases, PANORAMA or recursive file discovery.

## Resource and failure budget

- Sequential execution; one reader workload, no parallel training or heavy disk scan.
- Existing audit v1.1 default 256 MiB estimated working buffers plus overhead; not a hard
  process RSS guarantee. Retain max_axis=4096 and max_voxels=1,000,000,000 checks.
- Proposed operational ceiling: 120 seconds per pair and 15 minutes overall, enforced
  by a supervising runner/subprocess timeout (not currently implemented in the pilot runner).
  Do not pretend the existing audit kernel implements wall-time limits.
- Cap serialized output at 20 MiB total and require at least 100 GiB free internally;
  use a NEW ignored outputs/prowl directory, not raw-data copies or overwrites.
- Compressed inputs total under 50 MB uniquely. CT is reread across pairs and hashing plus
  decompression adds I/O; this is not a total byte-read or expanded-memory estimate.
- Estimated completion: a few minutes based on the earlier pilot, not a guaranteed runtime.
  Check headers/declared dimensions first; stop rather than enlarge limits automatically.
- On unavailable/mismatched volume, changed selection/input hash, source mutation, corrupt
  payload, timeout or unsupported format: preserve completed reports and stopped status,
  stop remaining work, and withhold a successful completion receipt.
- Unknown units, a measured incompatible grid, empty masks or unusual values are findings
  to retain, not reasons to silently repair, exclude, substitute cases or increase scope.

## Execution prerequisites and output

Before running, implement/review a bounded follow-up runner rather than changing the
two-case pilot's hard-coded boundary. Add synthetic tests for exact selection/counts,
train-role rejection, absent metadata, duplicate IDs, timeout and no-overwrite behavior.
Validate the 17 paths against the explicit source-layout rules; do not trust arbitrary
paths embedded in the old inventory. Pin runner/audit/input hashes in the new package.

Recheck the full native suite after code changes. Record a selection.json before voxel
reads, with reasons, input digests, explicit relative paths, limits and budget. During the
run, use mounted() UUID/device guards and measure full file hashes. Store every pair's
report, elapsed time, stop information and comparisons with expected preflight identity.

Use expected_values=None so actual value sets are observed without a guessed binary rule.
Keep original headers and inference provenance distinct. Report grid compatibility, raw
and scaled value bases, exact nonzero/nonfinite counts, truncation flags and physical
volume availability/reasons. Final receipt hashes reports and marks only actual completion.

## Interpretation after the run

Review each case explicitly, including disagreement between metadata and observed lesion
occupancy. Foreground value 1 in selected masks would support that observed encoding only;
it would not establish annotation authorship, clinical truth or the full release mapping.
Negative source flags and empty masks are distinct pieces of evidence, not interchangeable.

Do not approve a global mm override from plausible numeric spacing. Do not call the flagged
liver/lung files defective without content/geometry evidence. Do not generalize two anomaly
cases to 101. Publish any later eligibility or issue resolution separately with evidence.

Exit: bounded evidence and explicit remaining questions, not G1 closure or training permission.
After that, prioritize annotation provenance/unit decisions and the frozen cohort consumer.
