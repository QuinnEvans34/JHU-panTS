# Voxel Audit — Claude Handoff for Codex Review (2026-09-28)

Packet: `docs/capstone/operations/CLAUDE-VOXEL-AUDIT-HANDOFF-2026-09-28.md`. One bounded pass.
Nothing was run against real data, the external drive or a registered root. No commit, stage,
stash or branch operation was performed.

## Files (the packet's four-file allowlist, all new)

| file | sha256 |
|---|---|
| `scripts/diagnostics/audit_voxels.py` | `b505266b8d01e158916a381f64d72cdd04b8bea6f1ce19f24e7857eee20a5bfd` |
| `tests/test_voxel_audit.py` | `954a02ff9534816170b566ba9d0e7eebeeabc4464f2ca2ac46c184d231ca8f3e` |
| `docs/capstone/data/VOXEL-AUDIT-DESIGN.md` | `1d29573b9db02228e87d8128fcc7a610af785a1c7383f8704fc91ba0772bf695` |
| `docs/capstone/data/VOXEL-AUDIT-CLAUDE-HANDOFF.md` | this file (hash reported in the chat handback) |

Before and after writing, the interface files matched the packet's hashes:
`src/data/source_evidence.py` `54fe5b2c…`, `src/data/protected_identity.py` `833dc2dc…` and
`src/data/manifest_records.py` `090dabfc…`. Only `source_evidence` is imported, read-only.
No edits were made to `src/data`, schemas, shared docs, AGENTS/CLAUDE, existing tests,
dependencies, locks or pytest config. No binary fixtures were added; every NIfTI is written
under pytest's `tmp_path` at runtime.

## Environment: not native

The tests ran in a **Linux container**, not the Mac `.venv-prowl`. It used Python 3.12.3 with
the exact project pins: nibabel 5.4.2, numpy 2.5.1, jsonschema 4.26.0, pytest 9.1.1 and
PyYAML 6.0.3. The repo's `src/data` and `tests/test_source_evidence.py` were mirrored in
byte-identical form (hashes verified), along with `pytest.ini`. Native verification is
**not claimed**. The container venv also has `pyflakes`, used only for lint. It is not a
project dependency.

## Test evidence (container)

```
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_voxel_audit.py -q -p no:cacheprovider
62 passed in ~1.1s                      (repeated 3 times, stable)
python -m pytest tests -q -p no:cacheprovider      (mirror: voxel audit + source evidence only)
81 passed
pyflakes scripts/diagnostics/audit_voxels.py tests/test_voxel_audit.py   -> clean
python -m scripts.diagnostics.audit_voxels --demo                       -> both files measured
```

**Mutation check.** Fifteen deliberate bugs were injected into the kernel one at a time, and
the suite was run after each. All 15 were caught:

- a looser pair tolerance
- dropped NaN counting
- no identity re-check
- no gzip drain (CRC)
- ignoring the chunk budget
- a signed determinant
- the native qform/sform check turned off
- `empty` ignoring non-finite values
- limits checked after reading
- no pre-read truncation check
- trailing bytes ignored
- the scaled-mask warning dropped
- within-mask non-finite values dropped
- the unexpected count dropped
- the final `check_root` skipped

The mutation check itself found one real defect, which is now fixed. Compression was being
inferred from stream identity, and a wrapped stream made an uncompressed file skip its
pre-read truncation check.

**Not run here (Codex, please):** the two native commands in the packet, including the full
309-test baseline. There was no timing on real volumes and no Apple-specific file-system
behaviour (APFS, `O_NOFOLLOW` semantics on macOS, external-volume ctime).

## Acceptance matrix → tests

| # | requirement | tests |
|---|---|---|
| 1 | empty mask; exact count | `test_empty_mask_is_empty_with_zero_volume`, `test_nonempty_mask_exact_count` |
| 2 | anisotropic mm volume | `test_anisotropic_volume_is_hand_computed` (mm/meter/micron), `test_flipped_axis_volume_uses_absolute_determinant` |
| 3 | unknown units | `test_unknown_units_count_available_volume_unavailable`, `test_unknown_unit_mask_uses_approved_paired_rule_only_with_study_ids`, `test_unknown_units_with_only_sform_coded_is_comparable` |
| 4 | shifted/flipped affine; shapes; qform/sform | `test_same_shape_different_affine_blocks_voxel_pairing`, `test_different_shapes_block_voxel_pairing`, `test_pair_tolerance_boundary`, `test_qform_sform_disagreement_blocks_pairing` (mm + unknown), `test_uncoded_transforms_block_pairing`, `test_within_mask_ct_values_hand_computed` |
| 5 | labels, unexpected, fractional, negative | `test_multiple_allowed_labels_plus_unexpected_value`, `test_fractional_and_negative_labels_are_counted_not_rounded`, `test_expected_values_are_caller_policy_not_default`, `test_distinct_value_cap_truncates_listing_but_not_counts` |
| 6 | NaN/Inf explicit | `test_nonfinite_mask_values_are_counted_and_block_emptiness`, `test_nonfinite_ct_values_inside_mask_are_reported_not_dropped`, `test_scaling_overflow_is_reported` |
| 7 | slope/intercept; gz and plain | `test_slope_intercept_applied_in_float64`, `test_zero_or_nan_slope_means_unscaled`, `test_infinite_slope_stops_instead_of_silently_unscaled`, `test_nonfinite_intercept_is_refused`, `test_scaled_mask_is_measured_on_scaled_values_with_warning`, `test_compressed_and_uncompressed_measure_identically` (both byte orders), `test_int64_precision_risk_flagged_when_scaled` |
| 8 | truncated/corrupt, 4D, oversized, distinct cap | `test_truncated_uncompressed_payload_stops_before_reading`, `test_truncated_gzip_payload_stops`, `test_gzip_damaged_inside_header_region_is_refused_by_adapter`, `test_gzip_crc_corruption_is_detected_after_payload`, `test_trailing_bytes_are_counted_as_warning`, `test_non_3d_input_stops` (4D and (x,y,z,1)), `test_complex_datatype_stops`, `test_declared_oversized_shape_stops_before_any_payload_read`, `test_declared_huge_shape_with_tiny_file_stops_on_limits`, `test_paired_stop_aborts_partner_and_withholds_within_mask`, `test_unapproved_alias_and_symlink_are_refused`, plus the #5 cap test |
| 9 | no full-array conversion; slab bounds | `test_no_proxy_or_full_array_access` (ArrayProxy `__array__`/`__getitem__`/`get_unscaled`/`_get_scaled`/`_get_unscaled`, `get_fdata`, `data_from_fileobj` all raise), `test_payload_reads_are_bounded_by_the_chunk`, `test_chunk_size_does_not_change_measurements`, `test_traced_memory_stays_within_working_budget`, `test_working_budget_below_one_voxel_stops` |
| 10 | inputs unchanged, deterministic, mutation, headers | `test_inputs_unchanged_and_output_deterministic`, `test_file_modified_during_read_is_rejected`, `test_file_replaced_during_read_is_rejected`, `test_root_check_failure_after_read_is_a_coded_stop` (OSError/RuntimeError/ValueError) |
| — | output contract | `test_output_is_strict_json_without_paths_or_eligibility_claims`, `test_stopped_and_measured_records_share_one_key_set`, `test_cli_runs_only_the_fixture_demo` |

Expected values come from the fixture arrays themselves, not from audit output. Fixtures are
written byte by byte: a 348-byte header, a 4-byte extension flag, then the Fortran-order
payload. Spacings are exact in float32 (0.75, 0.875, 2.5 mm; voxel volume 1.640625 mm³).

## Design choices and tolerances

Full detail is in `VOXEL-AUDIT-DESIGN.md`. The points most worth review:

1. **Not using nibabel for voxels.** The audit reads the payload itself, streamed from the
   descriptor whose identity matches the hash. This makes slab bounds and mutation checks
   provable. The cost is a small independent reader, restricted to NIfTI-1 3D real types.
2. **Scaling stricter than nibabel.** An infinite slope stops the file (nibabel silently
   ignores it). A non-finite intercept is refused (nibabel raises inside the adapter).
3. **Pair tolerance equals `infer_mask_mm`'s (1e-5 absolute).** The native qform/sform check
   for unknown-unit files equals `infer_mask_mm`'s (`rtol=0`, `atol=1e-4`). Known-unit files
   keep the adapter's verdict. The audit can never call a pairing shared when the approved
   rule would refuse it.
4. **Uncoded transforms block pairing.** A zoom fallback affine is not a spatial statement.
5. **No default label policy.** `expected_values` comes only from the caller. Comparison is
   exact float64 equality.
6. **Non-finite mask values make `empty` and volume `null`**, with a coded reason, instead
   of guessing occupancy.
7. **Stops are preserved as records, not raised.** Only caller misuse raises `ValueError`.

## Memory formula

```
chunk_voxels = working_bytes // (Σ_files (itemsize + {CT: 32, mask: 64}) + (16 if paired))
peak ≈ chunk_voxels × that denominator + ~2 MiB fixed (adapter 1 MiB hash reads, gzip drain, headers)
```

Measured with tracemalloc on adversarial float64 inputs (scaled, all values distinct, with and
without NaN/Inf), peaks never exceeded 0.69 of the budget. At the default 256 MiB budget, an
int16 CT paired with a uint8 mask uses about 2.33 M voxels per chunk. This is an estimate, not
a measured runtime.

## Known limits

- NIfTI-1 single-file only. No NIfTI-2, `.hdr/.img` or 4D.
- mm-to-mm pairs from different writers may differ by float32 round-off beyond 1e-5 at large
  translations. They are reported as `affine_mismatch` together with the measured difference.
  A tolerance policy is a decision for Codex and Quinton, not something the audit sets.
- Truncated distinct-value listings depend on chunk order. Counts and totals do not.
- Identity checks cannot defeat a hostile writer that preserves size, mtime and ctime. This
  matches the adapter's documented boundary.

## Interface gaps (proposed; shared code not edited)

1. `header_geometry` returns before any qform/sform check when units are unknown. The audit
   covers this locally, using `infer_mask_mm`'s own test. Codex may want the adapter to emit
   `qform_sform_disagreement` for unknown-unit files too, so that manifest evidence carries it.
2. `measure_nifti` lets nibabel exceptions (`ImageFileError`, `HeaderDataError`) and
   `EOFError` escape uncoded. The audit maps them to `evidence_refused` or `corrupt_payload`.
   An adapter-level mapping would give every consumer the same codes.
3. A shared `check_root` factory for the PROWL-Data volume (mount, UUID, `st_dev`) would stop
   each caller from building its own. `scripts/acquisition/download_pants.py:mounted` already
   has the logic.

## Proposed training-only pilot (not executed; Codex selects and runs after review)

These cases are training-range IDs only, well below the publisher test range
`PanTS_00009001`–`PanTS_00009901`:

- `PanTS_00000001`: explicit-mm CT and lesion, unknown-unit pancreas. This exercises the
  paired unit rule.
- `PanTS_00000002`: all unknown units, qform_code 0 and sform_code 2. This exercises the
  native grid path.
- One or two cases that the layout inventory flagged, chosen by Codex.

Roots are placeholders. Take them from the extraction record, and do not guess them.

```python
# In the native .venv-prowl, from the repo root, after review. Placeholders in <>.
from pathlib import Path
import json
from scripts.acquisition.download_pants import mounted
from scripts.diagnostics.audit_voxels import audit_pair

mount = Path('/Volumes/PROWL-Data')
device = mounted(mount, '<PROWL_DATA_VOLUME_UUID>')
check_root = lambda: mounted(mount, '<PROWL_DATA_VOLUME_UUID>', device)
roots = {'pants_images': Path('<PANTS_IMAGES_ROOT>'), 'pants_labels': Path('<PANTS_LABELS_ROOT>')}

for case in ('PanTS_00000001', 'PanTS_00000002'):
    study = f'pants:study:{case}'   # only if the validated source join confirms this pairing
    for structure in ('pancreas', 'pancreatic_lesion'):
        report = audit_pair(roots, ct=('pants_images', f'{case}/ct.nii.gz'),
                            mask=('pants_labels', f'{case}/segmentations/{structure}.nii.gz'),
                            expected_values=[0, 1], study_ids=(study, study), check_root=check_root)
        print(json.dumps(report, sort_keys=True, allow_nan=False))
```

`expected_values=[0, 1]` is a probe for per-structure binary files, not a label policy. Omit
it to get raw value counts only. Outputs belong in a reviewed evidence location of Codex's
choosing, not in the repo.
