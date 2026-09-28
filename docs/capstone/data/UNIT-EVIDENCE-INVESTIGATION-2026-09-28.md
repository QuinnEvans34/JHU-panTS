# Cases 2 and 266: bounded physical-unit investigation

September 28, 2026. Quinton approved proceeding after discussion of the search scope.
Status: bounded investigation complete; units remain unresolved for cases 2 and 266.
No unit interpretation or eligibility change.

## Plan

Inspect existing local audit/provenance records and official release documentation,
paper and relevant conversion code for evidence that establishes physical units for
the acquired PanTSMini files in cases 2 and 266. Initial source discovery precedes this
written plan; conclusions and case-evidence examination follow it.

Bound: one source-review pass, at most 20 substantive publisher pages/code files plus
their repository listings, and retained local diagnostic records. Stop when those
sources either establish applicability or leave a specific publisher question.
No CT/mask reads, external-drive operations, bulk downloads, original DICOM acquisition,
publisher contact, training, source changes, or expansion into held-out cases.

Acceptable evidence: an explicit release-applicable unit convention, traceable conversion
provenance proving the scale for these files, or independent original-image geometry
with a verified case/version link. Numeric plausibility, matching grids, a training
resampling setting or library default alone cannot establish original physical units.

Outputs: this evidence/result note, an unsent publisher question if unresolved, and a
checkpoint update. Retain exact source URLs/revisions and local evidence identities.
Check local receipt hashes where available. No code change or software test rerun is
needed unless the investigation demonstrates an implementation defect.

## Result

The reviewed evidence supports mm as a plausible intended convention, but does not
establish it for these acquired unknown-unit files. Keep the existing geometry-dependent
use holds. No new conversion rule, source-wide override or paired-CT exception is justified.
This is a scoped negative finding, not a claim that no supporting evidence exists anywhere.

## Local evidence rechecked

All 13 file hashes in each of the following two saved-evidence receipts matched (26
checks total). These checks validate retained diagnostic bytes, not current source-drive
bytes. No CT/mask was reopened.

- `outputs/prowl/manifest-slice-35acf328-ae35-4c32-954c-df2c34034d87/verification.json`
  SHA-256 `39d91b6a4277bd3168d9887ee94ed9378e58e09fc16e8c7ef3b776624e58085b`.
- `outputs/prowl/voxel-followup-140effff-129c-4ff8-b455-70a2119707a1/receipt.json`
  SHA-256 `575acdd7e71861a6400bcafb89547b53c1859ed810619ec571b4b9f9f1f82d98`.

Case 2's retained CT/pancreas/lesion headers all declare unknown units and numeric spacing
1.5/1.5/1.5, with shape 275/198/180. Its retained metadata agrees numerically but records
no unit field. The site information is a provenance lead, not a verified original-case
mapping. No linked original DICOM geometry or acquisition conversion record was found
in the scoped retained records. Generated structured reports are not independent physical
measurement evidence; their derived volume descriptions cannot resolve this hold.

Case 266's retained pairs 09–11 show unknown units for the CT, pancreas, lesion and left
lung; each grid matches numerically, shape 55/369/204. The pair summaries withhold physical
geometry and do not retain a numeric spacing tuple, so this investigation does not invent
one. Pancreas/lesion pair report hashes are respectively
`a8738ca2296674ec21594555ae5b17a8e06ce08e7bff68cce7cdfff3770cf313` and
`95cb2883a00851427f446d002540cbbeb4ccf91de10c2f3f01f43495f558364c`.
The selection record ties the audit to metadata SHA-256
`4bcbf14a31b1ca9441af051a104702e7a832391f47d3af5f493048ec813283e3`;
that hash is not itself evidence of a unit convention.

## Publisher sources and interpretation

| Source inspected | Finding and limit |
|---|---|
| [PanTS paper v1, Table 1 and section 3.2](https://arxiv.org/html/2507.01291v1) | Dataset statistics label spacing/thickness in mm; authors describe conversion to NIfTI with NiBabel. This is corroboration, not a statement that missing unit codes in our release may be interpreted as mm. |
| [Pinned PanTS repository](https://github.com/MrGiovanni/PanTS/tree/243bef3075d2ab556eae374846e3ddfbc9f4c309), including recursive file listing | Contains documentation and download scripts; no original CT conversion pipeline or per-case geometry mapping in this pinned tree. |
| [Pinned data layout/class map](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/data/README.md) | Defines paths/classes, not physical-unit conventions. |
| [Pinned dataset card](https://huggingface.co/datasets/BodyMaps/PanTSMini/blob/3b1cd61108116b58ea5c1ddb3512c1847d965f96/README.md) | Identifies the release and download route; no unknown-unit interpretation rule. |
| [Pinned image downloader](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/download_PanTS_data.sh) | Downloads/extracts packaged images; no conversion or unit validation. Read only, not executed. |
| [Spacing question #1](https://github.com/MrGiovanni/PanTS/issues/1#issuecomment-3156811537) and [release follow-up](https://github.com/MrGiovanni/PanTS/issues/1#issuecomment-3238269888) | Collaborator points to metadata and announces replacement of NPZ with NIfTI. No rule for unknown-unit headers. |
| [DICOM question #2](https://github.com/MrGiovanni/PanTS/issues/2#issuecomment-3156747474) and [release follow-up](https://github.com/MrGiovanni/PanTS/issues/2#issuecomment-3238270788) | Replies discuss metadata and NIfTI availability; they do not provide case-linked original DICOM geometry. |
| [R-Super conversion consumer](https://github.com/MrGiovanni/R-Super/blob/fa8fdce648bc5c547fa76d3fb01e2071e85f8fa7/rsuper_train/dataset_conversion/abdomenatlas_3d.py) and [resampling helper](https://github.com/MrGiovanni/R-Super/blob/fa8fdce648bc5c547fa76d3fb01e2071e85f8fa7/rsuper_train/dataset_conversion/utils.py) | Reads existing NIfTI using SimpleITK, gets spacing and resamples. This downstream consumer is not the release's original acquisition/conversion provenance. It does not independently establish source units. Its affine-rewrite fallback was not executed or adopted. |

The issue-list scan was used to locate the two relevant metadata discussions, not to
adopt unrelated users' scientific claims or inspect additional cases. The public issue
replies and R-Super current branch are supplementary evidence; R-Super was resolved to
the exact commit above before its two code files were inspected. No downloaded code ran.
The review stayed below the 20-source bound. No exact original-case mapping was established.

## Fetched response identities

Public documentation/code was read into temporary files for inspection. These hashes
identify fetched bytes, not a permanent local source cache or dataset hashes. Git commit
URLs above pin code; issue replies can change. Initial web-tool access failed for some
pages; bounded read-only HTTP fetching succeeded after network permission review.

| Resource | SHA-256 |
|---|---|
| PanTS recursive tree JSON | `6d5055835cdbe8cba99d5b157b1d3db76485611104af5deeeb484cf99c380dcf` |
| PanTS data README | `e55c9b5c8ec30de07e80abdf0e7555e7c1597338b4cd266afbe695858163bc9d` |
| PanTSMini card README | `9ef102440ac6c6a0b4c63237f332380a6571c18cd19f1f60e7257d7e4e23e68f` |
| PanTS image downloader | `f92567155d52fa17b911dc060d609673ad0ec474d1b53cfee1189d3b18ea2533` |
| Issue 1 comments JSON | `7db6d3af38a42cc98fcfa42b7a7bef6de13699efd800c2dc1ce1331d6c85b04c` |
| Issue 2 comments JSON | `867697b946431144925720d288470d9c42b2646dce2ddec77d2184d0b5005798` |
| R-Super conversion consumer | `6998a3a4c2fd63bd4690f4cc7c0fd4ec22fca2445312a35c57a7d97ef0163672` |
| R-Super resampling helper | `8129bda66a9ee0b25606876f1f6a6b75c4ec796ad4208569bc360c55acba47e0` |

## Publisher question draft — not sent

We are qualifying the released PanTSMini NIfTI data for a research capstone. In
PanTS_00000002 and PanTS_00000266, the CT and checked segmentation masks declare unknown
NIfTI spatial units, although their grids agree numerically. Case 2 has numeric spacing
1.5/1.5/1.5, also listed in metadata.xlsx. We retain the originals unchanged.

Could you confirm whether the voxel spacing and spatial affine coordinates in these
released files are in millimetres despite the missing unit declaration? Does a documented
convention cover all PanTSMini files with unknown spatial-unit codes, or are there
source-specific exceptions? A release-specific preprocessing reference or original-case
mapping would help us record the interpretation accurately.

Our acquired image snapshot is tied to Hugging Face revision
`3b1cd61108116b58ea5c1ddb3512c1847d965f96`. CT SHA-256 values are:

- Case 2: `d9c23ce3de221bca3fde6b3dfa1b749964a3e95c7d914fbd6b29974eed1454a4`.
- Case 266: `ae4b95e088ac5a443baa1ae51da0f3eba252d68e7448b3fcdb3d78a2c8c4dfd3`.

## Next action and limits

Discuss the result and possible publisher contact with Quinton. Contact requires his
explicit send instruction; this draft is not sent. Keep cases 2/266 on hold and continue
source-protocol applicability/qualification work for other candidates after discussion.
A later satisfactory answer needs retained evidence and a reviewed interpretation policy
before new machine-readable dispositions are published. The paired explicitly-mm CT
policy remains unchanged.

No software defect requiring a change was established. No software tests rerun; last
verified baseline remains 578 passes with two existing warnings. No raw-data reads,
header repair, eligibility promotion, package replacement, experiment or Claude-file edit.
