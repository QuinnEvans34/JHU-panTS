# PanTS metadata adapter — September 28, 2026

Status: daily-plan item 1 complete; no manifest/cohort publication or eligibility approval.

Implementation: src/data/pants_metadata.py, tests/test_pants_metadata.py.
No added dependencies; narrow standard-library XLSX reader for the single named
PanTS_metadata worksheet and its pinned relationship. Not a general Excel parser.
It supports shared strings, inline strings and numeric cells; refuses formulas,
duplicate workbook entries/cells/studies, unsupported relationships/types, oversized XML,
missing/duplicate required columns and ambiguous tumour flags. Explicit XML/row/input
limits bound this pinned-workbook use, not arbitrary untrusted spreadsheet ingestion.

Input bytes must match the supplied approved SHA-256. Required columns are PanTS ID,
shape, spacing and tumor?. Nullable values stay missing; a missing tumour flag becomes
unknown, never negative. Source tumour status is preserved as publisher metadata, not
asserted voxel presence, diagnostic truth or annotation eligibility. Source spacing has
no declared units; spatial_units remains null. No biological patient identity is inferred.

## Real read-only reconciliation

The metadata file matched pinned SHA-256
`4bcbf14a31b1ca9441af051a104702e7a832391f47d3af5f493048ec813283e3`.
The adapter parsed 9,901 unique valid PanTS IDs. It then joined the first two sorted
members of the approved, hash-verified training list:

| Study | Metadata row | Shape | Numeric spacing | Source tumour flag |
|---|---:|---|---|---|
| PanTS_00000001 | 2 | 512,333,200 | 0.625,0.625,0.8 | 0 / negative |
| PanTS_00000002 | 3 | 275,198,180 | 1.5,1.5,1.5 | 0 / negative |

These source values agree numerically with the earlier header observations to float
precision. Unknown units and unresolved annotation semantics are unchanged. Reading the
metadata inventory includes publisher-test identifiers but does not access test image
payloads, select models, or alter protected membership.

## Verification and next

17 new synthetic checks; 326 total Python tests passed, two upstream torch warnings.
Checks include hash mismatch, unknown/malformed flags, malformed tuples, duplicate IDs,
reordered/missing/duplicate columns, exact missing/duplicate join failure, shared strings,
numeric cells and formula rejection. No shared interface or Claude-owned file changed.

Next is daily-plan item 2: assemble the real sampled subject/study/annotation/issue
records, preserve issue/inference provenance, and publish a new quarantined diagnostic
package under ignored outputs/prowl with reproducibility evidence. No full source
activation or frozen capstone cohorts are implied by this metadata milestone.
