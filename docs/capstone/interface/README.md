# Plan 08 interface design package

**Status:** Approved Plan 08 design baseline; implementation dependencies remain  
**Owner:** Quinton Evans  
**Last reviewed:** 2026-09-09

## Purpose

This package turns the existing React/NiiVue application into an implementation-ready plan for the
PROWL review workstation. It separates what already works from what must change for autonomous
case packages, grounded evidence, and durable review events.

## Package map

| Document | Question answered |
|---|---|
| [`CURRENT-STATE-INVENTORY.md`](CURRENT-STATE-INVENTORY.md) | What exists, what is reusable, and what is historical? |
| [`WORKFLOW-AND-STATE-MODEL.md`](WORKFLOW-AND-STATE-MODEL.md) | What does the user do and how do states change? |
| [`DATA-ADAPTERS-AND-PERSISTENCE.md`](DATA-ADAPTERS-AND-PERSISTENCE.md) | How do static/FastAPI packages and append-only reviews behave? |
| [`EVIDENCE-AND-TRUST.md`](EVIDENCE-AND-TRUST.md) | How are prediction, reference, measurement, and literature kept distinct? |
| [`ACCESSIBILITY-AND-VISUAL-QA.md`](ACCESSIBILITY-AND-VISUAL-QA.md) | What does operable, responsive, and visually honest mean? |
| [`FIXTURES-AND-ACCEPTANCE.md`](FIXTURES-AND-ACCEPTANCE.md) | Which cases and checks prove G7? |

The governing plan is [`../implementation/08-review-interface.md`](../implementation/08-review-interface.md).

## Non-negotiable rules

1. Extend the current application; do not restart it.
2. Render only validated artifacts through one internal view model.
3. Static and FastAPI transport cannot alter scientific values.
4. Operational review works without reference annotations.
5. Reference and retrospective metrics remain a separately labeled validation mode.
6. Missing or failed content never becomes a zero, healthy case, or blank successful contour.
7. Evidence is structured and cite-or-refuse; it never becomes a clinical chatbot.
8. Review success requires a durable append receipt, not `localStorage`.
9. Every review remains tied to exact package and prediction identity.
10. Browser contour editing, multi-user behavior, and clinical deployment remain out of scope.

## Decision boundary

Quinton approved P08-01 through P08-18 on 2026-09-09. The workflow and testable behavior are locked,
but code remains gated until Plans 09/10 complete the testing and operational contracts. D-208 may
remain open only if the UI uses neutral ordering and does not display a placeholder reviewer score.
