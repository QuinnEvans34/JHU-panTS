# Plan 02 implementation checkpoint — September 28, 2026

Status: first identity and migration-guard slice implemented; G1 remains open.

Follow-up: [manifest assembly](MANIFEST-ASSEMBLY-2026-09-28.md) is now implemented
and tested with supplied synthetic records. Real source evidence collection and frozen
cohort publication remain incomplete; do not treat this as completion of G1.

## Implemented

`src/data/protected_identity.py` provides pure, internal discovery identities and guards.
It does not publish schema-complete study/subject records or frozen cohorts.

- PanTS IDs are validated against the pinned 1–9,901 range. IDs above 9,000 retain
  publisher-test partition. Subject identity explicitly uses the unverified
  study-as-subject fallback; biological uniqueness is not asserted.
- PANORAMA grouping requires an explicit metadata patient ID, not a filename-derived
  patient assumption. The pinned CT filename adapter accepts only channel 0000;
  unreviewed channels fail instead of being silently collapsed.
- Duplicate study assignments and subjects crossing protected roles are rejected.
  Publisher-test identities are allowed only in the test role in this slice.
- The three approved legacy base lists are allowlisted by exact bytes/hash and count,
  not filename. Arbitrary or modified lists fail closed.

## Verification

Twenty new synthetic checks; **277 total Python tests passed**, two upstream warnings.
Read-only check against actual local migration inputs passed all three approved SHA-256
hashes, uniqueness/grouping checks and exact counts: 7,200 train, 1,800 validation,
901 test; total 9,901. No source images or label voxels were read for this check.

No cohort was frozen, source alias activated, historical membership modified, or
training consumer changed. Existing historical training scripts are not newly protected
by importing this module; the future capstone consumer must enforce all gates.

## Evidence discrepancy to resolve

The September 28 observed-layout note claims 14 PANORAMA patients repeat. The earlier
metadata audit records 11 repeated patients contributing 25 studies (maximum five).
Both are compatible with 2,238 studies / 2,224 patients only in the sense that the
difference is 14 extra studies; that subtraction does not count repeating patients.
Recompute the distribution from pinned metadata before reporting a current count.
The implementation groups by explicit patient ID regardless of that distribution.

## Remaining sequence

1. Source-root resolver and schema-complete manifest adapters with real file identities;
   do not fabricate content hashes, geometry or eligibility to fill required fields.
2. Reconcile pinned metadata, discovered images and annotations; preserve unknowns and
   emit quarantine issues. Keep protected test inventory separate from model access.
3. Reproduce the approved base membership in canonical cohort records; verify ancestry,
   duplicate protection groups, eligibility and annotation permissions.
4. Deterministic subject-grouped selection, immutable publication, registry resolution,
   repeat-build hashes and the consumer smoke test.

This internal identity slice does not implement cross-source duplicate adjudication,
full ancestry validation, source eligibility or a secure public record-ingestion API.
Those remain explicit prerequisites before G1 completion or capstone training.
