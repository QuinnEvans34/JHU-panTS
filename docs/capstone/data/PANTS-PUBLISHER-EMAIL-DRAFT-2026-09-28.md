# PanTS publisher email draft

Prepared September 28, 2026 for Quinton to review and send. **Not sent.**
Recipient: PanTS/PanTSMini maintainers through their official project contact.
No email address has been guessed or independently verified for this draft.

Copy the subject and message below. Technical details after the signature may be
included in the initial email or supplied on request. No images or masks are needed.

## Subject

PanTSMini research use: clarification of NIfTI spatial units and release license

## Message

Hello PanTS team,

My name is Quinton Evans. I am working on PROWL, an academic capstone focused on
pancreas and pancreatic lesion segmentation for research annotation assistance.
Thank you for making PanTS available.

While checking the PanTSMini release before training, I encountered two questions
that I could not resolve from the release documentation.

**1. Spatial units in released NIfTI files**

For PanTS_00000002 and PanTS_00000266, our saved header audits report unknown
NIfTI spatial units for the CT and the segmentation masks we checked, although
their grids agree numerically. For case 2, the numeric voxel spacing is
1.5 × 1.5 × 1.5, which also agrees with the metadata spreadsheet.

Could you confirm whether voxel spacing and spatial affine coordinates in these
released files are expressed in millimetres despite the missing unit declaration?
Does that convention apply to all PanTSMini files with unknown spatial-unit codes,
or are there source-specific exceptions? A release-specific conversion reference
or documented convention would be especially helpful.

We have preserved the original files and are holding these cases out of
geometry-dependent training until we can document the interpretation.

**2. Applicable release license**

In the pinned versions we reviewed, the PanTS GitHub LICENSE states CC BY-NC-ND 4.0,
while the PanTSMini Hugging Face dataset card lists CC BY-NC-SA 4.0. Which terms
apply to the PanTSMini images, labels and metadata in this release?

Our immediate use is local, noncommercial academic training and evaluation. For
later capstone reporting, could you also point us to the applicable permissions
or restrictions for example CT images with contour overlays, derived masks and
trained model weights? We are asking for clarification rather than assuming these
outputs all have the same distribution permissions.

Even a pointer to an existing release note or the appropriate maintainer would
help. Thank you for your time.

Best,
Quinton Evans
PROWL academic capstone

## Technical details to include or supply on request

- Dataset: [BodyMaps/PanTSMini, pinned revision](https://huggingface.co/datasets/BodyMaps/PanTSMini/tree/3b1cd61108116b58ea5c1ddb3512c1847d965f96).
- [Dataset card reviewed](https://huggingface.co/datasets/BodyMaps/PanTSMini/blob/3b1cd61108116b58ea5c1ddb3512c1847d965f96/README.md).
- [GitHub license reviewed](https://github.com/MrGiovanni/PanTS/blob/243bef3075d2ab556eae374846e3ddfbc9f4c309/LICENSE).
- Case 2 CT SHA-256: `d9c23ce3de221bca3fde6b3dfa1b749964a3e95c7d914fbd6b29974eed1454a4`.
- Case 266 CT SHA-256: `ae4b95e088ac5a443baa1ae51da0f3eba252d68e7448b3fcdb3d78a2c8c4dfd3`.

## Internal follow-through — not part of the email

Based on the retained [unit investigation](UNIT-EVIDENCE-INVESTIGATION-2026-09-28.md)
and [source-use review](PANTS-SOURCE-USE-REVIEW-2026-09-28.md). This drafting task did
not reopen source data or recheck live publisher notices. The email deliberately
identifies the pinned versions we reviewed.

After sending, record date/channel and retain the reply with its release applicability.
Publisher clarification is evidence for a reviewed policy or use decision; it does not
automatically rewrite headers, clear all annotations, or authorize a training run.
If there is no answer, keep unresolved cases held and continue qualification of other
candidates. The license question remains separate from physical-unit qualification.
