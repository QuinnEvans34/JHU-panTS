# Interface evidence and trust boundaries

**Status:** Approved Plan 08 design baseline  
**Decisions:** P08-04, P08-07 through P08-12  
**Last reviewed:** 2026-09-09

## Evidence classes

| Evidence | Source | UI label | May influence autonomous inference? |
|---|---|---|---|
| CT | Immutable source study | CT image | Input only |
| Raw model mask/probability | Exact prediction version | Model prediction | It is the output |
| Derived display/processing | Exact derived policy | Derived model display | No hidden replacement of raw |
| Measurements | Prediction/measurement artifact | Model-derived measurement | No recomputation in UI |
| Reference annotation | Evaluation/demo package only | Reference annotation | Never |
| Discrepancy/Dice | Evaluation artifact | Retrospective evaluation | Never |
| Literature passage/claim | Versioned evidence response | Literature evidence | Never changes prediction |
| Human review | Append-only event | Reviewer decision | Downstream record only |

## Visual separation

- Every view names evidence source and anatomy in text.
- Prediction and reference never rely on green/blue color alone.
- A derived mesh is labeled as a display representation; its smoothing does not change metrics.
- Retrospective Dice is visually grouped with reference/discrepancy, not model measurements.
- Raw/derived policy identity is available in details.
- Warnings remain visible when panels collapse or view mode changes.

## Structured question control

The assistant begins with five approved intent families:

1. delineation/contour considerations;
2. measurement interpretation/reproducibility;
3. pancreas anatomy/subregion terminology;
4. known AI segmentation limitations;
5. annotation/review workflow.

An intent selects a visible, versioned question template. Allowed structured finding fields from
Plan 07 may fill coarse non-identifying context. There is no open chat transcript and no patient
report/image/mask content in the request.

Out-of-scope examples—diagnosis, lesion subtype, prognosis, treatment, personal medical advice—return
the defined refusal without invoking a general-answer path.

## Evidence response presentation

### Sufficient

- concise atomic claims;
- claim-to-passage links;
- visible source title/year/identifier;
- passage text and stable locator;
- limitations and retrieval date/version in details.

### Insufficient

- direct statement that the indexed evidence was insufficient;
- optional ranked passages if they passed display-rights/filter rules;
- no synthesized answer.

### Limited/conflicting

- explicit limitation/conflict state;
- supported claims only;
- source-level separation rather than false consensus.

### Failed/unavailable

- operational reason safe for display;
- retry if appropriate;
- imaging and review controls remain available.

## Citation behavior

- Clicking a citation focuses the exact stored passage before any external link.
- The interface verifies every claim citation points into the response's retrieved passage set.
- External links use recorded persistent identifiers/allowed URLs and open separately.
- A missing passage or mismatched corpus/index/response identity invalidates the response display.
- Full restricted article text is not bundled into a distributable UI package.

## Wording boundary

Prefer:

- `possible lesion flagged by the model`;
- `model-derived measurement`;
- `review priority` or `ordering score` only after D-208;
- `reference annotation`;
- `literature evidence`;
- `evidence unavailable` or `the indexed sources did not support an answer`.

Avoid:

- `cancer detected`, `malignant`, `diagnosis`, `confirmed`, or `patient risk`;
- `ground truth` in operational review;
- confidence labels that imply calibrated probability when calibration is absent;
- `saved` before a durable receipt;
- `AI recommendation` for literature retrieval.

All user-visible copy receives a claim review before G7.
