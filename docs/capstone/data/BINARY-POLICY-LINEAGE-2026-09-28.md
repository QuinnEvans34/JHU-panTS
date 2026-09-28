# Approved binary policy lineage verification

September 28, 2026. Bounded Codex data task authorized by Quinton after context handoff.
No source-drive access, decoding run, package publication or eligibility change.

## Finding and change

The annotation-v2 schema already represents mapping status, policy identity, a policy
hash and a content-addressed approval reference. No schema change was needed.
The existing structural validator intentionally does not resolve evidence. Inspection
found no separate verifier binding the approved D-259 policy to reviewed evidence bytes.

`src/data/annotation_contract_v2.py::validate_approved_binary_lineage` now checks a
structurally valid record against caller-supplied retained approval/implementation bytes
and independently reviewed SHA-256 pins. It requires the PanTS approved policy ID,
approved status, absolute tolerance exactly 1e-6, relative tolerance zero, matching
approval hash/byte count and matching implementation hash. For this policy,
`mapping.policy_sha256` identifies the exact `src/data/binary_label_policy.py` bytes.
The approval reference separately identifies the decision document.

This verifier performs no writes or decoding and returns no eligibility decision.
It is not automatically called by the existing diagnostic assembler or publisher;
future publication of approved mappings must explicitly call it with retained evidence
and trusted pins. Generic structural validation remains permissive about other policy
identities for compatibility, and historical candidate records remain replayable.

## Trust boundary and reviewed evidence

The trusted pins must come from independently reviewed publication inputs, never from
the annotation being checked. Matching a record to its own self-supplied evidence is
not authorization. The function verifies byte identity and the narrow policy semantics;
it cannot authenticate a human approval, adjudicate its source/purpose applicability,
or establish that arbitrary caller-supplied code was reviewed. The publisher must retain
these reviewed inputs and resolve root aliases safely. No production resolver is added.

The test using actual repository evidence pins these reviewed versions explicitly:

| Evidence | Bytes | SHA-256 |
|---|---:|---|
| `BINARY-DECODING-APPROVAL-2026-09-28.md` | 2217 | `3929e0e359d1aa1d4a5cc5a0066285699821ed648bbe87bfdcbc2bc2bead6de3` |
| `src/data/binary_label_policy.py` | 1666 | `ecdbe3e887c4b791f1079e81dcb22d804fda2e8c4b661c341ae422d90e6f4407` |

Changing either evidence file requires reviewing and updating the corresponding test
pin, not automatically accepting its new hash. The test constructs a synthetic
quarantined annotation; it does not publish a revised real-data record.

## Verification

- 25 added tests cover approved/candidate identity, missing evidence, wrong hash/size,
  modified evidence (including internally consistent substitutions), exact tolerance,
  source scope, unchanged input records and continued quarantine for empty/nonempty masks.
- Focused annotation, decoder and manifest-v2 suite: **99 passed**.
- Full native suite: **578 passed**, two existing upstream torch.jit warnings, using
  `env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider`.
- Existing five-study package: all **25 recorded file hashes** rechecked; replay from
  persisted assembly inputs reproduced all five manifest output files byte-for-byte.
  All ten annotations still have null mapping, quarantined status and empty allowed uses.
- Captured schema, decoder and diagnostic converter/publisher hashes remained unchanged.
  Claude planning hashes matched at the package check; a later final comparison detected
  concurrent changes to Claude's `SCOPE.md` and `PHASES.md`. This task did not edit them.
  Scoped before/after diffs reviewed. No source data read.
- Task files pass a direct trailing-whitespace check. Repository-wide `git diff --check`
  reports existing trailing whitespace on lines 3–4 of `DATA-ACQUISITION-QUEUE.md`, which
  this task did not edit; no unrelated cleanup performed.

The old package remains
`outputs/prowl/manifest-v2-slice-685cfdbd-ae54-4508-be6f-5b9267197bd9/`.
Its historical code fingerprint remains historical; current replay compatibility does
not replace that fingerprint or reinterpret its mapping status. No new package created.

## Purpose dispositions still required

| Evidence | Current treatment | What remains before use |
|---|---|---|
| Case 78: hip/pelvic coverage and empty pancreas | Preserve original membership and quarantine; not a trusted pancreas-present target or disease-negative | Formal purpose-specific coverage disposition; any out-of-coverage robustness use needs separate registration |
| Cases 2 and 266: unresolved physical units | Do not infer mm from plausible numeric spacing | Independent unit evidence or explicit unresolved/excluded disposition for geometry-dependent purposes |
| Study-as-subject grouping | Retain `unverified_unique` fallback | Protected-cohort identity/duplicate review and honest residual-risk disclosure |
| Source annotation protocol | Publisher claims are not per-file project verification | Release applicability and structure-specific provenance review |
| Source-use terms | Existing restrictions/holds remain | Separate local research and public-release dispositions; this task makes no rights decision |
| Approved binary decoding | Policy linkage is now checkable | Qualified loading, geometry, provenance and per-purpose use decisions before a consumer may use labels |

Evidence remains in the source-use, spatial-units and case-78 reviews linked by the
current checkpoint. No issue was resolved or annotation promoted here. Full G1 and
the first-experiment R0–R8 gates remain open.

Next: discuss the purpose-specific dispositions with Quinton, then agree the exact
evidence/qualification scope needed to move towards frozen train-role cohorts. No
additional serialization layer is justified by this task. Claude handback review is
being handled in Quinton's older conversation and is not duplicated here.
