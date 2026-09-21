# Current-state interface inventory

**Status:** Approved inventory; scoped synthetic build/test baseline captured; full visual/real-viewer baseline pending  
**Last reviewed:** 2026-09-09

## Current application

September 20 update: unchanged build, 18 UI unit/component tests, and one synthetic Chromium
control flow passed. See [the evidence and limits](../testing/UI-FOUNDATION-2026-09-20.md).
The table and checklist below preserve the September 9 inventory; no full checklist completion is
implied by the new stub-viewer checks. The automated commands now exist in `ui/package.json`.

The existing `ui/` application is a Vite/React 18 single-page application with NiiVue, Lucide icons,
and custom CSS. It loads prepared cases from `ui/public/cases/`, optionally calls a local FastAPI
service, and presents CT/prediction/reference/overlap views in a viewer-first workspace.

## Reusable assets

| Asset | Current value | Capstone treatment |
|---|---|---|
| `ReviewWorkspace.jsx` | Mature viewer-first layout and interaction controls | Preserve layout; replace data/action boundaries incrementally |
| `NiivueViewer.jsx` | 2D/3D NIfTI/mesh display and interaction | Preserve behind a small viewer adapter and regression fixtures |
| `reviewState.js` | Explicit presentation reducer | Keep presentation concerns; remove package/job/review persistence from visual state |
| `viewerLayers.js` | Prediction/reference/difference visibility rules | Preserve after mapping canonical source/anatomy roles |
| `index.css` | Complete dark visual system and responsive rules | Reuse; change only for new workflow, accessibility, and stakeholder-backed needs |
| Prepared cases | Positive, true-negative, false-positive, and library cases | Preserve as historical visual fixtures; do not call them capstone-valid until adapted |
| Progressive reveal | Prediction-first/reference-later interaction | Preserve only in `validation_demo` packages |
| Build pipeline | `npm run build` succeeds by design | Baseline actual result must be captured under Plan 09 |

## Historical boundaries to replace

| Current behavior | Problem | Required boundary |
|---|---|---|
| `results.json` drives components | Mixed prediction/reference/evaluation/demo shape | Versioned case package → validated internal view model |
| `API_BASE` is hard-coded | Transport/environment leaks into components | Configured repository/adapter capability |
| `/predict` result has legacy fields | Live and static meaning can diverge | Same case-package contract after workflow publication |
| Review status in `localStorage` | Not append-only, versioned, or durable scientific evidence | Local writer plus immutable event/receipt/history |
| `reviewed` and `discussion` actions | Do not match approved accept/edit/reject | Exact review-event semantics and reason codes |
| Curated case prose in `App.jsx` | Hard-coded interpretation can drift from artifacts | Fixture metadata/presentation copy with provenance and claim review |
| Prediction/reference values coexist in one record | Reference may become available too early | Explicit operational versus validation/demo capability |
| Dice/validation narratives dominate cases | Ordinary workflow does not have ground truth | Reference-free operational-review acceptance fixture |
| App/package still use `PanTS CADe`/`pants-*` names | Historical branding and storage identifiers | PROWL naming in a bounded migration; do not rename science IDs |
| No test script in `package.json` | UI changes cannot prove workflow/regression | Plan 09 test command plus critical browser path |

## Baseline capture checklist

Before the first UI behavior change:

- [ ] Record Node/npm/browser/macOS versions and dependency lock hash.
- [ ] Run install/build from the documented environment and retain output.
- [ ] Capture 1440×900, 1280×720, 1024-wide, and 200%-zoom screenshots.
- [ ] Record keyboard tab order and current focus visibility.
- [ ] Open one positive, negative, and false-positive prepared case in 2D and 3D.
- [ ] Exercise CT/prediction/reference/overlap, anatomy focus, source focus, layer visibility, reset,
  case switching, and offline behavior.
- [ ] Record representative file sizes and time to first usable CT/viewer.
- [ ] Record browser console errors and failed network requests.
- [ ] Hash the current case manifest and selected fixture assets.

The baseline is evidence for preservation, not an endorsement of historical scientific contracts.

## Refactor seams

The safest order is:

1. add tests around reducer and visible behavior;
2. introduce interfaces/repositories beside existing loaders;
3. adapt one canonical package into an internal view model;
4. render the canonical fixture with existing components;
5. migrate one panel at a time;
6. add evidence and review components;
7. remove old domain-field access only after parity checks pass.

Do not combine the data-contract migration with a visual redesign or NiiVue replacement.
