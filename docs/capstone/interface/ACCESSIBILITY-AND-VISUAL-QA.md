# Accessibility, responsiveness, and visual QA

**Status:** Approved Plan 08 boundary; executable tooling belongs to Plan 09  
**Decision:** P08-17 and P08-18  
**Last reviewed:** 2026-09-09

## Target

Use WCAG 2.2 AA as the target for ordinary interface content and controls. The NiiVue canvas has
interaction/semantic limitations, so every critical workflow action must also have named controls and
textual state outside the canvas. Passing an automated scanner alone is not conformance evidence.

## Keyboard task

A reviewer must be able to:

1. open the case list and choose a study;
2. inspect package/warning/measurement text;
3. choose 2D plane/slice and prediction/reference modes using named controls;
4. request one structured evidence question and inspect citation/refusal;
5. choose action/reasons/note;
6. confirm, receive persistence status, reopen history, and revise;
7. escape every drawer, popover, dialog, and viewer focus region.

Canvas rotation and direct mesh selection are enhancements; they are not the only path to the task.

## Control requirements

- Native button/link/form semantics wherever possible.
- Unique accessible names that include anatomy/source where ambiguity exists.
- `aria-pressed`, selected tab, expanded, invalid, and disabled states match visual state.
- Visible focus and logical DOM/tab order.
- Focus moves into a modal confirmation and returns to its invoker on close.
- No positive/negative, source, warning, or selection state conveyed by color alone.
- Status announcements are concise and do not chatter during slice movement.
- Error summary identifies the field and moves/focuses predictably.
- Reduced-motion preference disables decorative motion and nonessential scanning effects.

## Viewer requirements

- Text outside the canvas names current study, plane, slice, evidence source, focus, and selected object.
- Plane, slice, zoom/reset, source, anatomy, and layer functions have conventional controls.
- Viewer errors use a visible alert and retry path.
- CT/mask alignment is visually checked in all three planes.
- 3D meshes are described as derived visualizations; they do not imply metric resolution.
- Reference assets are not loaded/activated early in validation/demo fixtures when reveal is required.

## Responsive matrix

| View | Required behavior |
|---|---|
| 1440×900 | Full desktop workspace; viewer dominant; study drawer available |
| 1280×720 | Core controls, warnings, evidence, and review action remain visible/reachable without overlap |
| 1024-pixel width | Drawer/panels collapse or stack; viewer and review task remain operable |
| 200% zoom | No clipped warning, confirmation, reason option, evidence state, or persistence receipt |

Mobile phone optimization is not committed for the single-user research workstation.

## Automated candidate checks

Plan 09 should evaluate a minimal combination of:

- reducer/adapter and component behavior tests using user-visible roles/labels;
- one Playwright critical flow in a real browser;
- axe integration on the initial, prediction, evidence, review, and failure states;
- screenshot comparison only for a few stable layouts, not every NiiVue frame.

Automated accessibility checks catch common defects but do not replace keyboard, zoom, contrast,
canvas, or stakeholder evaluation.

## Manual QA record

Record tester, date, browser/version, viewport, zoom, input method, fixture IDs, pass/fail, screenshot,
and issue link for:

- tab order and visible focus;
- no keyboard trap;
- labels/states announced coherently;
- non-color source/error distinction;
- 2D/3D CT-mask alignment;
- popover/dialog focus restoration;
- long warning/citation/note wrapping;
- offline, invalid-package, viewer-error, refusal, and write-failure states;
- repeated case/mode switching without stale content.

## References

- [WCAG 2.2](https://www.w3.org/TR/wcag/)
- [W3C accessibility principles](https://www.w3.org/WAI/fundamentals/accessibility-principles/)
- [Playwright accessibility testing](https://playwright.dev/docs/accessibility-testing)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
