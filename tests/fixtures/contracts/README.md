# Synthetic contract controls

These hand-authored records contain no source data, real reviews, or model output. Repeated hashes
are shape placeholders, not computed artifact identities. Referenced files do not exist and must not
be resolved by schema tests. `cohort.synthetic.json` describes two imaginary members; it does not
establish a registered cohort or verify membership/count/hash consistency.

The review fixture deliberately uses `edit_required` with no corrected mask: a correction request
does not promise that browser voxel editing exists. Tests also validate the existing explicitly
synthetic examples in `docs/capstone/contracts/examples/` without reading any referenced images.

Negative tests change one field or remove one required value after checking the positive control.
Expected rejection comes from the approved contract, not from a production serializer. Cross-record
patient overlap, true content/derivation hashes, cohort ancestry, durable review writing, and
static/API parity need application tests when their implementations exist. No Plan 04 workflow
implementation or run-manifest test is added before the required coding authorization.
