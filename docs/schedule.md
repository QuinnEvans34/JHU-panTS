# 5-Week Schedule

Project: 3D Pancreas-Aware Pancreatic Lesion Segmentation (PanTS)
Primary target: Level 4.5 (background, pancreas, and lesion)

This is a solo project, and the dates below are approximate. I will line them up with the official course calendar. The first two weeks are mostly setup and making sure the data is valid, so the real technical milestones start in Week 2 and build from there. For each week I wrote down what I want to finish and what it would look like if I fell behind, so I can catch problems early.

---

## Week 1: Setup and Data Validation (around Jun 29 to Jul 5)

What I want to get done:

- Finish the proposal and the pitch.
- Set up the repository structure (the config, source code, scripts, and supporting files).
- Download a small local subset of PanTS to work with, without ever committing the raw data.
- Write the script that builds a manifest pairing each scan with its label files.
- Load a single case all the way through the pipeline and save axial, coronal, and sagittal overlays of the CT with the pancreas and lesion outlines, checking that the masks line up with the anatomy.

By the end of the week I want to be able to load one PanTS case and save correct three view overlays of the CT with the pancreas and lesion.

Behind schedule would look like: I cannot load or line up a single CT and mask pair, or the overlays do not match the anatomy, by the end of the week.

---

## Week 2: Preprocessing and Wiring the Pipeline (around Jul 6 to Jul 12)

What I want to get done:

- Build the real preprocessing with MONAI: reorient the scans, resample them to a common voxel spacing, window the CT intensities, and normalize them.
- Create patient level train, validation, and test splits, being careful never to split by slice.
- Add the training transforms, including the positive and negative patch cropping and some light augmentation.
- Build the model, the loss, the metrics, and the training loop.
- Run an overfit test where I force the model to reproduce the mask on one or two cases.

By the end of the week I want the model to overfit one or two cases and reach near perfect accuracy on them.

Behind schedule would look like: the model cannot overfit even a tiny set, which would mean something in the data, the loss, or the labels is wired wrong.

---

## Week 3: Baseline Training (around Jul 13 to Jul 19)

What I want to get done:

- Run a quick pancreas only training as a fast way to prove the pipeline works on an easy target, without spending too long on it.
- Run the first real pancreas plus lesion training on a small subset.
- Get the validation loop, checkpoint saving, and experiment tracking with MLflow working.
- Have my Week 3 one on one check in, focused on my model choice and the health of the plan.

By the end of the week I want the model training on a subset and producing validation accuracy curves and overlays for both the pancreas and the lesion.

Behind schedule would look like: no validation curve, training that diverges, or a lesion score stuck near zero.

---

## Week 4: Lesion Focused Training and Full Volume Evaluation (around Jul 20 to Jul 26)

What I want to get done:

- Push the model to actually find lesions by biasing the patch sampling toward tumor regions and tuning the loss.
- Evaluate with sliding window inference across the full volume rather than scoring on patches.
- Report the metrics that matter, including pancreas accuracy, lesion accuracy, sensitivity, precision, and false positive volume.

By the end of the week I want full volume results with the pancreas and lesion reported separately, and a real, non trivial lesion score.

Behind schedule would look like: the lesion score is near zero or the model only predicts background, or I do not have full volume evaluation working.

---

## Week 5: Evaluation, Demo, and Delivery (around Jul 27 to Aug 2)

What I want to get done:

- Do a failure case analysis, looking at where the model misses tumors or over predicts, with overlays in all three views.
- Build the React and NiiVue demo that loads a case, shows the outlines in three planes and in 3D, gives the possible tumor summary, and lets the user export the mask. It reads predictions computed ahead of time, so it does not need a live backend.
- Write the final report covering my methods, metrics, visuals, limitations, and the honest framing that this is not a diagnostic tool.
- Prepare the final presentation.
- Have my Week 5 one on one check in, focused on the interface and the final prep.

By the end of the week I want a complete repository, a written report, a working demo, and separate pancreas and lesion metrics.

Behind schedule would look like: the demo is not running, or I do not have full volume metrics and visuals ready for the final.

---

## Risk Buffer

If any week slips, Level 4.5 is the line that has to hold, and Level 5 (the full multi structure version) is a stretch goal that gets dropped first. If the lesion segmentation is underperforming by Week 4, my fallback is to deliver a strong pancreas segmentation result along with a documented analysis of why the lesion is so hard to detect, which is still a complete and honest project.
