# Business-Facing UI — Walkthrough

**PanTS Review** — a clinical review workspace for pancreas and pancreatic-lesion segmentation.
Built with **React + NiiVue** (a WebGL medical-imaging viewer), styled with a purpose-built dark
medical theme. Screenshots in [`ui-screenshots/`](ui-screenshots/).

---

## What the UI lets the business user do

The user is a **radiologist or imaging annotator**. The interface is built around one workflow:
*look at a scan the model has never seen, have the model propose an outline, and decide whether to
accept, edit, or reject it.*

### Inputs
| Input | Control | Purpose |
|---|---|---|
| Which scan to review | **Scan library** — a browsable gallery of prepared, held-out CT studies | Pick a study the way you would pick one off a worklist |
| Run the model | **Analyze scan** button | Triggers a live prediction on the selected scan |
| Which structures to show | **Pancreas** / **Possible lesion** layer toggles | Isolate one structure at a time |
| How strong the overlay is | **Overlay opacity** slider | See the underlying tissue through the outline |
| How to view the anatomy | **Three planes** / **3D** toggle | Standard triplanar radiology view, or a rotatable 3D surface model |
| Field of view | **Full abdominal CT** toggle | Switch between the pancreas close-up and the whole abdomen for anatomical context |
| 3D depth | **CT volume opacity** + **Cut away CT** | Slice into the CT volume to expose the organ surfaces inside |
| Verification | **Reveal source of truth** | Overlay the expert-drawn reference on top of the prediction |
| Review decision | **Mark reviewed** / **Discuss** | Record a per-case decision (persists between sessions) |
| Hand-off | **Export predicted mask** | Download the outline as a standard NIfTI file for editing in professional tools |

### Outputs
The finding panel returns a **CADe summary** — deliberately phrased as a prompt for review, never as
a diagnosis:
- **CADe flag** — "Possible lesion" or "No finding flagged"
- **Approximate diameter** (mm) and **predicted volume** (cm³)
- **Confidence** — the model's certainty in the flagged region
- **Location** — the pancreatic region involved
- **Inference time** — e.g. "scored in 0.6s"
- **Overlap with source of truth** — pancreas and lesion Dice, shown once truth is revealed

On the images: **teal** = model pancreas, **red** = model lesion, **blue** = reference pancreas,
**amber** = reference lesion. The same convention is used everywhere in the app.

---

## How the UI connects to the deployed model endpoint

The front-end calls the **FastAPI inference service** (`scripts/serve.py`) that wraps the registered
MLflow model `pancreas-lesion-segmenter` v1 (checkpoint step 18000).

```
React UI  ──GET  /cases────────▶  FastAPI service  ──▶  registered SegResNet (MPS)
          ──POST /predict───────▶     (loads the checkpoint once at startup,
          ◀── CADe summary JSON ──     serializes inference behind a lock)
```

- **`GET /cases`** populates the scan library from the prepared local case folder.
- **`POST /predict {case_id}`** runs the model on that scan and returns the CADe summary — typically
  **~0.6–1.0 s** per scan.
- The prediction is genuinely computed on request. The heavy 3D volumes and surface meshes are
  pre-rendered for instant display, but the numbers in the finding panel come from the live call.

**Graceful degradation.** If the service is unavailable the app does not break — it falls back to the
saved result for that case and shows *"endpoint offline — showing cached result."* The UI is fully
functional with no backend running, which is a deliberate demo-safety decision.

---

## How data freshness is surfaced

Freshness is shown in three places, because a clinical user must never wonder whether they are
looking at a stale answer:

1. **Header** — the exact model serving the results: *"Model: pancreas-lesion-segmenter v1 ·
   checkpoint step 18000"*, plus a note that predictions are computed live by a deployed FastAPI
   endpoint when available, with cached results as fallback.
2. **Per-result badge** — switches from **"Precomputed"** to **"Live · scored 10:31:59"** with the
   measured inference time the moment a live prediction returns.
3. **Explicit fallback notice** — if the result came from cache rather than a live call, the app says
   so in plain language rather than silently showing an old number.

---

## Design decisions made for a non-technical user

**Plain language over jargon.** The model outputs a softmax probability map; the user sees "Possible
lesion," an approximate diameter in millimeters, and a confidence. Volumes are shown in cm³ and sizes
in mm — units a clinician already thinks in — not voxel counts.

**A progressive reveal, not a wall of data.** A scan loads **unmarked**, exactly as it came from the
scanner. The user analyzes it, sees the model's proposal, and only then reveals the reference. This
mirrors how a reader actually works and makes the model's contribution obvious, rather than presenting
a pre-drawn image where it is unclear what the model did.

**Honest framing, everywhere.** A persistent banner states *"Research use only. Segmentation and
annotation-assist interface — not a diagnosis."* The model's output is called a **proposal** and a
**possible finding**, never a detection or a result. This is a deliberate safety choice: the interface
should make over-trusting the model difficult.

**The failure cases are in the demo on purpose.** The prepared library includes scans the model gets
right, a small tumor it under-covers, healthy scans it correctly ignores, and one healthy scan it
over-calls. Showing the false positive is the fastest way for a reviewer to calibrate how much to
trust a flag.

**Radiology-native interaction.** Triplanar views with a synchronized crosshair, scroll-through slices,
and a dark theme are what imaging professionals already use. The 3D surface view exists because a
rotatable model of the pancreas with the lesion inside communicates location instantly to someone who
does not read cross-sections for a living.

**It cannot stall.** Precomputed volumes, cached fallback, and no required backend mean the interface
always renders. For a tool meant to save a busy reader time, an interface that hangs is worse than one
that is slightly less live.

---

## Known limitations surfaced in the interface

- The model is given the pancreas region rather than searching the full scan autonomously — the
  fully-automatic cascade is the next phase.
- False alarms are common (17% specificity on held-out healthy scans); the UI frames every flag as a
  prompt to review for exactly this reason.
- Small tumors are over-drawn and need editing, which is why mask export exists.
