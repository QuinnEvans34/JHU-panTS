# Notebook Narration Script

A "say this" line for each part of `eda-notebook.ipynb`, each paired with the decision it forced. The rule for the whole talk: never show a chart without stating the decision it drove. Keep each to one or two sentences out loud, then move on.

## 1. Dataset overview
On screen: the counts, 9,000 train and 901 test, tumor-positive versus tumor-free.
Say: "This is the raw material, about 9,900 abdominal CT scans, each a full 3D volume with voxel-level pancreas and tumor masks. Nine thousand are for training and 901 are a held-out official test set."
Decision: sets the scope and the fact that this is a 3D segmentation problem, not tabular.

## 2. Tumor prevalence by split (Visualization 1)
On screen: the bar chart, about 10 percent tumor in train, about 17 percent in test.
Say: "Only about one scan in ten has a tumor, and the test set is deliberately tumor-richer. This imbalance is the single biggest driver of everything I built."
Decision: bias patch sampling toward tumor voxels, use a Dice-based loss instead of plain accuracy, and score lesion accuracy only on tumor cases while measuring false alarms separately on healthy ones.

## 3. Lesion volume distribution (Visualization 2)
On screen: the log-scale histogram, median near 4,700 cubic millimeters, a tail of tiny lesions.
Say: "Among tumor cases, lesion size spans five orders of magnitude, from a couple cubic millimeters up to over 700,000. A handful are only a few voxels."
Decision: the model has to catch very small targets, so patch sampling is tumor-biased, and at inference I drop sub-threshold specks as almost certainly false alarms.

## 4. Scan geometry heterogeneity (Visualization 3)
On screen: slice-count and slice-thickness histograms, huge spread.
Say: "The scans are wildly inconsistent, slice counts from 8 to over a thousand and voxel spacing varying more than tenfold. A model cannot compare apples to oranges."
Decision: every scan is reoriented to a standard orientation and resampled to a common 1.5mm grid, then intensity-windowed, before the model ever sees it.

## 5. Acquisition: contrast phase and sites (Visualization 4)
On screen: contrast-phase bars and scans-per-site.
Say: "The data spans many institutions, four scanner makers, and several contrast phases. That diversity is a strength for generalization, but it is also where the intensity and geometry variation comes from." (If asked: the metadata lists six manufacturer strings, but that is really four makers, because GE and Philips are each double-counted under two spellings; and the site field mixes grouped labels like '15 Sites' with codes, so it is many more than twenty institutions.)
Decision: windowing and resampling are non-negotiable, and it is also why I am honest that a 100-case development subset only sees a slice of this diversity.

## 6. Label validation (Visualization 5)
On screen: the cross-tab, 99.6 percent agreement.
Say: "As an independent check, my tumor label, derived by counting voxels in the mask, agrees with the dataset's own tumor flag 99.6 percent of the time."
Decision: that is strong evidence the label pipeline is wired correctly, and I flag the 44 disagreements as a data quirk rather than trusting the spreadsheet blindly.

## 7. Data quality summary
On screen: completeness and missing-metadata numbers.
Say: "The imaging is essentially 100 percent usable, every case has its masks and there are no duplicates. The demographic metadata is messy, about half of age and sex missing, but I never feed it to the model, so it does not affect training."
Decision: clean the images (standardize), ignore the tabular metadata as a model input.

## 8. The overfit test (the sanity gate)
On screen: the overfit curve, loss falling, pancreas and lesion Dice rising.
Say: "Before trusting any real training, I forced the model to memorize a tiny fixed set. Loss fell from 1.87 to 0.54, pancreas Dice reached 0.89, and on a tumor case the lesion reached 0.85."
Decision: this proves the whole pipeline can learn end to end, so any later struggle is a tuning problem, not a broken pipeline. This is the Week 2 milestone.

## The one-sentence close
"Every one of those findings is paired with a concrete decision in the pipeline, which is exactly how I want the model judged: the data told me what to build, and I built it."

## If asked about raw versus cleaned (likely, since it is on the results)
"Raw is the model's direct prediction. Cleaned is that same prediction after rule-based post-processing, keep the largest blob, drop tiny specks, and require a lesion to sit near the pancreas. It runs only at evaluation, never during training, and I report both so you can see what the model learned versus what the deployed tool would actually show. Notice cleanup actually lowers my lesion Dice, from 0.169 to 0.139, while raising specificity from 8 to 42 percent. That is a real tradeoff, and I show it rather than hide it, which is the opposite of gaming the metric."

## If asked "isn't post-processing just gaming the score?"
"No, and the proof is that it lowers my lesion Dice rather than raising it. The rules are fixed and general, they never see the ground-truth answer, and I always report the raw number next to the cleaned one. The point of the cleanup is not a better score, it is a usable tool: the raw model flags a tumor on almost every healthy scan, and the rules cut those false alarms."

## If asked about the probability threshold (the logistic-regression connection)
"Segmentation is really per-voxel classification: the model outputs a probability of lesion for every voxel, and something turns that into yes or no. By default that is a 0.5 cutoff, the argmax. My threshold sweep raises that cutoff, exactly like moving the decision threshold in logistic regression, so a voxel called lesion at low confidence becomes a no. Higher threshold means fewer lesion calls, higher specificity, lower sensitivity, the same ROC-style tradeoff.
The key finding: the threshold barely helped me, specificity stayed at 8 percent until almost 0.90, but the geometric constraint jumped it to 42 percent. The reason is that my false positives were confident but misplaced, the model was over 90 percent sure of a tumor sitting in the wrong place. A probability threshold cannot remove a confident wrong answer, but a geometric rule can, because it does not care how confident the model is, only that a pancreatic tumor cannot be there. That is why the threshold was my weak lever and the anatomy constraint was my strong one."
