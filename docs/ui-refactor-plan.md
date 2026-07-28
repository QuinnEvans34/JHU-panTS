# Review Workspace Interaction and Visual-Quality Refactor

**Status:** Implemented in the React Review workspace (2026-07-28)  
**Created:** 2026-07-28  
**Scope:** React Review workspace, NiiVue integration, and presentation meshes  
**Historical context:** `docs/ui.md` remains useful background, but this document governs the next UI refactor where the two disagree.

Implementation note: the viewer-first layout, explicit review reducer, persistent evidence modes, direct 2D/3D selection, focus/isolate treatments, stable NiiVue registries, upgraded surface materials, discrepancy assets, and responsive controls are now implemented. The authoritative NIfTI masks and metrics remain unchanged; presentation meshes are derived display assets.

---

## 0. Decision summary

The Review workspace will be refactored from a results dashboard with a medical viewer into a **viewer-first scientific evidence workspace**.

The scan and its anatomy will become the primary interface. The user will:

1. Open a clean CT.
2. Score it.
3. Inspect and directly select the model's pancreas or lesion.
4. Focus or isolate an anatomical structure.
5. Explicitly unlock the Johns Hopkins reference annotation.
6. Switch freely among CT, Prediction, Source of truth, and Overlap modes.
7. Inspect agreement, over-prediction, and missed reference regions in 2D and 3D.

The existing three curated cases keep their scientific role. Library cases retain the progressive reveal and never display the reference annotation before the user unlocks it.

The 3D visual treatment will also be upgraded. We will **not replace NiiVue immediately**. NiiVue already contains multiple suitable mesh shaders, object/depth picking, mutable mesh properties, atlas outlines, and custom shader support. We will first improve the exported surfaces and build a higher-quality NiiVue material/lighting treatment. A replacement or hybrid 3D renderer is a fallback only if a defined visual-quality spike shows that NiiVue cannot meet the target.

No manual pancreas or lesion outlining will be added. The interface remains a segmentation review and scientific comparison tool, not a diagnostic system or in-browser segmentation editor.

---

## 1. Product intent

### 1.1 What the interface should feel like

The interface should feel like an interactive scientific instrument:

- The medical image occupies most of the screen.
- Anatomy is directly selectable.
- Controls are compact, contextual, and reversible.
- The user can move between forms of evidence without rescoring or changing pages.
- Visual comparison explains the model's behavior spatially, not only numerically.
- The interface is polished enough for presentation without beautifying away real model errors.

### 1.2 What the interface should not feel like

It should not feel like:

- A dashboard with a viewer embedded inside it.
- A wall of permanent sliders and toggles.
- A one-way slideshow where each button appends new content.
- A collection of separate scientific views that lose the current camera or anatomical focus.
- A rendering demo whose visual polish implies more spatial resolution than the model actually produced.

### 1.3 Scientific framing

Use **Source of truth** in prominent UI labels for presentation continuity, with **Reference annotation** in explanatory copy or tooltips.

The Johns Hopkins annotation is the comparison reference; it is not presented as an infallible diagnosis. Prediction, reference, and discrepancy visuals must remain clearly labeled.

---

## 2. Current-state diagnosis

### 2.1 Interaction problems

- The viewer is mostly passive. The user manipulates controls around the anatomy instead of manipulating the anatomy itself.
- Prediction, source of truth, and overlap are treated as one-way reveal states rather than persistent evidence modes.
- The right panel is visually dense and gives secondary controls too much space.
- Layer visibility, anatomy focus, source focus, and workflow stage are represented by overlapping booleans rather than one clear interaction model.
- Changing sources, opacity, or anatomy visibility currently rebuilds the NiiVue scene. This creates unnecessary loading, flicker, camera resets, and a “settings panel” feeling.
- The scientific payoff appears in the side panel instead of being expressed primarily in the viewer.

### 2.2 3D visual-quality problems

The current pancreas does not look cheap because it is merely a very low-polygon mesh:

- Exported pancreas surfaces commonly contain approximately 7,000–16,000 vertices.
- The exporter already applies Gaussian pre-smoothing and 12 iterations of Taubin smoothing.
- Prediction surfaces are generated from the model's continuous probability field rather than only the hard argmax mask.

The more likely limitations are:

- The model/display source grid is 1.5 mm, which places a real ceiling on recoverable spatial detail.
- The current OBJ export does not explicitly write vertex normals.
- NiiVue uses its default Phong material because no mesh shader is selected.
- The pancreas is semitransparent so an internal lesion remains visible; ordinary alpha blending weakens its silhouette and can create depth-sorting artifacts.
- Dark surfaces lose their far edges against the dark viewer background.
- The faint CT volume can resemble a rectangular block rather than intentional anatomical context.
- Fixed lighting and camera framing do not adapt to the selected anatomy.
- There is no selected-object treatment, rim light, contour, or controlled depth cue.

### 2.3 What “higher definition” can honestly mean

We can produce a denser, smoother, better-shaded display surface. We cannot recover anatomical detail absent from the 1.5 mm probability/mask grid.

Any supersampling is display reconstruction, not improved model accuracy. NIfTI masks and reported metrics remain untouched.

---

## 3. Governing design principles

1. **The image is the interface.**
2. **Workflow unlocks evidence; evidence modes remain reversible.**
3. **Focus and visibility are different actions.**
4. **Direct selection and button-based selection must stay synchronized.**
5. **Context is reduced before it is removed.**
6. **Scientific errors remain visible.**
7. **Visual smoothing must not modify metrics or imply additional model resolution.**
8. **The reference annotation is never activated before explicit reveal on library cases.**
9. **Common actions stay visible; advanced controls move into a popover.**
10. **Color is never the only indicator of source, anatomy, selection, or error.**

---

## 4. Target workflow

### Stage 1 — Unmarked CT

- Load the CT with no prediction or reference layer.
- Keep the primary action obvious: **Analyze scan**.
- Permit ordinary CT navigation before scoring.
- Prediction, Source of truth, and Overlap modes are locked.
- The interface does not preload the reference into the active NiiVue scene.

### Stage 2 — Prediction review

After a successful score:

- Enter **Prediction** mode automatically.
- Show the prediction in 2D and 3D.
- Display the live scoring badge and CADe summary in a compact context strip.
- Unlock direct selection of predicted pancreas and lesion.
- Allow focus, isolate, show/hide, camera centering, and return to All.
- Show **Reveal source of truth** only after the user has had an opportunity to inspect the prediction.

### Stage 3 — Source-of-truth review

After explicit reveal:

- Unlock Source of truth and Overlap modes.
- Enter **Source of truth** mode automatically.
- Show the reference pancreas in blue and reference lesion in amber.
- Keep Prediction available as a one-click mode.
- Do not require another inference call.

### Stage 4 — Overlap and discrepancy review

- Enter Overlap mode from the persistent evidence selector.
- Show prediction and reference together.
- Allow anatomy focus: All, Pancreas, or Lesion.
- Allow source emphasis: Both, Prediction, Reference, or Difference.
- Keep Dice metrics in a compact in-view HUD.
- Provide explicit Agreement, Prediction only, and Reference only discrepancy views.
- Permit instant switching back to Prediction or Source of truth.

### Reset behavior

For an unmarked library case, **Reset / new scan** returns to Stage 1:

- Clear the live result.
- Remove prediction and reference from the active scene.
- Clear anatomy/source selection.
- Reset evidence mode to CT.
- Reset camera/crosshair and contextual measurements.

Resetting the camera alone remains a separate, non-destructive action.

---

## 5. Information architecture and layout

### 5.1 Desktop target

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ PanTS 00009005   Live · scored 11:52 · 0.5s        2D | 3D | Reset view │
├──────────────────────────────────────────────────────────────────────────┤
│       CT  |  Prediction  |  Source of truth 🔒  |  Overlap 🔒           │
├──────────────┬───────────────────────────────────────────────────────────┤
│ Studies      │                                                           │
│              │                    MAIN VIEWER                            │
│ Collapsible  │                                                           │
│ drawer       │       Click an anatomical structure to focus it           │
│              │                                                           │
├──────────────┴───────────────────────────────────────────────────────────┤
│ Focus: All | Pancreas | Lesion       Layers 👁       View settings ···   │
├──────────────────────────────────────────────────────────────────────────┤
│ Context: selected object, CADe summary, volume, confidence, or Dice HUD  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Layout changes

- Make the viewer the dominant surface.
- Convert the case rail into a collapsible study drawer.
- Remove the always-expanded right-side tool stack.
- Move the evidence selector directly above the viewer.
- Place anatomy focus controls directly below or inside the viewer.
- Use a compact bottom context strip for the selected object or current evidence.
- Move advanced options into **View settings**.
- Keep the research-use disclaimer visible without allowing it to consume primary interaction space.

### 5.3 Controls that remain immediately visible

- Analyze scan / Reveal source of truth when applicable
- CT / Prediction / Source of truth / Overlap
- 2D / 3D
- All / Pancreas / Lesion
- Layer palette
- Reset view

### 5.4 Controls moved to View settings

- Full abdominal CT
- CT opacity
- Overlay opacity
- Cut away CT
- Cut depth
- Optional rendering material selection during development
- Optional presentation/clinical surface style if retained after testing

---

## 6. Viewer state model

The refactor will replace loosely related display booleans with an explicit state model.

```text
workflowStage:
  unmarked | scored | truthUnlocked

evidenceMode:
  ct | prediction | truth | overlap

anatomyFocus:
  all | pancreas | lesion

sourceFocus:
  both | prediction | truth | difference

focusTreatment:
  context | isolate

selectedObject:
  null
  prediction.pancreas
  prediction.lesion
  truth.pancreas
  truth.lesion
  difference.agreement
  difference.predictionOnly
  difference.referenceOnly

visibleLayers:
  ct
  prediction.pancreas
  prediction.lesion
  truth.pancreas
  truth.lesion
  difference.agreement
  difference.predictionOnly
  difference.referenceOnly
```

### State invariants

- `truth` and `overlap` modes are unavailable for library cases until `truthUnlocked`.
- `overlap` always has at least two evidence layers or a derived difference layer available.
- Selecting a hidden object makes it visible.
- Isolate never changes the underlying saved visibility preferences.
- Changing evidence mode preserves anatomy focus when that focus exists in the destination mode.
- Switching 2D/3D preserves evidence mode, focus, selection, crosshair world coordinate, and camera target where possible.
- Changing scans clears transient focus and applies the correct workflow stage for the destination case.

---

## 7. Direct anatomy interaction

### 7.1 2D picking

NiiVue's location callback reports the values of loaded volumes at the selected voxel. The masks use:

- `1` = pancreas
- `2` = lesion

Click behavior:

- Click a lesion voxel → select the visible lesion source.
- Click a pancreas voxel → select the visible pancreas source.
- In Overlap mode, use source ordering and layer values to determine whether the click intersects prediction, reference, or both.
- If multiple objects occupy the point, show a compact source chooser or select the currently emphasized source.
- Click background or press Escape → clear selection and return to the current All/context view.

### 7.2 3D picking

Each mesh will be loaded with a stable name and mapped to a semantic identity:

```text
prediction.pancreas
prediction.lesion
truth.pancreas
truth.lesion
```

NiiVue object/depth picking will map the clicked mesh ID back to that identity.

If direct picking proves unreliable for a specific transparent overlap:

- Use the current depth-selected object where unambiguous.
- Prefer the emphasized source.
- Keep anatomy/source chips as an accessible, deterministic fallback.

Do not use NiiVue's `clickToSegment` function. That function creates or modifies a segmentation and is outside this project's UI scope.

### 7.3 Focus treatment

When an object is selected:

- Increase its saturation and opacity.
- Apply a visible rim/silhouette treatment.
- De-emphasize non-selected segmentation layers.
- Reduce CT visual weight without destroying anatomical orientation.
- Center the crosshair/camera target on the object's centroid or bounding box.
- Show a compact selected-object card.

Initial tuning targets:

| Selected object | Selected layer | Related anatomy | Other source | CT context |
|---|---:|---:|---:|---:|
| Prediction lesion | 100% | 10–18% pancreas shell | 8–15% | dim |
| Prediction pancreas | 85–100% | 35–50% lesion context | 8–15% | dim |
| Reference lesion | 100% | 10–18% reference pancreas | 8–15% | dim |
| Difference region | 100% | 8–15% contextual surfaces | 8–15% | dim |

These are starting visual targets, not locked scientific parameters.

### 7.4 Isolate treatment

The contextual card exposes **Isolate**:

- Hide non-selected segmentation surfaces.
- Keep an optional faint CT or orientation marker.
- Preserve camera position.
- Offer **Restore context** in the same location.

### 7.5 Selection synchronization

- Clicking anatomy updates the focus chips.
- Clicking a focus chip updates the viewer selection.
- Changing modes updates the object palette.
- Selected state uses text, border, and an icon in addition to color.

---

## 8. Evidence modes

| Mode | Viewer content | Main purpose |
|---|---|---|
| CT | CT only | Inspect the unmarked study |
| Prediction | CT + predicted pancreas/lesion | Evaluate the model proposal |
| Source of truth | CT + reference pancreas/lesion | Inspect the independent annotation |
| Overlap | Prediction + reference and/or derived difference | Explain agreement and error |

### 8.1 Prediction mode

- Prediction pancreas: `#26c5a6`
- Prediction lesion: `#f96363`
- Default to All anatomy.
- Lesion remains visually prominent but does not obscure the pancreas context.

### 8.2 Source-of-truth mode

- Reference pancreas: `#38bdf8`
- Reference lesion: `#fbbf24`
- Label the evidence as a reference annotation.
- Use the same interaction rules as Prediction mode.

### 8.3 Overlap mode

Overlap mode has two representations.

#### Source overlay

- Prediction and reference remain in their established colors.
- Source focus can emphasize Prediction, Reference, or Both.
- Non-focused source becomes a ghosted context layer.
- Pancreas and lesion can be reviewed separately.

#### Difference view

Derived evidence:

- **Agreement** — prediction and reference both contain the selected anatomy.
- **Prediction only** — over-segmentation or false-positive region.
- **Reference only** — reference region absent from the prediction.

Initial semantic colors:

- Agreement: soft violet/near-white with an explicit Agreement label.
- Prediction only: red/magenta.
- Reference only: amber.

These colors apply only in Difference view and do not replace the normal prediction/reference palette.

### 8.4 Metrics HUD

In Overlap mode, display:

- Pancreas Dice
- Lesion Dice
- Current selected anatomy
- Current source/difference emphasis

The HUD remains compact and visually subordinate to the anatomy.

---

## 9. Two-dimensional visual treatment

### 9.1 Contour-forward rendering

The 2D comparison should favor boundaries over heavy filled masks.

Target behavior:

- Prediction mode: light fill plus strong prediction contour.
- Source-of-truth mode: light fill plus strong reference contour.
- Overlap mode: reduce fills further and emphasize both contours.
- Difference mode: use semi-transparent difference fills plus crisp boundaries.

NiiVue capabilities to evaluate:

- `setAtlasOutline`
- `overlayOutlineWidth`
- nearest-neighbor mask interpolation
- per-source opacity changes without reloading volumes

### 9.2 Slice focus

Selecting an anatomy:

- Move all three planes to its centroid.
- Preserve synchronized crosshairs.
- Optionally fit the selected bounding box with reasonable surrounding context.
- Avoid zooming so tightly that orientation is lost.

### 9.3 CT presentation

- Keep the CT diagnostically legible in 2D.
- Do not blur or stylize the CT itself.
- De-emphasis uses overlay/CT brightness and surrounding-layer opacity, not fabricated image detail.

---

## 10. Three-dimensional visual-quality strategy

### 10.1 Rendering objective

The 3D anatomy should appear:

- Smooth but not artificially inflated.
- Clearly separated from the background.
- Legible from all rotation angles.
- Easy to select.
- Honest about thin structures, small lesions, disconnected false positives, and boundary disagreement.

### 10.2 NiiVue material spike

Before creating a custom shader, render the same representative case with:

- Phong (current baseline)
- Matte
- Hemispheric
- Toon
- Edge
- Outline
- Rim
- Matcap
- Silhouette

Evaluate each for:

- Silhouette visibility
- Surface depth/readability
- Transparency artifacts
- Lesion visibility inside the pancreas
- Color fidelity
- Performance
- Scientific neutrality

The likely baseline candidate is Matte or Hemispheric for normal surfaces, with Rim/Outline behavior for selection.

### 10.3 Custom medical surface shader

If built-in shaders are insufficient, create a restrained custom NiiVue mesh shader with:

- Two-sided diffuse lighting
- Stable ambient fill
- Soft, low-intensity specular response
- Fresnel/rim illumination at silhouette edges
- No metallic appearance
- No animated or decorative effects
- Separate normal and selected variants

The selected variant may strengthen the rim and brightness but must not change geometry.

### 10.4 Transparency strategy

Avoid relying on one permanently transparent pancreas shell.

Normal All view:

- Use a more substantial pancreas surface with a defined rim.
- Keep the lesion opaque and visually dominant.
- Tune the pancreas so depth remains readable without hiding the lesion.

Lesion focus:

- Ghost the pancreas to approximately 10–18%.
- Keep the lesion fully opaque.
- Dim CT volume context.

Pancreas focus:

- Make the pancreas close to opaque.
- Retain the lesion as a smaller contextual accent.

Overlap:

- Emphasize one source at a time or use Difference view.
- Do not expect four equally transparent meshes to remain readable.

### 10.5 Camera and framing

- Compute a world-space bounding box per mesh.
- Fit the selected anatomy into the viewport with stable padding.
- Set the pivot to the selected anatomy centroid.
- Preserve orientation when moving between sources.
- Use smooth but brief camera transitions only if they do not interfere with manual rotation.
- Keep a one-click standard anatomical view reset.

### 10.6 Background and CT context

- Use a subtle dark radial/vertical gradient rather than a visually flat black void.
- Keep the CT optional in 3D.
- Prefer a focus-centered cutaway or relevant slice context over a dominant rectangular volume block.
- Make the clipping/cutaway boundary visually intentional.
- Never clip prediction/reference meshes merely to hide visual problems.

### 10.7 Edge visibility

Test, in order:

1. Better base material and lighting.
2. Rim or outline shader.
3. Selected-object shader variant.
4. A second silhouette pass only if NiiVue can do it without z-fighting.
5. Custom combined fill-and-rim fragment shader.

Do not add thick black cartoon outlines by default. The result should look polished and medical, not illustrative.

---

## 11. Presentation mesh pipeline

### 11.1 Preserve scientific assets

The following remain authoritative and unchanged:

- `ct.nii.gz`
- `pred.nii.gz`
- `gt.nii.gz`
- Dice and CADe measurements derived from the masks

Presentation meshes are derived visual assets. They never replace the masks for metrics.

### 11.2 Export experiments

Generate a mesh-quality comparison for representative cases:

1. Current export baseline.
2. Current field with explicit vertex normals.
3. Two-times supersampled scalar field before marching cubes.
4. Feature-preserving smoothing with anatomy-specific settings.
5. Alternative mesh container if it improves normals, file size, or load behavior.

Candidate mesh formats:

- OBJ with explicit normals
- PLY with normals
- MZ3 for compact NiiVue-native loading

Do not change the production format until visual quality, alignment, load time, and picking are validated.

### 11.3 Supersampling

For display meshing only:

- Upsample the scalar field from 1.5 mm to approximately 0.75 mm.
- Use interpolation appropriate to the source:
  - Prediction: continuous probability interpolation.
  - Reference: distance-field or carefully controlled label reconstruction.
- Run marching cubes on the denser display field.
- Keep all original NIfTI masks and measurements unchanged.

Supersampling may make a surface visually smoother. It does not create new anatomical evidence.

### 11.4 Anatomy-specific smoothing

Pancreas and lesion should not share one blindly applied smoothing strength.

- Pancreas can tolerate moderate feature-preserving smoothing.
- Small lesions require weaker smoothing to avoid shrinking, rounding, or erasing them.
- Preserve every connected component that exists in the source prediction/reference.
- Do not remove false-positive components for appearance.
- Do not fill holes or repair topology merely to make the model look better.

### 11.5 Normal generation

Evaluate explicit smooth vertex normals:

- Use marching-cubes normals or recompute area-weighted vertex normals.
- Transform normals correctly into world space.
- Verify that affine orientation and nonuniform scaling do not corrupt lighting.
- Compare explicit normals to NiiVue's automatically generated normals.

### 11.6 Mesh fidelity gates

A polished display mesh must satisfy all of the following:

- World alignment remains exact.
- No connected component is removed for appearance.
- Re-voxelized display mesh versus source mask target:
  - Pancreas Dice ≥ 0.98
  - Lesion Dice ≥ 0.95
- Target 95th-percentile surface displacement ≤ one source voxel (1.5 mm).
- Any failure of these targets must be visible in the comparison report and blocks automatic replacement.

These gates evaluate the display reconstruction, not model performance.

### 11.7 Difference assets

For polished 3D Difference view, export:

- Pancreas agreement
- Pancreas prediction only
- Pancreas reference only
- Lesion agreement
- Lesion prediction only
- Lesion reference only

These assets are derived from the original masks. They remain inactive until source of truth is unlocked.

---

## 12. NiiVue architecture refactor

### 12.1 Separate loading from presentation

The NiiVue integration will have distinct responsibilities:

1. **Scene loading**
   - Load CT, prediction/reference masks, and available meshes.
   - Build stable volume and mesh registries.
   - Run only when the case, full-CT source, or fundamental view type changes.

2. **Presentation updates**
   - Change visibility, color, opacity, shader, focus, and camera target.
   - Do not reload files.

3. **Interaction events**
   - Report selected anatomy/source to React.
   - Report world-space crosshair and camera state.

4. **State restoration**
   - Apply React state after 2D/3D transitions or scene reloads.

### 12.2 Stable registry

```text
volumes.ct
volumes.prediction
volumes.truth
volumes.difference.*

meshes.prediction.pancreas
meshes.prediction.lesion
meshes.truth.pancreas
meshes.truth.lesion
meshes.difference.*
```

Each entry stores:

- NiiVue index/ID
- semantic identity
- source
- anatomy
- default color
- default opacity
- selected shader
- centroid and bounding box
- visible/unlocked state

### 12.3 React/NiiVue ownership

React owns:

- Workflow stage
- Evidence mode
- Selection
- Focus/isolate state
- User visibility preferences
- Contextual text and measurements

NiiVue owns:

- WebGL scene objects
- Camera/orbit implementation
- Crosshair rendering
- Medical volume and mesh drawing

The bridge translates explicit React state into imperative NiiVue updates.

---

## 13. Planned file-level changes

These are implementation targets, not changes made by this planning document.

### `ui/src/App.jsx`

- Remove most Review-workspace implementation details.
- Keep application-level routing, case catalog, API state, and modal state.
- Move Review-specific state into a dedicated workspace component/reducer.

### `ui/src/components/ReviewWorkspace.jsx`

- New main Review workspace shell.
- Own the explicit viewer workflow/evidence state.
- Coordinate case selection, inference, reveal, selection, reset, and responsive layout.

### `ui/src/components/NiivueViewer.jsx`

- Refactor scene loading away from ordinary visibility/opacity changes.
- Build stable named layer/mesh registries.
- Add 2D location picking and 3D mesh picking.
- Add focus, isolate, shader, camera-target, contour, and in-place visibility APIs.
- Preserve world focus across modes.

### `ui/src/components/EvidenceModeControl.jsx`

- CT / Prediction / Source of truth / Overlap segmented control.
- Communicate locked/unlocked modes.
- Never hide why a mode is unavailable.

### `ui/src/components/ViewerObjectPalette.jsx`

- All / Pancreas / Lesion focus controls.
- Compact source/layer visibility.
- Selected-state and accessibility labels.

### `ui/src/components/ViewerContextBar.jsx`

- Live score badge.
- Selected-object identity.
- Volume/confidence for prediction review.
- Dice and discrepancy labels for overlap review.
- Focus/Isolate/Restore actions.

### `ui/src/components/ViewSettingsPopover.jsx`

- Full CT, CT opacity, segmentation opacity, cutaway, and cut depth.
- Keep advanced settings outside the permanent layout.

### `ui/src/lib/reviewState.js`

- State reducer, allowed transitions, invariants, and reset rules.
- Centralize the progressive-reveal contract.

### `ui/src/lib/viewerLayers.js`

- Semantic layer definitions, colors, default materials, focus treatments, and source/anatomy mappings.

### `ui/src/index.css`

- Replace bulky panel styling with viewer-first layout.
- Add compact evidence controls, in-view HUD, object palette, contextual strip, and selected states.
- Add responsive fallbacks without reducing the viewer to a small card.

### `scripts/export_case.py`

- Add opt-in display-mesh supersampling experiments.
- Add explicit normal export where supported.
- Add anatomy-specific smoothing.
- Add mesh-fidelity measurements.
- Add derived discrepancy meshes after validation.
- Preserve all original masks, components, and metrics.

### `ui/public/cases/results.json`

Add only metadata required for interaction:

- Mesh centroids/bounding boxes if not computed client-side
- Difference asset paths
- Display-mesh provenance/version
- Optional mesh-fidelity audit values

Never include local filesystem paths.

---

## 14. Implementation phases

### Phase 0 — Checkpoint and visual baseline

- Commit the current working UI before implementation.
- Capture reference screenshots/video for:
  - 2D prediction
  - 3D prediction
  - 2D overlap
  - 3D overlap
  - Small lesion
  - False positive
- Record current load time, mode-switch behavior, and representative mesh counts.

### Phase 1 — Interaction specification and wireframes

- Produce wireframes for CT, Prediction, Source of truth, and Overlap.
- Finalize exact toolbar and context-strip placement.
- Lock desktop and presentation-resolution behavior.
- Do not begin visual polish before the state and layout contract is accepted.

### Phase 2 — State and layout refactor

- Create the explicit reducer/state model.
- Extract ReviewWorkspace from App.
- Build the evidence selector and compact viewer controls.
- Move advanced settings into a popover.
- Preserve existing visual output while changing the architecture.

**Acceptance gate:** all current workflows still function before direct picking or mesh polish is added.

### Phase 3 — Stable NiiVue scene

- Load scene assets once.
- Change ordinary presentation properties in place.
- Preserve crosshair, camera, and selection.
- Eliminate loading spinners during visibility, opacity, and evidence-mode changes after assets are available.

### Phase 4 — 2D selection and focus

- Add voxel-value picking.
- Add anatomy focus, isolate, clearing, and centering.
- Add contour-forward 2D rendering.
- Synchronize viewer selection and React controls.

### Phase 5 — 3D selection and focus

- Add semantic mesh identities.
- Add direct mesh picking.
- Add selection materials and camera fitting.
- Validate transparent overlap behavior and fallback controls.

### Phase 6 — 3D visual-quality spike

- Run the built-in shader comparison.
- Verify canvas pixel density and anti-aliasing.
- Compare current versus explicit-normal meshes.
- Compare current versus supersampled display meshes.
- Choose the minimum-change treatment that meets the quality bar.

**Decision gate:** continue with NiiVue unless the spike fails the acceptance criteria below.

### Phase 7 — Source and overlap interaction

- Unlock persistent Truth and Overlap modes after reveal.
- Add source emphasis.
- Add compact Dice HUD.
- Add 2D difference evidence.
- Add validated 3D discrepancy meshes.

### Phase 8 — Polish and presentation QA

- Tune motion, empty states, labels, keyboard behavior, and responsive layout.
- Test all curated and unmarked cases.
- Test backend-online and backend-offline behavior.
- Record the final demonstration path.

---

## 15. Acceptance criteria

### 15.1 Workflow

- A library case opens as CT only.
- Analyze unlocks Prediction and enters Prediction mode.
- Reference assets are not active before explicit reveal.
- Reveal unlocks Truth and Overlap without requiring another inference call.
- The user can switch freely among all unlocked evidence modes.
- Reset/new scan returns an unmarked case to CT-only Stage 1.
- Curated cases retain immediate access to their existing scientific evidence.

### 15.2 Interaction

- Clicking pancreas or lesion in 2D selects the correct object.
- Clicking a visible mesh in 3D selects the correct object in representative cases.
- Anatomy chips and direct selection remain synchronized.
- Focus de-emphasizes context without destroying orientation.
- Isolate and Restore context are reversible.
- Escape, background click, and All clear selection.
- Switching 2D/3D preserves the evidence and anatomy state.

### 15.3 Visual quality

- Pancreas silhouette remains legible at all standard rotations.
- Selected anatomy is unmistakable without changing its geometry.
- Lesion remains visible inside or adjacent to the pancreas.
- Overlap does not depend on four equally transparent meshes.
- 2D contours remain crisp at presentation resolution.
- Difference view clearly distinguishes Agreement, Prediction only, and Reference only.
- Display meshes pass the fidelity gates in Section 11.6.

### 15.4 Performance

- No network reload for ordinary visibility, focus, source emphasis, or opacity changes.
- Evidence-mode switch after loading feels immediate, target ≤150 ms.
- Focus/isolate updates target ≤100 ms.
- 3D orbit remains responsive on the project MacBook, target ≥45 FPS for representative scenes.
- No progressive memory growth after repeated mode/case switching.

### 15.5 Accessibility

- Every direct viewer action has a button/keyboard equivalent.
- Selected state is communicated by label, border/icon, and color.
- Locked modes explain how they become available.
- Controls have usable focus order and visible focus states.
- Reduced-motion users do not receive camera animation.

---

## 16. Visual-quality decision gate

Keep NiiVue for both 2D and 3D if the visual spike demonstrates:

- Crisp high-DPI rendering
- Reliable silhouette/rim treatment
- Acceptable transparent-surface behavior
- Reliable representative mesh picking
- Stable camera/pivot control
- Scientifically faithful display meshes

Consider a hybrid renderer only if NiiVue fails one or more core criteria after the shader and mesh-pipeline improvements.

### Hybrid fallback

If required:

- Keep NiiVue for NIfTI, 2D tri-planar navigation, crosshairs, and mask contours.
- Use Three.js/React Three Fiber or VTK.js for the polished mesh-only 3D surface view.
- Reuse world-space mesh coordinates and the shared React viewer state.
- Preserve an explicit link between 2D crosshair position and 3D focus.

Hybrid trade-offs:

- Better materials, lighting, outline post-processing, and raycast picking.
- More code, more dependencies, more synchronization risk.
- CT volume rendering becomes harder to reproduce outside NiiVue.

Therefore hybrid is a fallback, not the starting plan.

---

## 17. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Smoothing beautifies away errors | Preserve masks/metrics, retain every component, enforce fidelity gates |
| Small lesions shrink or disappear | Use weaker lesion smoothing and verify re-voxelized fidelity |
| Transparent overlap becomes unreadable | Emphasize one source or use Difference view |
| 3D picking fails through transparency | Prefer emphasized source and keep deterministic object controls |
| Refactor breaks curated cases | Preserve curated workflow in Phase 2 before adding new interaction |
| Too many controls return | Keep only evidence, focus, layers, mode, and reset persistent |
| Viewer changes cause reload/flicker | Separate scene loading from property updates |
| More polished render implies clinical certainty | Keep evidence labels and scientific framing visible |
| Hybrid renderer expands scope | Use the visual-quality decision gate before adding it |
| Supersampled mesh is mistaken for higher model resolution | Mark it as display reconstruction and never use it for metrics |

---

## 18. Explicit non-goals

- No manual pancreas or lesion drawing.
- No browser-based segmentation editing in this refactor.
- No diagnostic classification or tumor-type claim.
- No modification of model predictions for visual convenience.
- No removal of false positives or disconnected prediction components for appearance.
- No replacement of source masks with smoothed meshes for evaluation.
- No medical-device workflow or clinical deployment claim.
- No immediate NiiVue replacement before the visual-quality spike.

---

## 19. Demonstration story after the refactor

1. Open a clean scan.
2. Inspect it in 2D or 3D.
3. Analyze it live.
4. Click the predicted lesion.
5. Rotate or move through the synchronized planes while the pancreas becomes a faint contextual shell.
6. Isolate the lesion briefly, then restore context.
7. Inspect the predicted pancreas.
8. Reveal the Johns Hopkins reference annotation.
9. Switch between Prediction and Source of truth.
10. Enter Overlap and focus on the lesion.
11. Show Agreement, Prediction only, and Reference only.
12. Use the Dice HUD to connect the visual difference to the metric.
13. Explain where the model is strong, where it misses, and why human review remains necessary.

The presentation is centered on spatial evidence rather than claims.

---

## 20. Completion definition

This refactor is complete when the Review workspace:

- Feels centered on the scan rather than its controls.
- Supports reversible CT, Prediction, Source-of-truth, and Overlap modes.
- Makes pancreas and lesion directly interactive in both 2D and 3D.
- Supports focus and isolation without losing anatomical context.
- Shows discrepancy as spatial evidence.
- Presents a materially cleaner, more legible 3D pancreas without changing the underlying prediction.
- Maintains the progressive reveal and the project's scientific honesty.
