# Claude work packet: bounded voxel audit

Status: prepared for Quinton to give Claude; not dispatched or started by Codex.
Owner: Claude implementation; Codex independent review and real-data execution.
Purpose: produce trustworthy diagnostic measurements, not eligibility decisions.

## Workspace and baseline

Use only `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
Read AGENTS.md, CLAUDE.md, docs/capstone/README.md and
docs/capstone/operations/WORKSPACE-SAFETY.md. Current approved capstone decisions
outrank old project history. Check pwd, Git root, status and check_workspace.py.
Missing paths mean stop; do not recreate Neuro-data, clone, move files or add symlinks.

HEAD: f4d7109b466fc12854be4a86c9893750399a0672. Important: that commit alone is NOT
the working baseline. Much reviewed code remains untracked/uncommitted. Do not reset,
clean, checkout another branch, stage everything, stash, commit or push. This packet
authorizes same-checkout, disjoint-file work; no new checkout/worktree is authorized.
Git branches do not isolate agents in the same directory.

Read-only interface snapshot at handoff (SHA-256):

- src/data/source_evidence.py: 54fe5b2c5fe56696149be57ba3bd2f498e73c3144b88f90472b809306ef8433c
- src/data/protected_identity.py: 833dc2dcb2d08d355810dca23232d220d458fcb1c837cd402bbd77b8c8e5b755
- src/data/manifest_records.py: 090dabfc1fd7ea5879bed4d8fcc77e4b465bef210ee0652d2a6fb18daf10d5e7

If these change, report the interface drift before integrating against them. Do not
restore the old bytes. Codex will avoid changing these interfaces during this packet
without explicitly notifying Quinton/Claude.

## Required reading

- docs/capstone/data/SOURCE-EVIDENCE-2026-09-28.md
- docs/capstone/data/SPATIAL-UNITS-REVIEW-2026-09-28.md (approval follow-up supersedes proposal heading)
- docs/capstone/data/OBSERVED-LAYOUT-2026-09-28.md (provisional conclusions)
- docs/capstone/operations/EXTRACTION-REVIEW-2026-09-28.md
- docs/capstone/implementation/09-testing-and-quality.md
- docs/capstone/data/PANORAMA-MAPPING.md (context, not authorization to change mappings)
- the three interface files above and tests/test_source_evidence.py

## Exclusive write allowlist

Create only these files; if any already exists, inspect ownership before editing:

1. scripts/diagnostics/audit_voxels.py
2. tests/test_voxel_audit.py
3. docs/capstone/data/VOXEL-AUDIT-DESIGN.md
4. docs/capstone/data/VOXEL-AUDIT-CLAUDE-HANDOFF.md

Synthetic NIfTI fixtures must be created under pytest temporary directories at test
runtime. Do not commit binary fixtures. No edits to src/data, schemas, shared docs,
AGENTS/CLAUDE, existing tests, dependencies/locks, pytest configuration, UI or training.
If more files or dependencies are needed, propose them and stop that part for review.
The allowlist is a coordination rule, not an OS security sandbox.

## First deliverable: synthetic-only audit kernel

Do not attempt the whole data pipeline. Implement callable pure/diagnostic functions
that accept an explicit CT/mask pair and return JSON-serializable measurements/issues.
Use installed NumPy/NiBabel; reuse read-only source_evidence interfaces where appropriate.
No default real roots, recursive scans or automatic file discovery. No production CLI
execution against the external drive in this packet. A fixture-only demo is sufficient.

Required measurements:

- Native header shape, declared units, selected affine, qform/sform and consistency;
  compare paired grids using documented absolute tolerances. Do not resample.
- File identity and evidence provenance without absolute paths in scientific output.
- Voxel count, nonfinite count, finite min/max; mask nonzero count and emptiness.
- Bounded distinct mask-value summary, nonintegral/negative label detection, and explicit
  overflow/truncation flags. Accept expected values as a caller policy, never guess that
  every label source uses binary 0/1. CT intensities are not discrete label classes.
- Distinguish raw stored versus scaled NIfTI values. State which is reported and test
  slope/intercept behavior; no silent integer casts or threshold-based relabeling.
- Physical mask volume only when mm geometry is explicit or carries approved inferred
  provenance; unknown units mean unavailable physical volume, not assumed mm.
- Shape/affine mismatch reported as a blocking diagnostic; do not compute paired overlap
  on incompatible grids or silently reshape, transpose, reorient, or resample.

Bound memory explicitly: proxy/slice or slab iteration, voxel/shape/working-buffer limits
checked before large allocation, capped distinct-value accumulation. No unconditional
get_fdata() or full-volume np.asarray(proxy). Account for dtype promotion and temporary
buffers. Compressed-file slicing may be slow: document this tradeoff rather than claiming
a full-dataset runtime. Stop on unsupported dimensions, malformed/truncated payloads,
observed file mutation, exceeded limits or unavailable prerequisites; preserve errors.

## Scientific boundaries

- A measurement is not an approved exclusion, annotation mapping or eligibility decision.
- The 101 size-flagged cases are audit candidates, not confirmed corrupt labels.
- Unknown units: reuse the approved paired-explicit-mm-CT rule without weakening it.
  All-unknown pairs remain unresolved. Originals are never rewritten.
- PANORAMA labels' semantic mapping remains Plan 03 work. Reporting a set of values
  does not prove what the values mean or establish manual/automatic provenance.
- Do not declare negative diagnosis from an empty or unavailable mask.
- No inference, training, checkpoint reads, CAP-EXP, Prefect, executor loop or Plan 04 code.

## Minimum acceptance matrix

Use hand-constructed independent expected values, not production output as its oracle:

1. Empty binary mask; nonempty mask with exact known voxel count.
2. Anisotropic mm geometry with hand-computed physical volume.
3. Unknown units: voxel count available, mm volume unavailable.
4. Same shape but shifted/flipped affine; differing shapes; qform/sform disagreement.
5. Multiple allowed labels plus unexpected value; fractional and negative labels.
6. NaN/Inf handled explicitly rather than dropped from the denominator silently.
7. NIfTI slope/intercept case; compressed and uncompressed cases.
8. Truncated/corrupt payload, 4D input, declared oversized shape and distinct-value cap.
9. Instrument proxy access to reject full-array conversion and enforce slab bounds.
10. Inputs unchanged, deterministic outputs, mutation rejection and original headers preserved.

Run your focused tests first, then the full suite when the native environment is available:

    env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/test_voxel_audit.py -q -p no:cacheprovider
    env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider

Baseline: 309 passes, two upstream torch deprecation warnings. Count changes alone do not
prove acceptance. Use existing registered pytest markers. If working in a Linux VM where
the Mac venv cannot run, state that clearly; do not rebuild the project environment or
claim native verification. Codex will run the Mac tests after your handoff.

## Stop and hand back

One bounded implementation pass, then hand back for review—no autonomous task loop.
Report exact files changed, current hashes, tests/environment/results, skipped checks,
design choices/tolerances, known limits, estimated memory formula, and proposed real-data
pilot commands (not executed). List interface changes needed instead of editing shared code.
Do not modify Notion, send external messages, or mount/access real data during this packet.

Codex reviews independently, runs native tests, then selects a training-only real-data
pilot after inspection. This packet does not authorize real-data scanning or acceptance
of Claude's output without that review. Quinton owns final scientific scope decisions.
