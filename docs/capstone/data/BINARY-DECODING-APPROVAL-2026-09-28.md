# Approved binary decoding rule

Approved by Quinton Evans in this task on September 28, 2026: "I approve this rule."
Decision ID: D-259. Approved policy ID: `pants-semantic-binary-atol1e-6-v1`.

- Input: nonempty 3D real numeric mask AFTER effective NIfTI slope/intercept scaling.
- Every voxel must be finite and within absolute 0.000001 of zero or one; relative
  tolerance is zero. Reject the whole input otherwise; no generic positivity or clipping.
- Output: a NEW uint8 binary array (background 0, foreground 1), preserving source bytes.
- Record the chosen policy identity, tolerance, voxel count, foreground count and number
  of values normalized. Existing implementation returns these fields.
- Empty foreground remains empty; it grants no disease label or annotation allowed use.

`src/data/binary_label_policy.py` now accepts the explicit approved policy ID. The historical
candidate ID remains supported for replay with unchanged behavior; it is not retroactively
renamed or treated as an approval record. New qualified consumers must name the approved ID.
Both identifiers use identical numeric semantics; neither is selected implicitly.

Approval is for the rule, not for a training launch, bulk rewrite, source eligibility,
canonical file publication, evaluated reference use, model initialization or redistribution.
The decoder still operates on a loaded array; bounded loading/memory qualification and
provenance, geometry, identity, rights and per-purpose eligibility remain required.
No dataset/trainer was wired to it. Existing manifests and prior evidence are unchanged.

Future v2 mapping records may reference this approval file (measured hash/size at publication)
and the exact implementation hash. Keep the declaration status separate from artifact
eligibility; publishing this decision alone does not resolve the other holds.

Verification: eight added approval/rejection tests; full native suite **553 passed**, two
existing upstream torch.jit warnings. Approved/candidate IDs produce identical arrays but
retain distinct recorded policy identity. Source-array preservation and continued rejection
of intermediate/nonfinite/raw stored values are tested. No training consumer was changed.
