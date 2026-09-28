# First real diagnostic manifest slice — September 28

Status: built, schema/link checked and replay verified; **quarantined**, not a frozen
cohort or qualified source. Daily item 2 is partly complete; annotations remain deferred.

## Evidence and result

Ignored local package:
`outputs/prowl/manifest-slice-35acf328-ae35-4c32-954c-df2c34034d87/`

Manifest ID:
`manifest:pants-diagnostic:93552beff9c65d437d21ccd3452d5d8946383a95791f81f372f15af3301fc886`

- First two sorted members of the exact hash-approved training list, not evaluation cases.
- Two subjects, two studies; six measured CT/pancreas/lesion file references.
- All six SHA-256 values match the earlier SOURCE-EVIDENCE checkpoint.
- Eight blocking issues: two qualification-pending, two unverified subject-identity,
  four original unknown-spatial-unit findings. These are not eight defective files.
- Zero eligible studies and zero annotation records; no allowed annotation uses granted.
- Source snapshot partial; diagnostic root alias only. Production aliases remain disabled.
- Persisted assembly inputs reproduce every canonical collection and manifest byte exactly.
- Seven new synthetic tests; full Python suite **333 passed**, two upstream torch warnings.
- Claude's reserved files were untouched; all three held interface hashes remain unchanged.

## What a record means

`pants:study:PanTS_00000002` links its source identity, source-scoped subject fallback,
exact CT hash/relative location, and blocking issue IDs. Its geometry is null because
the CT header does not declare physical units. Numerical spacing agrees with metadata,
but that is not independent proof of millimetres. It cannot enter training from this package.

The metadata's tumour flag is retained as source evidence, not promoted to a verified
lesion target or generic clinical diagnosis. Target status remains unknown. Acquisition
fields are deliberately null in the narrow study adapter; the original selected metadata
rows remain in metadata.json, pending field-level normalization.

## Annotation contract limitation and next step

The annotation schema requires nonempty source voxel values and a mapping version, with
no representation for unknown encoding. This pass has only hash/header evidence, not a
verified voxel mapping. Filling those fields would fabricate evidence. Therefore masks
remain in measurements.json and selected-files.json, with QUALIFICATION_PENDING linked
to each study, rather than incomplete or invented annotation records.

After Claude's audit is handed back and independently accepted, run the bounded pilot,
review encoding/provenance, then create a NEW package containing annotation records.
Do not overwrite this package or mark daily item 2 fully complete yet. No schema/interface
change was made while Claude works against the agreed interface snapshot.

## Unit interpretation and history

unit-interpretation.json separately records the approved paired-CT inferred-mm result for
case 1's pancreas, including both file hashes and original unknown units. Original measured
evidence and issue records remain unchanged. The diagnostic manifest intentionally retains
the original issue as open: formal append-only resolution publication is not implemented by
this builder. Case 2 remains unresolved. No headers or source files were rewritten.

## Reproduction and limits

Builder: scripts/diagnostics/build_manifest_slice.py. Execute from the repository root with
`.venv-prowl/bin/python -m scripts.diagnostics.build_manifest_slice` only when the registered
drive is mounted. Each execution remeasures the same two approved training cases and creates
a NEW UUID directory; it never resumes/overwrites an existing package. This is diagnostic
code, not a general manifest CLI or production publisher.

assembly-inputs.json persists issue IDs once; replay uses these saved records rather than
generating new UUIDs. verification.json hashes the package files and records replay success.
The successful check is persisted-input reproducibility, not identical identity across fresh
acquisitions. Fresh runs intentionally create new issue/run IDs and timestamps.

code-identity.json records scoped source/schema SHA-256 values, including untracked code;
its canonical digest occupies build.diff_sha256. It is a scoped source fingerprint, NOT a
literal Git patch or complete environment capture. HEAD alone is not the runnable baseline.
config.json captures selection and approved input hashes. The snapshot inventory URI is
package-relative; file references use the diagnostic extraction alias. Do not feed this
diagnostic alias into a production resolver without its separate qualification.

The writer validates before publishing and refuses an existing directory. It is not atomic
production publication or power-loss durability: incomplete failures lack verification.json.
No full-data scan, voxel audit, extraction, cohort freeze, training, commit, push or Notion
update occurred in this pass. Generated source metadata stays ignored, not committed.
