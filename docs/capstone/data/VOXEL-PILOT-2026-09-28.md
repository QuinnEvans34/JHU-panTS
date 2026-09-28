# Two-case voxel pilot — September 28, 2026

Status: completed after Codex fixes and native review. Diagnostic measurements only.
No eligibility decisions, source edits, resampling, frozen cohort or training occurred.

## Scope and evidence

New ignored package: `outputs/prowl/voxel-pilot-3b89b0d7-6bd3-4649-83f8-db075b036595/`.
Four reports plus receipt.json (report hashes, code hash, version, timing, prior package).
Runner: scripts/diagnostics/pilot_voxel_audit.py, explicit --package argument.

Inputs were the prior manifest slice's two training cases, whose exact approved training
membership and metadata joins were rechecked. Mount UUID/filesystem/device were checked
around reads. Every report's file hash matched the earlier evidence. The original diagnostic
manifest package was not overwritten. No recursive discovery or test cases were read.

Expected-value policy was deliberately omitted: the audit measured values, not assumed
binary semantics. Limits used the default 256 MiB working budget plus overhead; process
peak RSS was not measured. Total reported pair time was about 8.4 seconds including repeated
CT reads and checks. These small, cached cases do not forecast full-dataset runtime.

| Case | Mask | Nonzero voxels | Observed values | Physical volume |
|---|---|---:|---|---|
| PanTS_00000001 | pancreas | 182,215 | 0, 1 | 56,942.188 mm³, approved paired-CT inferred units |
| PanTS_00000001 | lesion | 0 | 0 | 0 mm³, explicit header units |
| PanTS_00000002 | pancreas | 25,386 | 0, 1 | Unavailable: unknown units |
| PanTS_00000002 | lesion | 0 | 0 | Unavailable: unknown units |

All four grids matched numerically with zero affine/spacing differences under the retained
strict tolerance. Unknown-unit pairs match on a native grid, not proven physical millimetres.
All four masks had zero NaN/Inf, negative or fractional voxels. Value listings were not
truncated. All reports completed; no stopped file or source hash change was observed.

## Meaning and next gate

The two lesion masks are empty. That is a voxel observation, not proof of a negative clinical
diagnosis, label quality, or a general lesion-label encoding (there were no positive lesion
voxels in this sample). Do not infer unseen foreground encoding from all-zero masks.

Case 1 exercises approved mask-unit inference successfully; case 2 correctly keeps physical
volume unavailable. The unresolved all-unknown-unit question has not been repaired or waived.
Annotations and source-specific provenance/allowed uses still need qualification. The prior
manifest's open issue records remain unchanged; later resolutions need new linked artifacts.

Next: choose a bounded training-only follow-up containing positive source tumour flags and
reviewed anomaly candidates, with an explicit resource budget; settle annotation provenance
and unit policy before any eligibility decision. Do not jump from four pairs to a full scan.
The first-experiment readiness checklist remains independent work that can proceed now.
