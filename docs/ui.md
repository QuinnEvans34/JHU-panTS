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
3. **NiiVue viewer** — the centerpiece is a **rotatable 3D view** (decided 2026-07-15, this is the hero, not 2D slice-scrolling): the CT volume rendered in 3D with the pancreas (green) + lesion (red) **surface meshes** overlaid, navigated by orbit plus **clip planes through all three axes** (move through space while staying in 3D). Controls: layer toggles, opacity, and a prediction-vs-ground-truth toggle (the wrong-prediction case shows both in two colors). Optional 2D planes as a secondary detail inset if wanted.
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

Surface **meshes** (marching cubes → `.obj`, world-aligned) for the crisp 3D organ+tumor render — pancreas + lesion, for both prediction and ground truth.

**Producer built Week 3 (2026-07-15):** `scripts/export_case.py` writes all of the above per case (CT, gt/pred masks, meshes, and the `results.json` entry) in the whole-box model's input space, so the volume and meshes align. `--list` mode scans the val set to help pick the healthy / tumor / wrong-prediction showcase trio. This is the reusable spine: the same files feed a static figure now and the Week 5 NiiVue app.

## 6. Tiers

| Tier | Scope | Status |
|------|-------|--------|
| Core | Data exporter (`export_case.py`) → CT + masks + meshes + `results.json` | **Built Week 3** |
| Core | Static React + NiiVue: layered 3D (CT volume + surface mesh), orbit + clip planes | Week 5 target |
| Stretch | Live inference via FastAPI backend | Capstone |
| Stretch | Confidence heatmap overlay (probability map as a NiiVue layer) | Capstone |
| Fallback | The `peek_case.py` PNGs / a barebones viewer | Always available |

## 7. Timing & risk

Build in **Week 5**, after the model is trained and evaluated. The pipeline is designed so the UI just reads saved predictions, so a rough patch on the frontend can't block the graded ML work. The `scripts/peek_case.py` overlays already exist as a zero-risk fallback if the React build runs short on time.

## 8. Libraries

- `react`, `vite`, `tailwindcss`, `shadcn/ui`, `@niivue/niivue`.
- Stretch (live): `fastapi`, `uvicorn`, plus the existing MONAI/PyTorch inference code.

## 9. Open questions

- ~~NiiVue overlay styling: label volume vs. surface mesh for 3D~~ **RESOLVED (2026-07-15):** layered 3D — CT volume render + surface mesh overlay (pancreas translucent, lesion solid). Meshes precomputed via marching cubes in `scripts/export_case.py`. One thing to verify when first loaded: mesh-to-volume alignment in NiiVue (the world affine from the MONAI MetaTensor should place them together; if a flip/offset appears, adjust the affine handling in `get_affine`).
- Confidence heatmap: render the probability map as a NiiVue overlay?
- Hosting for the static demo (Vercel/Netlify/GitHub Pages).
- How many showcase cases to precompute (mix of tumor-positive and healthy).

---

## Designing for the non-technical audience (radiologists)

**The governing principle (from the professor, 2026-07-08):** complexity from the audience's own world is welcome; complexity from ours is not. A radiologist reasons fluently in 3D anatomy, millimeters, and organ sub-regions, so those are fair game and even expected. Dice, specificity, loss, and thresholds are complexity from the ML world, and to a clinician they are noise at best and misleading at worst. Every model output must be translated into clinical language and imagery before it reaches this UI.

**Show (the clinician's language):**

- The scan with the proposed outline overlaid, in the three standard planes plus a rotatable 3D view. The image is the interface; the outline is a suggestion drawn on it. The 3D reconstruction is genuinely complex, but it lives in their domain, so it communicates size and location instantly without a single number.
- Lesion size in millimeters or centimeters, the unit they already use clinically, not voxel counts.
- Anatomical location in words: head, body, or tail of the pancreas, and proximity to nearby structures.
- A simple, qualitative suspicion level rather than a raw probability. A short band like lower / moderate / higher, or a visual cue such as overlay intensity, reads instantly. If a bare number ever appears, it needs a familiar anchor, never a naked decimal.
- Human-in-the-loop controls: accept, edit, or reject the contour. The radiologist stays in charge; nothing is auto-committed or auto-hidden. This is annotation-assist, not automation.

**Hide from the clinical view (belongs elsewhere):**

- Dice, sensitivity, specificity, the sensitivity-specificity tradeoff, loss, probability thresholds, voxel counts, model confidence as a bare decimal. None of these help a clinician decide, and a big number they cannot interpret erodes trust.

**Two audiences, two surfaces.** The ML metrics are not thrown away, they are moved. Dice, sensitivity, specificity, and the tradeoff curves belong in a separate validation or performance view (and in the written report) aimed at the technical and regulatory audience who need to judge whether the tool is trustworthy. The clinical UI and the validation report are different products for different readers, and mixing them serves neither.

**Framing and safety.** The tool prompts a second look, it does not diagnose. Flags must be easy to dismiss, the disclaimer stays visible, and the language stays suggestive ("possible finding, please review") rather than declarative. The goal is to save the radiologist time on the outline while leaving every judgment to them.

**Design test.** Before any element ships to the clinical view, ask: would this number or control mean something to a radiologist who has never taken a statistics course? If not, either translate it into anatomy, size, and location, or move it to the validation surface.
