# UI / Business Layer Design

**Living doc.** The front-end a user actually touches. Framing: radiologist / imaging-annotator **annotation-assist** + **CADe** presentation ("there could be a tumor here"). Not a diagnostic device — a human accepts / edits / rejects.

---

## 1. Framework

**Streamlit.** Single-page app, Python-native (no JS build), fast to stand up. Heavy 3D rendering delegated to plotly / optional WebGL components.

## 2. The three things the user sees

The page tells one story, top to bottom:

1. **CADe summary panel** — the headline. "Possible lesion detected · head of pancreas · ~1.8 cm (volume mm³) · confidence 0.7" or "No lesion detected." Plus the honest disclaimer banner: *segmentation tool, not a diagnosis; a clinician decides.*
2. **3D render — "what we found"** — a rotatable 3D model of the pancreas (translucent) with the lesion (solid red) sitting inside it. Built by running **marching cubes** (`skimage.measure.marching_cubes`) on the **masks** (not the raw CT) → plotly `Mesh3d`. Cheap because it meshes the small segmentation, not a 300 MB volume.
3. **Tri-planar slice viewer** — axial / coronal / sagittal panes, a slider to scroll, pancreas (green) + lesion (red) overlays with a toggle, and window/level control. This is how radiologists actually read, and it always works.

## 3. Tiers of 3D visualization

| Tier | Approach | Cost | Status |
|------|----------|------|--------|
| 1 | Tri-planar slices + mask overlays | Cheap | **Core** |
| 2 | Marching-cubes mesh of masks → plotly `Mesh3d` (rotatable organ + tumor) | Cheap (meshes masks only) | **Core "wow"** |
| 3 | Volumetric render (CT + overlays) via **NiiVue** (WebGL) or **stpyvista** (VTK) | Heavier | Stretch |

Optional polish: a **confidence / probability heatmap** overlay on the slices, so the user sees *where* the model is unsure.

## 4. Inputs & the accept/edit/reject loop

- **Load a case** from the test set (dropdown over the manifest) or **upload a NIfTI**.
- Run inference → display results.
- **Export the predicted mask (NIfTI)** so the user can open it in a real tool (e.g. 3D Slicer) and edit — this is the actual accept/correct/reject action the framing promises.

## 5. Inference handling (performance reality)

Sliding-window inference on MPS is slow, so the demo **pre-computes predictions for a set of showcase cases** and loads them instantly; live upload is supported but shows a progress spinner and a wait. This keeps the demo snappy for the pitch/presentation while still proving the end-to-end path works.

## 6. Layout sketch

```
┌────────────────────────────────────────────┐
│  ⚠ Segmentation tool — not a diagnosis      │
│  CADe summary: possible lesion · location · │
│                volume · confidence          │
├──────────────────────┬─────────────────────┤
│   3D mesh (rotatable) │  Case picker /      │
│   pancreas + lesion   │  upload · export    │
├──────────────────────┴─────────────────────┤
│  Axial   |   Coronal   |   Sagittal         │
│  [slice slider]  [overlay toggle] [W/L]     │
└────────────────────────────────────────────┘
```

## 7. Libraries

- `streamlit`, `plotly` (Mesh3d + slice display), `scikit-image` (marching_cubes), `nibabel` (NIfTI I/O), `monai` (sliding-window inference), `numpy`.
- Optional stretch: `niivue` (WebGL viewer), `stpyvista` (VTK).

## 8. Open questions

- Live inference vs precomputed-only for the demo (lean precomputed + optional live).
- Handling an uploaded scan with an unexpected field of view / spacing (run full preprocessing first).
- Whether to ship the 3D mesh as a saved interactive HTML artifact (also useful for MLflow demo runs).
- How much editing to support in-app vs. export-to-Slicer (default: export, since real annotation tools already exist).
