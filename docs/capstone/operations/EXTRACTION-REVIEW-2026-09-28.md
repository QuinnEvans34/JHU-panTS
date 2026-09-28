# Extraction review — September 28, 2026

Status: first corrective slice tested; full review and data revalidation remain open.

Verification: 248 Python tests passed, with two upstream torch deprecation warnings.
An initial run exposed tests relying on the old delayed floor check: they used laptop
temporary storage against the external-drive floor. Fixtures now explicitly simulate
healthy external capacity, while dedicated failure tests override it. Production
capacity thresholds were not lowered. No UI changes or UI rerun in this slice.

## Evidence and scope

Codex read the extraction receipts: 15 archive completion events, 300,608 files,
565,327,340,747 expanded bytes. Corresponding destination directories exist.
This is receipt reconciliation, not an independent payload hash verification.
The publisher test-image archive remains unextracted. No source activation,
training, real-data extraction, drive writes, or Git commit was performed in this slice.

## Confirmed defects and corrections

- An empty existing destination was accepted as already extracted. Existing trees now
  must pass file-count/total-size checks before skipping; logs explicitly label that
  metadata-only verification, not content verification.
- Cumulative expanded-size limits were enforced after writing the offending file.
  TAR and ZIP now check before opening/writing that member. Direct member writes
  also reject excessive declared sizes.
- Floor checks occurred after writes and were time-throttled. A forced guard check
  now precedes archive extraction, and available space is checked before member creation
  and each chunk write. Mount checks remain paced to avoid a diskutil call per file.
  This is not a filesystem reservation and cannot prevent another process consuming space.
- Verification now rejects non-directory/symlink roots and special files, propagates
  directory traversal errors, and fails if a requested extracted tree is absent.
- Same-size content changes demonstrably pass metadata checks. This limitation is
  retained explicitly, not misrepresented as a repaired content-integrity mechanism.

Five new synthetic regression cases cover TAR/ZIP pre-write ceilings, same-size
changes, symlink roots, and pre-write floor enforcement. The existing destination
test now requires rejection of the invalid tree.

## Initial open items (see follow-up sections for subsequent resolutions)

1. Enforce the complete documented queue budget (payload, overhead, retry, cache
   reserve, free-space floor), beyond the per-write floor checks added here.
2. Fix and qualify TAR end-of-archive validation in both scanner and extractor.
   The old scanner misses appended data; the extractor's length bound is not a
   comprehensive proof that trailing padding contains only zeros. Preserve dated
   scan receipts and append evidence rather than rewriting history.
3. Review promotion/no-clobber races, path ancestor races, crash durability and ZIP
   archive identity. Current checks are not protection against a concurrent hostile writer.
4. Define and execute targeted content verification, including pinned PANORAMA label
   identity and PanTS label integrity; metadata checks alone are insufficient.

## Corrections to layout interpretation

Treat OBSERVED-LAYOUT-2026-09-28.md as provisional for downstream decisions.
Compressed file size depends on both the voxel grid and compressibility/content;
size anomalies alone establish neither field of view nor label validity. Sampling
50 of 101 cases cannot prove pancreatic structures are unaffected. Do not remove
quality/exclusion controls on this evidence.

Three manual negative studies can support only a very uncertain specificity estimate,
not no estimate. Mixed annotation provenance is not mathematically unavoidable for
every possible sensitivity/specificity evaluation. Prevalence alone does not alter
the definition of specificity; case mix and selection can change measured performance.
These are review corrections, not new empirical findings about the source images.

## Tool access

The direct patch tool could not resolve the relocated checkout. Invoking the installed
apply_patch executable through an explicitly scoped, approved shell command succeeded.
No project relocation, duplicate checkout, symlink, or global permission change was needed.

## Next

Complete the open safety review, qualify targeted verification, reconcile shared status,
then proceed to Plan 02 protected inventory and patient-grouped cohorts. Plan 04 coding
authorization is unchanged. Nothing here declares the sources training-ready.

## Follow-up corrective pass and direct integrity checks

The queue and individual new archive now enforce the documented budget: payload,
10% overhead rounded up, 64 GiB retry allowance, 1 TiB future-cache reservation,
and the existing free-space floor. Existing partials consume actual free space;
they are never deleted to make the check pass.

Scanner and extractor now share a streaming TAR audit that tracks the last nonzero
decompressed byte even when tarfile reads ahead. It requires two terminator blocks,
512-byte alignment and zero trailing padding, capped at 16 MiB. The cap is an
explicit supported-format policy, not a claim that all possible TAR writers use it.
Regression tests cover appended data, nonzero data hidden inside existing padding,
missing terminators, USTAR/GNU/PAX and additional zero blocking. The obsolete
extractor length-only check was removed. Old scan receipts remain unchanged.

Validation: **255 Python tests passed**, two upstream deprecation warnings.

Direct read-only PANORAMA check: **2,242 extracted files, 1,252,888,391 bytes**
matched every blob size and Git SHA-1 in the retained, non-truncated pinned tree
`label-tree-20260920T040820977803Z.json`. Run took 15 seconds; mounted volume
identity was checked at start, periodically and at finish. This checks all expected
package file contents against the local pinned reference, not medical annotation
quality, absence of extra files, or an independently refetched upstream tree.

Still open: promotion race/crash durability and ZIP archive-identity hardening;
full PanTS label archive revalidation with the revised scanner; broader extracted
content verification and geometry/voxel checks. No new extraction should start
under a claim that this is a complete adversarial security review.

Bounded PanTS check: the first **58 eligible training-label archive members**
(IDs restricted to 1–9000), totaling **6,488,845 bytes**, matched extracted sizes
and SHA-256 content hashes against the retained label archive. This deliberately
non-random sample establishes only those files' agreement. It does not validate
the entire archive's gzip trailer, current compressed hash, all extracted labels,
or annotation semantics. No publisher-test label payload was selected for comparison.

## Promotion and ZIP mutation follow-up

macOS promotion now uses renamex_np with RENAME_EXCL and RENAME_NOFOLLOW_ANY,
confirmed against the installed SDK and man page. A regression proves an existing
empty destination cannot be replaced. Other operating systems fail closed for
promotion until an equivalent primitive is qualified; there is no plain-rename fallback.

ZIP extraction now compares device, inode, size, modification and change timestamps
before/after extraction and rejects a changed input. This is mutation detection,
not a publisher checksum or cryptographic authenticity proof. ZIP CRC still checks
member payloads. Acquisition digests and the direct pinned-label check remain separate
evidence; CT ZIP publisher hashes were not reread in this review.

The volume is checked again after the pre-promotion flush, and a second flush follows
promotion before success is emitted. Neither flush proves power-loss durability of the
USB device. After a crash, preserve questionable output and reverify content; metadata
counts cannot detect same-size corruption. Parent-path replacement during member writes
is outside the single-writer trusted-workstation boundary. Do not run concurrent writers
or treat these scripts as an adversarial multi-user security sandbox.

Validation: **257 Python tests passed**, two upstream deprecation warnings. Tests ran
on macOS, including the real exclusive-rename primitive against temporary directories.
No real-data extraction or promotion occurred. Full label rescan was started read-only;
its terminal result will be appended separately.

## Complete PanTS label archive rescan — passed

The revised scanner read the full compressed stream through gzip EOF and validated
the TAR terminator/padding. Volume identity was checked at start, during progress,
and at completion. Terminal result:

- Files: 287,128; directories: 19,802.
- Expanded member bytes: 52,020,675,883.
- Compressed bytes read: 15,561,944,549.
- SHA-256: `2de0c363c73c8106b0456d49f3e5057641fefb5383a03f6cf13b4f300a672c83`.
- Member safety issues: none.
- Hash, file count and expanded size match the September 21 receipt.

This resolves the old scanner's trailing-data uncertainty for the retained label
archive. The hash remains a local continuity check, not a publisher-provided label
digest. It does not establish every extracted file's current contents or voxel quality.
The full archive includes publisher-test label members; this was structural/integrity
validation only, without loading images for analysis, selection or training.

Next: Plan 02 protected inventory and patient-grouped cohort controls, with geometry,
label semantics and duplicate reconciliation retained as explicit source-readiness gates.
No archive deletion, new extraction, source activation or Git commit was performed.
