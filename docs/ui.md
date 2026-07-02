# UI / Business Layer Design

**Living doc.** The front-end a user actually touches. Framing: radiologist / imaging-annotator **annotation-assist** + **CADe** presentation ("there could be a tumor here"). Not a diagnostic device — a human accepts / edits / rejects.

> **Stack decision (2026-07-01):** **React + NiiVue** (dropped Streamlit — too prototype-looking). Build in **Week 5**, after the model works, from *saved predictions* — so UI effort can never sink the ML core.

---

## 1. Stack

- **React** (Vite) — the app shell, clean and fully custom.
- **NiiVue** (`@niivue/niivue`) — a WebGL medical-image viewer built for **NIfTI** (our exact format): tri-planar slices, 3D volume rendering, colored mask overlays, opacity/colormap control — all out of the box. This is the piece that makes the React path realistic; we don't hand-roll volume rendering.
- **Tailwind + shadcn/ui** — the surrounding UI (CADe panel, case picker, controls, buttons) in a clean clinical dark theme.

## 2. Architecture — static first, backend optional

**The key move that keeps effort sane:** the UI is a *consumer of saved predictions*, not a live model host.

- **Core (static, no backend):** the training pipeline pre-computes predictions for a set of showcase cases → saved as **predicted-mask NIfTI** + a small **`results.json`** (per case: lesion present, location, volume mm³, confidence). NiiVue loads the CT + predicted mask from static files; React renders the panels from the JSON. Deploys anywhere (Vercel/Netlify), no server. Perfect for the presentation.
- **Stretch (live inference):** add a small **FastAPI** service — upload a scan → sliding-window inference (MONAI) → return the predicted mask + CADe JSON. Capstone-friendly; not required for the course.

This split is why the model pipeline must **write predictions to disk in a clean, documented format** (see §5) — the same discipline that makes the model submittable to JHU later.

## 3. What the user sees

One page, clinical dark theme, top to bottom:

1. **Disclaimer banner** — *segmentation tool, not a diagnosis; a clinician decides.*
2. **CADe summary panel** — the headline: "Possible lesion · head of pancreas · ~1.8 cm · confidence 0.7" or "No lesion detected."
3. **NiiVue viewer** — the centerpiece: tri-planar CT with pancreas (green) + lesion (red) overlays, scrollable slices, **and a 3D mode** (rotatable volume / organ-with-tumor). Layer toggles + opacity.
4. **Actions** — case picker, **export predicted mask (NIfTI)** for editing in a real tool (3D Slicer) — the accept / edit / reject step.

## 4. Layout sketch

```
┌───────────────────────────────────────────────┐
│  ⚠ Segmentation tool — not a diagnosis          │
├──────────────────────────────┬──────────────────┤
│                              │  CADe summary     │
│      NiiVue viewer           │  • possible lesion│
│  (tri-planar + 3D, overlays) │  • location/volume│
│   [2D/3D] [layers] [opacity] │  • confidence     │
│                              │  Case: [picker ▾] │
│                              │  [Export mask]    │
└──────────────────────────────┴──────────────────┘
```

## 5. Data contract (UI ↔ pipeline)

The model side produces, per showcase case:

- `ct.nii.gz` (or a link to it) — the input volume.
- `pred.nii.gz` — predicted mask (0 bg / 1 pancreas / 2 lesion).
- an entry in `results.json`: `{case_id, has_lesion, location, lesion_volume_mm3, confidence, dice_pancreas?, dice_lesion?}`.

Optional: a surface **mesh** (marching cubes → `.mz3`/`.obj`) for a crisp 3D organ+tumor render in NiiVue.

## 6. Tiers

| Tier | Scope | Status |
|------|-------|--------|
| Core | Static React + NiiVue over precomputed predictions | Week 5 target |
| Stretch | Live inference via FastAPI backend | Capstone |
| Stretch | Surface-mesh 3D render + confidence heatmap overlay | Capstone |
| Fallback | The `peek_case.py` PNGs / a barebones viewer | Always available |

## 7. Timing & risk

Build in **Week 5**, after the model is trained and evaluated. The pipeline is designed so the UI just reads saved predictions, so a rough patch on the frontend can't block the graded ML work. The `scripts/peek_case.py` overlays already exist as a zero-risk fallback if the React build runs short on time.

## 8. Libraries

- `react`, `vite`, `tailwindcss`, `shadcn/ui`, `@niivue/niivue`.
- Stretch (live): `fastapi`, `uvicorn`, plus the existing MONAI/PyTorch inference code.

## 9. Open questions

- NiiVue overlay styling: label volume overlay vs. surface mesh for the 3D view (start with the label volume; add mesh if time).
- Confidence heatmap: render the probability map as a NiiVue overlay?
- Hosting for the static demo (Vercel/Netlify/GitHub Pages).
- How many showcase cases to precompute (mix of tumor-positive and healthy).
