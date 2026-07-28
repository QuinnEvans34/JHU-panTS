# How to Use the PanTS Review Tool

*A plain-language guide. No technical background needed.*

---

## What this tool does

This is a **second-reader assistant for abdominal CT scans**. It looks at a scan of a patient's
abdomen, outlines the **pancreas**, and highlights any region that **might** be a pancreatic tumor.

Think of it like spell-check for medical images. Spell-check does not decide what your sentence
should say — it underlines something and asks you to look. This tool does the same thing: it draws
a proposed outline and says *"there could be something here, please review."*

**It is not a diagnosis.** It never says "this patient has cancer." A trained radiologist looks at
every result and decides what is real.

## Who it is for

- **Radiologists** reading abdominal CT scans, who want a second set of eyes that never gets tired.
- **Imaging annotators** whose job is to trace organs and lesions by hand — slow, tedious work.
  Instead of drawing an outline from scratch, they can accept, edit, or reject one the tool proposes.

The pancreas is a genuinely hard organ to read. It is soft, irregular, tucked behind other organs,
and pancreatic tumors are often nearly invisible to the human eye. That is the problem this tool exists to help with.

---

## Using it, step by step

### Step 1 — Open the scan library
Launch the app and open the **Scan library**. You will see a set of prepared CT scans, each one a
real patient study the model has never been trained on. Every scan is anonymous — identified only by
an ID like `PanTS 00009005`.

### Step 2 — Load a scan
Click a scan to open it in the **Review workspace**. It loads **unmarked** — just the raw CT images,
exactly as they came from the scanner, with nothing drawn on them yet. You are looking at what a
radiologist sees before anyone has touched it.

You can move through the scan the way you would expect:
- **Three planes** shows the standard three views (from the front, the side, and from above). Scroll
  to move through the slices; drag the crosshair to line all three views up on the same spot.
- **3D** shows a rotatable three-dimensional model. Drag to spin it, scroll to zoom.
- **Full abdominal CT** switches from the close-up around the pancreas to the whole abdomen, so you
  can see where the pancreas actually sits in the body.

### Step 3 — Analyze it
Click **Analyze scan**. The model runs on the scan right then — this is a live analysis, not a saved
answer — and takes about **one second**. You will see the time it was scored and how long it took, so
you always know the result is current.

### Step 4 — Read the result
The panel on the right fills in:

| What you see | What it means |
|---|---|
| **Possible lesion / No finding** | Whether the tool flagged anything worth a look. "Possible lesion" is a prompt to review — **not** a diagnosis. |
| **Approximate diameter** | Roughly how wide the flagged region is, in millimeters. |
| **Predicted volume** | How much tissue was flagged, in cubic centimeters. Larger regions are generally more likely to be real. |
| **Confidence** | How strongly the model believes the flagged region is a lesion. Treat it as the model's certainty, not a probability that the patient has cancer. |
| **Location** | Where in the pancreas the region sits. |

On the images, the outlines are color-coded:
- **Teal** — the pancreas as the model sees it.
- **Red** — the region the model thinks might be a tumor.

### Step 5 — Check it against the source of truth
Click **Reveal source of truth** to overlay the expert-drawn answer that came with the scan:
- **Blue** — the pancreas as an expert drew it.
- **Amber** — the tumor as an expert drew it.

Now you can see exactly how the model did. Where red sits on top of amber, the model found the real
tumor. Where red appears with no amber underneath, the model raised a false alarm. This view is the
honest scorecard, and it is the fastest way to build (or lose) trust in a given result.

You will also see two **Dice** scores. Dice is simply *how much the two outlines overlap*, from 0
(no overlap at all) to 1 (a perfect match). A pancreas Dice around 0.85 means the organ outline is
very close to the expert's. A lesion Dice around 0.5 means the tumor outline is roughly half-overlapping —
useful as a starting point to edit, not a finished contour.

### Step 6 — Export
**Export predicted mask** downloads the outline as a standard medical-imaging file that can be opened
and edited in professional annotation software. This is the actual hand-off: the tool gets you 80% of
the way, you finish it.

---

## How to interpret results honestly

**What the tool is good at.** It finds tumors. Across 151 held-out scans that contained a real tumor,
it flagged **96%** of them. If the goal is "do not miss anything," it performs well. It also outlines
the pancreas itself very reliably (about 85% overlap with expert contours).

**What it is not good at — read this before trusting it.**

1. **It raises a lot of false alarms.** On scans with no tumor at all, it stayed correctly quiet only
   **17%** of the time. In plain terms: *it cries wolf often.* A flagged region is a prompt to look,
   nothing more. This is the single most important limitation to understand.
2. **It over-draws small tumors.** For tumors under about 1 cm³, the tool tends to paint a region far
   larger than the actual lesion. It usually finds them, but the outline needs real editing.
3. **The tumor outline is a starting point, not a final answer.** Roughly half-overlap on average
   means every contour should be reviewed and adjusted.
4. **It is given the pancreas region to look at.** The current version is pointed at the pancreas
   rather than searching the entire scan on its own. Fully automatic whole-scan search is the next
   phase of this work.
5. **It was trained on one dataset.** Performance on scans from very different scanners, hospitals, or
   imaging protocols is unknown and should be validated before any real use.

**The bottom line for a reviewer:** treat a flag as *"look here first,"* never as *"this is cancer."*
The tool is designed to save you time on the tracing work and to make sure something suspicious does
not slip past — not to make the call for you.

---

## If something goes wrong

- **"Endpoint offline — showing cached result"** — the analysis service is not running, so the app is
  showing a previously saved result instead of scoring live. The displayed numbers are still valid;
  they were just computed earlier. Restarting the service restores live analysis.
- **A scan will not load** — the prepared scan files are missing from the local case folder. See the
  README for how to regenerate them.

---

*Research use only. This is a segmentation and annotation-assist tool, not a diagnostic device, and
it has not been reviewed or approved by any regulatory body.*
