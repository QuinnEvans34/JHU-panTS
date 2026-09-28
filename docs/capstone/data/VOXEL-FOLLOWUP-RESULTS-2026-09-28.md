# Five-case audit results — September 28, 2026

Status: **bounded audit complete; scientific qualification remains open**.
Plan: VOXEL-FOLLOWUP-PLAN-2026-09-28.md. No original data changed, no exclusion decisions,
production source activation, cohort freeze, training, commit or push.

## Execution and verification

- Runner: scripts/diagnostics/followup_voxel_audit.py (--run); 12 sequential child processes.
- Exact planned five training cases / 17 unique files / 12 CT-mask pairs; no substitutions.
- Output: outputs/prowl/voxel-followup-140effff-129c-4ff8-b455-70a2119707a1/.
- selection.json persisted before voxel reads: input/code hashes, selection reasons, paths,
  stat identities and budgets. Each child rechecked volume and source identities; repeated
  CT hashes agreed. receipt.json records all 17 measured source hashes and report hashes.
- Independently rechecked all 13 receipt-listed artifact hashes (selection + 12 reports).
- Pair times summed to 12.322 seconds, including subprocess startup but excluding preparation.
  Package size 62,379 bytes, below the 20 MiB cap; internal 100 GiB free-space floor passed.
- No timeout, stopped file, source mutation or unsupported-format failure. All grid comparisons
  matched with zero numeric affine/spacing difference; physical units remain a separate issue.
- Every measured CT and mask had zero NaN/+Inf/-Inf. Mask value lists were not truncated.
- 14 new runner tests; full native suite **424 passed**, two upstream torch warnings.

Timeouts are enforced around each child (120 seconds or remaining overall budget, whichever
is smaller). The 900-second budget starts before setup and is checked at child boundaries;
setup filesystem calls are not independently interruptible by this supervisor. This is a
trusted local diagnostic wrapper, not a hardened general-purpose job service or Plan 04 runner.
Working-memory accounting remains an estimate plus overhead, not measured peak process RSS.

## Observations

| Study | Pancreas nonzero voxels | Lesion nonzero voxels | Additional finding |
|---|---:|---:|---|
| PanTS_00000003 | 14,894 | 1,055 | Both measured masks have values 0/1 |
| PanTS_00000026 | 45,095 | 7,244 | Lesion has scaled foreground 1.0000000591389835 |
| PanTS_00000031 | 37,344 | 540 | Same scaled lesion foreground as case 26 |
| PanTS_00000078 | **0** | 0 | Flagged liver mask also empty |
| PanTS_00000266 | 11,193 | 0 | Flagged left-lung mask has 2,280 nonzero voxels; physical units unknown |

All three source-positive tumour candidates contain lesion foreground. Both source-negative
candidates have empty lesion masks. This agreement is descriptive, not clinical validation
or permission to treat the source flag as an adjudicated diagnosis.

### Finding 1: scaled label encoding needs an explicit consumer rule

Cases 26 and 31 lesion files store int8 data, with stored min=-128 and max=127. Their
NIfTI slope is 0.003921568859368563 and intercept is 0.501960813999176. Applying that
header scaling in float64 gives semantic values 0 and 1.0000000591389835. The audit
correctly reports scaled_label_values and fractional foreground rather than rounding.

This looks consistent with a near-binary storage/scaling representation, not evidence of
corrupt labels. A raw-byte interpretation would be wrong, and exact semantic equality to
1 would miss these measured foreground values. This does not assert that the inherited
training code currently has that exact bug; its consumers still require qualification.

Next: propose and test a versioned source-specific decoding policy after provenance/class
mapping review. Retain raw/scaled evidence, require the expected background/foreground
clusters within explicitly justified tolerances, and reject genuinely ambiguous values.
Do not silently round every label or apply a universal >0 rule to every dataset. No decoding
policy, tolerance, annotation record or source rewrite was introduced in this pass.

### Finding 2: an empty pancreas is now an actual observed issue

Case 78's pancreas, lesion and liver masks are empty. All grids match and the payloads
read successfully. Emptiness alone cannot distinguish absent anatomy in the imaged field,
missing annotation, or another source issue. It is NOT proof that the pancreas is absent
biologically or that the CT is corrupt.

The earlier size-only suggestion that pancreatic targets need no exclusions is not supported.
This case requires targeted source/visual review before localizer-target eligibility. Do not
silently use it as a trusted negative pancreas target or remove it from the base split.
No new eligibility was granted; existing source/manifest readiness remains blocked.

### Finding 3: unknown units remain distinct from matching grids

All CT/mask pairs in case 266 match numerically, but CT and masks declare unknown units.
The audit correctly withholds physical volumes, including for the empty lesion mask.
For cases 3/26/31/78, unknown-unit masks qualified for the existing paired-explicit-mm-CT
rule where needed. This does not justify a source-wide millimetre override.

## What this changes next

1. Resolve source annotation provenance/allowed uses and propose the scaled-mask decoding
   contract with synthetic boundary/rejection tests. This is now backed by real foreground.
2. Review case 78's empty pancreas using a bounded source/visual inspection plan; decide its
   eligibility only with evidence. Keep case 266's unknown units unresolved meanwhile.
3. Feed later approved decisions into NEW annotation/manifest artifacts and append-only
   issue resolutions. Preserve these reports and the earlier quarantined manifest unchanged.
4. Continue Plan 02 frozen-cohort publication/consumer implementation under its gates.

No broad scan is scheduled. Two size-flagged cases selected from the retained 50-case sample
cannot characterize all 101 flags or the entire source. These findings sharpen the next
implementation work; they do not close G1 or authorize training.
