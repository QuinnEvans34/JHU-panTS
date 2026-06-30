# Project Pitch & Defense — Talking Points (M1P1)

**5-minute pitch + 5-minute Q&A.** Speak to the panel, don't read. Goal: anyone in the room can explain back *what* you're building and *why* it matters.

---

## 5-minute pitch (target ~1 min per beat)

**1. Problem & business user (~1 min)**
Outlining the pancreas and a pancreatic lesion on a 3D CT scan is slow, manual work — a trained reader traces the organ slice by slice across hundreds of images, and the pancreas is one of the hardest organs to delineate. My user is a **medical-imaging annotator / radiologist** in a research or clinical-imaging pipeline who has to produce these contours. The decision I support: for each scan, they **accept, edit, or reject** an automatically proposed outline instead of drawing from scratch.

**2. Dataset & why it fits (~1 min)**
**PanTS**, created by Johns Hopkins (NeurIPS 2025): 36,390 CT volumes, voxel-wise masks for pancreatic tumors, pancreas subregions, and 24 surrounding structures. Open-source (CC-BY-NC-SA). It's a static benchmark — not real-time — which is exactly right for training a segmentation model. I use the ~346 GB Mini release and develop on a local subset with patch-based training.

**3. ML approach & output (~1 min)**
This is **3D semantic segmentation** — a patch-based **3D U-Net** in MONAI/PyTorch. Primary target (Level 4.5): predict **background / pancreas / lesion**. The hard part is class imbalance — the lesion is tiny — so I use **Dice+CE loss** and **tumor-positive patch sampling**. Output: a 3D mask of pancreas and lesion, evaluated with full-volume sliding-window inference and Dice reported *separately* for pancreas and lesion.

**4. Front-end / how the user consumes it (~1 min)**
A **Streamlit viewer**: load a scan, see CT with pancreas (green) and lesion (red) overlays in axial/coronal/sagittal, scroll slices, toggle masks, read the predicted **lesion volume in mm³**, and export the mask to edit in a real tool. The user *accepts or corrects* — they don't draw from a blank screen.

**5. What I'm excited to learn (~30 sec)**
Standing up a **complete 3D medical-imaging pipeline** end to end — MONAI, volumetric data, and class-imbalanced segmentation are all new to me, and that's exactly the gap I want to close.

> **Say this once, clearly:** "This is a segmentation tool, not a diagnostic system. A human makes every clinical decision."

---

## Anticipated Q&A — have answers ready

- **"Isn't this just diagnosis in disguise?"** No — it outputs a contour, not a diagnosis. The user reviews and edits; no clinical determination is made or claimed.
- **"The lesion is tiny — won't the model just predict background?"** That's the core risk. Mitigations: pos/neg patch sampling (~70% lesion-positive), Dice/Focal loss, and reporting lesion Dice *separately* so the failure can't hide behind a high average.
- **"346 GB — how do you train on a laptop/local GPU?"** I don't train on full volumes or the full set. Local subset + patch-based training + sliding-window inference at test time. Patch size is tuned to my VRAM.
- **"How do you avoid data leakage?"** Patient-level splits, never slice-level. The same patient never appears in both train and test.
- **"How will you know it works?"** Stage-0 overfit check first; then per-class Dice/IoU, lesion sensitivity/precision on full-volume inference, plus visual overlays and failure-case analysis.
- **"What if lesion segmentation fails?"** Fallback: deliver strong pancreas segmentation + a documented analysis of why the lesion is hard. Still a complete, honest project.
- **"Why pancreas + lesion instead of lesion only?"** Anatomical context. Tumor-only segmentation is harder and less stable; the pancreas grounds the model.

---

## Delivery reminders
- 5 minutes is tight — rehearse to ~4:30 so Q&A doesn't eat the pitch.
- Lead with the user and the problem, not the architecture.
- It's fine to say "I don't know yet" in Q&A — defend the *plan*, not perfection.
