# Voxel Audit Design (voxel-audit-v1)

## Codex v1.1 follow-up

Ownership transferred by Quinton after review. Native tests now pass (77 focused,
410 full suite); the two-case pilot completed. See VOXEL-AUDIT-CODEX-REVIEW-2026-09-28.md
and VOXEL-PILOT-2026-09-28.md. The synthetic-only status below is historical.
Paired results now wait for BOTH finalizers, CT-derived units are withheld on CT failure,
and ambiguous geometry withholds physical volume. The demo canonicalizes its temporary
root without relaxing shared path guards. Existing format/memory/full-scale limits remain.

Status: implemented on synthetic fixtures only, pending Codex review. Not run on real data.
Packet: `docs/capstone/operations/CLAUDE-VOXEL-AUDIT-HANDOFF-2026-09-28.md`.
Code: `scripts/diagnostics/audit_voxels.py`. Tests: `tests/test_voxel_audit.py`.

## Purpose and boundary

The source-evidence adapter (`src/data/source_evidence.py`) proves which bytes a file holds
and what its header declares. It does not open voxel payloads. This audit answers what only
the payload can answer:

- how many voxels are finite, NaN, +Inf or -Inf;
- what values a mask stores, whether it is empty, and how many voxels fall outside a
  caller-supplied set of expected values;
- whether a CT/mask pair shares one voxel grid, and, only if it does, descriptive CT values
  inside the mask.

It is measurement, not eligibility. It makes no exclusion, label mapping, lesion-status
inference, split decision, threshold verdict or diagnosis. Every record carries
`eligibility: "not_assessed"`. Whether a finding matters for a cohort is decided downstream by
Codex's manifest and cohort tooling and by Quinton.

## Interface

```python
audit_volume(roots, alias, uri, *, role, expected_values=None, limits=Limits(), check_root=...)
audit_pair(roots, *, ct=(alias, uri), mask=(alias, uri), expected_values=None,
           study_ids=None, limits=Limits(), check_root=...)
```

- Inputs are explicit `(root alias, relative URI)` pairs, resolved by the adapter's
  `resolve_file` (approved alias, canonical root, no symlinks, regular file). There is no
  discovery, recursion or default root. The CLI runs only `--demo`, which builds a synthetic
  pair in a temporary directory; any other argument exits 2.
- `role` is `"ct"` or `"mask"`. `expected_values` is mask-only caller policy. There is no
  default label set. Passing it for a CT raises `ValueError`, because intensities are not
  label classes.
- `study_ids=(mask_study_id, ct_study_id)` must come from a validated source join. It is used
  for one thing: invoking the adapter's approved `infer_mask_mm` (`paired-explicit-mm-ct-v1`)
  unchanged, so an unknown-unit mask can report a volume. Filenames are never used to guess it.
- `check_root` is the caller's mount/UUID check. It runs before hashing, after the header
  read, and again after the payload is read.
- Records are strict JSON (`allow_nan=False` passes). They contain the alias and relative URI,
  never an absolute path. Stopped and measured records share one key set; measurements are
  `null` until complete.

## How a file is read

1. **Evidence.** `measure_nifti` hashes the exact bytes and reads the header. The audit pins
   the file identity `(st_dev, st_ino, st_size, st_mtime_ns, st_ctime_ns)` around that call.
2. **Header parse (independent).** The audit opens the file itself with
   `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, checks that `fstat` matches the pinned identity, and
   parses the 348-byte header with `Nifti1Header.from_fileobj(check=False)`. It accepts only
   single-file NIfTI-1 (`n+1`), exactly 3 dimensions, and real integer or float types up to
   64 bits. It rejects 4D, including `(x, y, z, 1)`, plus complex, RGB, bool and float16 types,
   and a non-integral `vox_offset` or one below 352.
3. **Limits before any payload read.** Declared axis length, voxel count and working budget
   are checked against `Limits` before a single payload byte is read. A header that declares
   4096^3 voxels over a 400-byte file stops as `limit_exceeded`. An uncompressed file shorter
   than `vox_offset + voxels * itemsize` stops as `payload_truncated`, also before reading.
4. **Streaming.** The payload is read in fixed chunks into one reused buffer (`readinto`,
   `np.frombuffer`) from the same descriptor that matched the hashed identity. nibabel's
   `ArrayProxy`, `get_fdata()` and full-volume `np.asarray(proxy)` are never used. The tests
   replace those methods with ones that raise an error, then check that a full paired audit
   still succeeds.
5. **Finish.** A gzip stream is drained to EOF in 1 MiB reads, so Python's gzip verifies the
   CRC32 and ISIZE trailer. Trailing bytes are capped at 16 MiB. Then `fstat` of the open
   descriptor and `lstat` of the path must both still match the pinned identity, and
   `check_root` must pass. Otherwise the result is `file_mutated` or `root_check_failed`.

The chunks are voxel slabs in on-disk (Fortran) order. For gzip, reaching a slab means
decompressing everything before it. The audit reads each file front to back exactly once, so
that cost is paid once. It does not do random-access slicing.

## Values

- **Scaling.** Scaling is stated independently of nibabel, and more strictly. A `scl_slope`
  of 0 or NaN means unscaled, matching the NIfTI-1 standard and nibabel. A finite nonzero
  slope with a finite intercept scales. Any other combination stops as `invalid_scaling`.
  nibabel silently treats an infinite slope as unscaled, which would misreport every value in
  the file. For a NaN or Inf intercept with a valid slope, nibabel raises inside
  `measure_nifti`, and the audit records `evidence_refused`.
- **Promotion.** Scaled values are computed in float64 explicitly. Nothing is cast to an
  integer type. For 64-bit integers above 2^53 with active scaling, the record sets
  `float64_precision_loss_risk`.
- **Exhaustive accounting.** `finite + nan + posinf + neginf == count` is asserted for every
  file. Non-finite values are counted in their own fields and never silently dropped from a
  denominator. `scaled_overflow_voxels` counts finite stored values that became non-finite
  after scaling.
- **Stored and semantic ranges** are both reported (`stored_min/max`, `min/max`), along with
  `values_basis` (`stored` or `scaled`).

## Masks

- `nonzero_voxels`, `negative_voxels` and `nonintegral_voxels` are counted over finite
  semantic values. `empty` is `true` or `false` only when the mask has no non-finite values;
  otherwise it is `null`, because occupancy is ambiguous.
- `value_counts` lists at most `max_distinct` (default 1024) values. Each listed value's
  count is exact. Totals such as nonzero and unexpected counts never depend on the cap. If
  the cap is hit, `distinct_values_truncated` is set. Which values get listed then depends on
  chunk order, so truncated listings are not chunk-size invariant. Untruncated ones are.
- With `expected_values`, `unexpected_value_voxels` is exact. `unexpected_values` lists at
  most `max_listed` values, and `unexpected_values_truncated` is set when there are more.
  The comparison is exact equality in float64, with no tolerance and no rounding.
- A scaled mask is measured on its scaled values, with a `scaled_label_values` warning.
- **Volume** is `nonzero * |det(affine[:3, :3])|`, in mm³. The basis is `header_mm` (from the
  adapter's millimetre geometry) or `inferred_mm:paired-explicit-mm-ct-v1`. When no geometry
  exists (unknown units with no validated pairing, or invalid geometry), the volume is
  unavailable and a coded reason is given, while the voxel count stays available. Non-finite
  mask values also make the volume unavailable.

## Pair grid comparison

- If both files have adapter mm geometry, shape, spacing and the RAS affine are compared in
  mm. Otherwise the native header values are compared: this is the same test `infer_mask_mm`
  applies. The tolerance is absolute: `1e-5` (`PAIR_ATOL`, identical to `infer_mask_mm`).
  So the audit can never call a grid shared when the approved unit rule would refuse the
  pairing.
- Blocking issues are `shape_mismatch`, `affine_mismatch`, `spacing_mismatch`, and
  `{ct,mask}_<code>` for `qform_sform_disagreement`, `invalid_geometry`,
  `unsupported_image_dimensions`, `uncoded_spatial_transform` or `affine_spacing_disagreement`.
  An uncoded file (qform_code = sform_code = 0) uses nibabel's zoom fallback affine, which is
  not a statement of where the voxels are, so it blocks.
- **Interface gap covered here, not in shared code.** For unknown units, `header_geometry`
  returns before any qform/sform check. For those files only, the audit applies
  `infer_mask_mm`'s own coded-transform test (`rtol=0`, `atol=1e-4` native). Files with known
  units keep the adapter's verdict unchanged, which uses `rtol=1e-5` and `atol=1e-4/scale`.
- The audit never resamples, reorients, reshapes or flips anything. Within-mask CT values are
  computed only when the grid is verified as shared. Both files are then read in lockstep, and
  the report gives the count, finite and non-finite counts, min, max, and a mean (a
  `math.fsum` of per-chunk float64 sums). These are descriptive only.
- If either paired file stops during lockstep reading, its partner stops with
  `aborted_with_pair`, and no within-mask values are reported. When the grid is not shared,
  each file is still measured independently.

## Memory bound

Chunk size in voxels: `chunk = working_bytes // per_voxel`, where

```
per_voxel = Σ_files (itemsize + role_cost) + (16 if paired else 0)
role_cost = 32 for CT, 64 for mask
```

Peak traced memory is about `chunk * per_voxel`, plus fixed overhead. The fixed overhead is
the adapter's 1 MiB hashing reads, the 1 MiB gzip drain reads, zlib state and nibabel header
objects.

The role costs were measured with `tracemalloc` on adversarial synthetic inputs (float64,
scaled, every value distinct, with and without NaN/Inf), then rounded up. Observed peaks
never exceeded 0.69 of the working budget, plus at most about 2 MiB of fixed overhead. The test suite
re-measures one adversarial paired case and asserts `peak <= working_bytes + 2 MiB`.
`tracemalloc` does not see zlib's C allocations, which are small and constant per stream.

At the default 256 MiB budget, an int16 CT paired with a uint8 mask gets about 2.3 M voxels
per chunk. A 512×512×300 CT therefore takes about 34 chunks per file. This is an estimate
from the formula. No real-data runtime has been measured.

## Coded stops

| code | meaning |
|---|---|
| `evidence_refused` | adapter refused the file (alias, symlink, mutation, nibabel header error) |
| `unavailable_prerequisite` | OS error reaching the file (strerror only, no path) |
| `unsupported_format` / `malformed_header` | not single-file NIfTI-1 / impossible header fields |
| `unsupported_dimensions` / `unsupported_datatype` | not exactly 3D / not real int or float ≤ 64-bit |
| `invalid_scaling` | non-finite slope or intercept with a nonzero slope |
| `limit_exceeded` | declared shape or budget over `Limits`, checked before payload reads |
| `payload_truncated` / `corrupt_payload` | short payload / gzip or zlib damage, including CRC |
| `excess_trailing_payload` | more than 16 MiB after the declared payload |
| `file_mutated` / `root_check_failed` | identity changed / caller root check raised (any exception) after reading |
| `aborted_with_pair` | paired file stopped during lockstep reading |

A stop is preserved in the record, not raised. Caller misuse raises `ValueError`: a wrong
role, expected values for a CT, or non-finite expected values.

## Known limits

- NIfTI-1 single-file only. NIfTI-2, `.hdr/.img` pairs and 4D series stop.
- The mm-to-mm pair tolerance (1e-5 absolute) is inherited from `infer_mask_mm`. Real pairs
  written by different tools can differ by float32 round-off at large translations and be
  reported as `affine_mismatch`. The record includes the measured maximum difference, so
  Codex and Quinton can decide on a policy. The audit does not loosen the tolerance itself.
- The identity check detects changes to metadata and inode. Like the adapter, it cannot
  defend against a hostile writer that preserves size, mtime and ctime.
- Truncated distinct-value listings depend on chunk order (see Masks).
- For very small gzip files, damage near the start makes nibabel's header read fail first,
  which gives `evidence_refused` rather than `corrupt_payload`. Both are coded stops.
- No runtime or throughput claims are made. Nothing here has touched the external drive.
