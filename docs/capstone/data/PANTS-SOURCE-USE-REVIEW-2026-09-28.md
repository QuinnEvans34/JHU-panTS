# PanTS source linkage, usage terms and decoding decision

Reviewed September 28, 2026. Evidence review and recommendations, not legal clearance,
publisher confirmation, annotation promotion or training authorization.

## Verified release linkage

The pinned [Hugging Face card](https://huggingface.co/datasets/BodyMaps/PanTSMini/blob/3b1cd61108116b58ea5c1ddb3512c1847d965f96/README.md)
identifies PanTSMini as the PanTS release with 9,000 training and 901 in-distribution test
images and directs users to the official GitHub project and PanTSMini_Label.tar.gz.
The pinned [official downloader](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/download_PanTS_label.sh)
uses that same JHU label archive URL and separates training/test IDs at 9000/9001.
These are publisher links, not scripts executed during this review.

This establishes source-family/archive-endpoint linkage for our acquisition. It does not
prove that the mutable archive bytes never changed or that every file received an identical
annotation procedure. Existing local archive hashes remain our byte identity; the publisher
does not provide a new per-file attestation through these documents. Preserve our approved
7,200/1,800/901 memberships; paper-version terminology cannot replace them.

## Annotation provenance

The [versioned paper, section 3.3](https://arxiv.org/html/2507.01291v1#S3.SS3)
describes manual tumor labeling/review and AI-initialized non-tumor anatomy followed by
human verification/correction. Therefore proposed source-protocol labels remain
human_manual for lesions and human_validated for pancreas, with publisher_protocol scope
and source_asserted assurance—not project_verified. The paper includes both inherited and
new tumor annotations. Do not imply every original mask was independently inspected by us.

Release-specific applicability, exceptions, rights and allowed-use decisions still must be
recorded before replacing unknown method in the quarantined v2 records. Source-level
provenance does not resolve empty masks, physical units, coverage or geometry.

## License discrepancy: confirmed, not silently resolved

- [Pinned GitHub LICENSE](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/LICENSE): CC BY-NC-ND 4.0.
- Pinned Hugging Face card: CC BY-NC-SA 4.0.
- The paper's own publication license is not a substitute for the dataset license.

Under [CC BY-NC-ND section 2(a)(1)](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.en),
noncommercial production/reproduction of adapted material is permitted, but sharing that
adapted material is not. [CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en)
permits adaptation/sharing subject to its conditions. This supports distinguishing local
noncommercial research processing from public distribution; ND is not a blanket prohibition
on private preprocessing. It does not settle which license covers each acquired component,
underlying contributors' rights, or how trained weights are legally characterized.

Recommended operational boundary: continue engineering and qualification for local academic
research, retain attribution and restrictions, keep data/derived masks private and off Git.
Do not mark unrestricted redistribution, commercial use, public derived data, or model-release
clearance. Before model delivery/public release, resolve applicable requirements with the
publisher and, if needed, the school's research/legal support. The official checkpoint
submission invitation supports contacting JHU, not an unrestricted model distribution license.
No contact was made, terms accepted on Quinton's behalf, or existing hold removed in this pass.

## Rechecked pinned response hashes

Read-only HTTP retrieval; no dataset or source-drive reads. Full documents were not copied
into the repo. These hashes identify the fetched raw response bytes, not a local cached file.

| Pinned resource | SHA-256 |
|---|---|
| HF card README | 9ef102440ac6c6a0b4c63237f332380a6571c18cd19f1f60e7257d7e4e23e68f |
| GitHub LICENSE | 3581c0055b9652dd9e7a8e55755879fde7ab2ea511878ae268fd6fae3546ff81 |
| GitHub label downloader | ab7c4489f59af7c66d420f2cd5b046ffa69ffbc1927a6ab92e0b0006a4b8f92e |

## Decision to request from Quinton: strict binary decoding

Recommend approving the existing candidate rule for later qualified binary-mask consumers:
apply NIfTI scaling first; accept each voxel only within absolute 0.000001 of zero or one,
with zero relative tolerance; normalize to a NEW uint8 0/1 representation; reject all other
values and nonfinite inputs. Preserve originals, hashes, policy identity and change counts.
This covers measured foreground 1.0000000591389835 without adopting generic positivity.
Empty masks remain empty and do not become automatic clinical negatives or eligible targets.

Status: awaiting explicit policy approval. This is NOT authority for full-data rewriting,
training, old-checkpoint reuse or release. Once approved, version the policy and attach a
decision record; resource qualification, provenance, geometry and per-purpose allowed-use
gates remain separate. Existing candidate implementation is unchanged and unactivated.

## Next steps

1. Obtain the narrow decoding-policy decision; do not require Quinton to adjudicate a license.
2. Implement approved policy identity/lineage without enabling unqualified training.
3. Continue source/geometry/identity qualification and decide the bounded next audit scope.
4. Keep publisher clarification for release/terms as an explicit track, not a reason to stop
   unrelated tests or Claude's independent retrieval foundation.

Documentation-only pass. Last native software baseline remains 545 passing tests; tests were
not rerun for this source review. No eligibility, source file, schema or model state changed.
