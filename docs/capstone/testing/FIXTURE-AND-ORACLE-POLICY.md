# Test fixture and independent oracle policy

**Status:** Approved design; implementation remains gated  
**Decisions:** P09-05 through P09-08 and P09-13 through P09-15  
**Last reviewed:** 2026-09-09

## Fixture classes

| Class | Git | Purpose | Identity |
|---|:---:|---|---|
| Hand-authored JSON/CSV/YAML control | Yes | Contracts, mappings, identities, metrics, errors | File/content hash |
| Generated arrays/tiny NIfTI | Yes when safely generated | Geometry, labels, sampling, components, affine round trip | Recipe plus content hash |
| UI fixture packages/assets | Yes when synthetic/licensed | States, adapters, evidence, review persistence | Package/schema/content hashes |
| Retrieval control passages/questions | Yes when authored/publicly permitted | Rights, ranking, recall/MRR, citation/refusal | Corpus/question version |
| Local real imaging | No | Layout, headers, geometry, overlay, performance | Root alias + source snapshot + manifest hash |
| Local permitted article text | No unless exact release rights allow | Parser/index realism | Corpus/document/rights record |
| Checkpoint/model artifact | Usually no | Loading, MPS inference, release verification | Model/run/content hashes |
| Manual/stakeholder material | Only de-identified allowed records | Visual/UX/claim verification | Build/fixture/session identity |

## Generation rules

- Fixture generation is deterministic and records its seed/recipe.
- Tiny spatial fixtures use known voxel coordinates, affine, spacing, and world landmarks.
- Include asymmetric shapes so flips, swaps, and transposes are observable.
- Include positive, negative, empty, invalid, boundary, and multi-component cases.
- Generated outputs used as golden values are reviewed and committed; tests do not regenerate
  expected values using production code.
- Fixture updates are versioned and explain which contract or oracle changed.

## Metric goldens

The minimum set covers:

- perfect/zero/partial overlap;
- empty prediction with positive reference;
- negative reference with empty and non-empty prediction;
- completed versus failed/abstained study denominators;
- multiple lesions with correct, missed, extra, split, merge, and tie matching;
- sensitivity/specificity at multiple operating thresholds;
- Wilson intervals at small counts;
- clustered subject/study bootstrap behavior;
- paired improvement with gains/losses across the same cases;
- ignored/unknown target status and explicitly ineligible cases.

Each expected result includes the handwritten calculation or an independent reference script/library
whose identity is distinct from production.

## Spatial goldens

- Non-identity affine with anisotropic spacing.
- LPS/RAS orientation-sensitive landmarks.
- Odd/even shapes and padding on different sides.
- ROI touching each border.
- Scale-to-fit case with all axes different.
- Forward/inverse probability resampling before discretization.
- One-voxel lesion and multiple separated lesions.
- Invalid affine, mismatched grids, NaN/Inf intensity, and unknown label.

Tests state whether equality is voxel exact, nearest-neighbor label exact, landmark/world tolerance,
or interpolation tolerance.

## Retrieval goldens

- Exact terminology found by lexical retrieval.
- Semantic paraphrase intended for dense retrieval.
- Duplicate passages from one source.
- Rights-filtered source that ranks highly but cannot display full text.
- Correction/retraction notice.
- Answerable, partially answerable, insufficient, conflicting, diagnostic, treatment, and adversarial
  question.
- Claim with correct citation, irrelevant citation, missing citation, and citation outside retrieved
  set.

The 60-question Plan 07 set is evaluation evidence, not the only unit fixture. Small authored rank
lists provide exact recall/MRR oracles.

## Review/UI goldens

Use Plan 08 UI-F01 through UI-F18, including reference-free operation, failure, stale version,
evidence refusal, idempotent review append, and browser-only export-not-recorded state.

## Protected-data controls

- Fixture scan rejects absolute paths, recognizable source IDs where not explicitly allowed, large
  binary files, NIfTI/DICOM extensions outside approved generated fixture paths, secrets, and article
  bodies outside permitted test material.
- GitHub CI never resolves local root aliases.
- Local-real manifests contain source-scoped IDs/hashes, not copied data.
- Failure output and screenshots are reviewed for identifiers before release/sharing.
- Test notes follow the same no-patient/no-restricted-text rule as runtime logs.

## Oracle review rule

When production and golden disagree, neither wins by default. Reconstruct the input, contract,
convention, and independent calculation. Until resolved, the relevant gate is blocked and the
disagreement is evidence—not an invitation to choose the nicer result.
