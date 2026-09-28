# Source evidence adapter — September 28, 2026

Status: read-only hash/header adapter tested; bounded real-data sample completed.
G1 remains open; no source activation or frozen cohort publication.

## Implementation

`src/data/source_evidence.py` resolves only explicitly supplied diagnostic root aliases,
rejects traversal, absolute/noncanonical paths, symlinks and non-regular files, hashes
exact file bytes, and detects observed identity/size/time changes across hashing and
header inspection. Real-data callers supply the registry-based mount/UUID callback.
This diagnostic root mapping does not enable production source aliases.

NIfTI geometry requires positive finite 3D shape/spacing, a nonsingular finite affine,
and explicit spatial units. Known units are converted to millimetres. Unknown units,
uncoded transforms, conflicting qform/sform and affine-spacing disagreements become
explicit issue codes. No voxel arrays, mask occupancy or anatomical semantics are read.
Issue codes are diagnostic findings, not yet published schema-complete data-issue records.

Source metadata joins and study/annotation record construction remain unimplemented.
This adapter alone cannot establish snapshot completeness or eligibility. It assumes
the approved single-writer workstation boundary, not hostile concurrent path mutation.
Hashing compressed bytes and reading headers does not independently validate every
decompressed voxel payload or its gzip trailer.

## Tests

Eleven new tests; **301 total Python tests passed**, two upstream warnings. Coverage:
known hash/geometry, prohibited voxel array loading, five unsafe paths, unknown aliases,
symlinks, unknown spatial units, metre-to-millimetre conversion and file mutation.

## Real-data sample

Selected the first two sorted IDs from the exact hash-verified approved train file:
PanTS_00000001 and PanTS_00000002. Measured CT, pancreas and lesion files for each.
Drive identity checked before and after each measurement. No files modified.

| Study | File | Bytes | Header result |
|---|---|---:|---|
| 00000001 | CT | 40,442,531 | Explicit mm geometry; no adapter issues |
| 00000001 | pancreas | 178,866 | Unknown spatial units |
| 00000001 | lesion | 148,944 | Explicit mm geometry; no adapter issues |
| 00000002 | CT | 11,169,107 | Unknown spatial units |
| 00000002 | pancreas | 50,591 | Unknown spatial units |
| 00000002 | lesion | 42,899 | Unknown spatial units |

The first study's CT and lesion headers reported shape [512,333,200], spacing
[0.625,0.625,0.800000011920929] mm and matching reported affines. This is header
agreement, not proof of correct annotation alignment or content.

Measured SHA-256, in the table's order:

1. `0e2e7a4a8d954e188dba1571c2c338f2619c91e783d1474a3c865f24d4d93950`
2. `10204e1d58ec477f7c05233ba8a48e7763d35d305262736f04cf4e4785cd2f70`
3. `46a1e89ba0d46e0ecc71a4656ace3782186cf56fb6117cc72357f1f047871be0`
4. `d9c23ce3de221bca3fde6b3dfa1b749964a3e95c7d914fbd6b29974eed1454a4`
5. `2e7db34ba66374d67a1249f6403c9c89a9e58736b724f5de76412be830d41028`
6. `982ce7f48b032a35eef00b6f8fcd68b39111d3eb77182b1c06dc26c52635abc7`

These are measured local file identities, not comparisons to publisher file digests.
All six retain eligibility=not_assessed. Four unknown-unit findings are not evidence
of corruption and are not silently repaired or converted to mm.

## Next

Compare raw paired headers and publisher/source conventions to propose an explicit,
evidence-backed units reconciliation policy. Preserve originals and record any later
inference as such. Then add metadata joins and schema-complete unresolved issues,
qualify a sampled manifest build, and plan the full evidence scan. Do not freeze real
cohorts or enable training while required geometry/eligibility is unresolved.
