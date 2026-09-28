# Native voxel-audit review — September 28

## Resolution — Codex ownership accepted

Quinton explicitly transferred implementation ownership to Codex. R1–R3 are fixed in
voxel-audit-v1.1; original findings below are retained as review history. No return to
Claude is required. Shared source-evidence/identity/manifest interfaces remain unchanged.

- Paired statistics are published only after both finalizers succeed. Late failure clears
  paired interpretation; failed CT integrity also withholds CT-derived mask volume.
- Unresolved ambiguous-geometry codes suppress physical volume for standalone and paired
  audits; raw geometry evidence and voxel counts are retained.
- Fixture demo resolves its own temporary root; production path protections are unchanged.
- Added 15 regressions: either partner's late root/CRC/mutation stop, actual final root
  callbacks, standalone/paired geometry conflicts and uncoded transforms, and a temporary
  directory alias. Focused native suite: **77 passed**. Full native suite: **410 passed**,
  two upstream torch warnings. Injected CRC/mutation finalizer tests supplement the
  existing actual corrupt-gzip and file-mutation tests; they are not real-drive fault tests.

Accepted for the bounded pilot, not universally qualified for every NIfTI or a full scan.
Pilot evidence/results: VOXEL-PILOT-2026-09-28.md. Full qualification remains open.

Disposition: **changes requested; real-data pilot not started**.
Claude's four delivered file hashes match its handoff. The three shared interface hashes
also match. No Claude-owned implementation/test files changed during this review.

## Native verification

Mac .venv-prowl, existing dependencies; no environment changes:

- Focused suite: **61 passed, 1 failed** (test_cli_runs_only_the_fixture_demo).
- Full suite: **394 passed, 1 failed**, two upstream torch warnings, 4.20 seconds.
- Three additional synthetic diagnostic probes independently reproduced the findings below.
- No real source files, external-drive scans or training used in this review.

The previous 333-test baseline is preserved. Claude's 309 baseline reference was historical.
Its Linux results and mutation campaign are reported evidence, not independently rerun here.

## Required fixes within Claude's existing four-file lane

### R1 — paired results must wait for final integrity checks (high priority)

audit_pair assigns within_mask_ct at lines 700–701, before ct_t.finish and mask_t.finish
at lines 716–717. Those finalizers can still reject the file through CRC, mutation or
root-identity checks. The returned paired statistics survive that rejection.

Independent reproduction: synthetic uncompressed 6x5x4 CT (values -1000 through -881)
and all-ones mask, same valid mm grid. A check_root callback succeeds six times (both
evidence paths), then raises RuntimeError starting at call seven (finalization).
Both CT and mask returned status=stopped, while within_mask_ct still reported 120
voxels and mean=-940.5. This violates the fail-closed paired-result boundary.

Fix: finalize both files before publishing any paired statistic. If either stops,
within_mask_ct must be null and its unavailability reason explicit. Do not allow a
paired inferred physical volume to survive failure of the CT evidence it depends on.
Preserve original stop reasons and valid independent measurements where justified.
Add regressions for each partner failing at finalization, including late CRC/mutation
and root-check failure—not only failure while consuming voxel chunks.

### R2 — do not present ambiguous physical geometry as a valid volume (high priority)

_Target.finish and audit_pair use any non-null geometry for physical mask volume,
even when header_issues includes qform_sform_disagreement or affine_spacing_disagreement.
The shared adapter can return a selected affine AND issues; non-null is not approval.

Independent fixture: 120 occupied voxels, mm units, sform spacing (.75,.875,2.5), qform
spacing (1.5,.875,2.5). Both disagreement codes were present, yet volume.available=true,
mm3=196.875, basis=header_mm, reason=null. The alternate coded transform implies twice
that physical volume. A shift-only conflict also reports an unconditional volume.

Fix: conservatively withhold physical volume for unresolved geometry issues in the
existing ambiguous-grid set; retain raw/header evidence and nonzero voxel counts.
Apply consistently to standalone and paired audits. Approved inferred-mm results still
require clean supporting CT evidence. Add standalone and paired disagreement/uncoded
regressions; preserve successful explicit-mm and approved inferred-mm cases.
No shared-adapter change is needed to fix these audit consumers.

### R3 — canonicalize the fixture root, not the safety boundary (medium priority)

demo uses Path(tmp), but macOS TemporaryDirectory can return a /var path resolving to
/private/var. The shared resolver correctly refuses noncanonical roots. The CLI returns
stopped evidence, grid=null, and test_cli_runs_only_the_fixture_demo fails.

Fix demo's own root with Path(tmp).resolve(); retain the resolver's strict guard.
Add a platform-independent regression using a temporary-directory alias so Linux can
exercise this too. Do not loosen real-root/symlink protections to make the demo pass.

## Decisions reviewed

- Keep rejecting infinite scaling factors rather than silently treating them as identity.
- Keep the strict pairing tolerance for the initial pilot. Measure real differences first;
  do not relax tolerance globally based on hypothetical rounding.
- Keep bounded streaming. The 256 MiB working budget is an estimate plus overhead, not a
  hard process RSS cap. Full-scale runtime remains unmeasured.
- The unknown-unit transform-check gap in shared evidence is real; the local audit check
  is useful. Shared issue normalization/root-helper refactoring can follow separately.

## Handback to Claude

Read this review, fix R1–R3 only within the original four-file allowlist, extend the
synthetic tests and update your handoff with hashes/results and remaining limits.
Do not run real data, change shared interfaces/dependencies, commit or start another task.
If native Mac execution is unavailable, say so; Codex will rerun the full suite.

This packet is ready for Quinton to pass to Claude; it has not been sent automatically.
After corrected handback, Codex reviews again, reruns native tests, and only then
considers the two-case training-only pilot. No broad scan or eligibility promotion.
