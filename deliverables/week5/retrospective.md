# Project Retrospective

**Project:** 3D pancreas-aware pancreatic lesion segmentation on the Johns Hopkins PanTS dataset
**Timeline:** five weeks, solo · **Final model:** `pancreas-lesion-segmenter` v1

---

## What I am most proud of technically

The thing I am proudest of is an idea that was mine, and that worked. For the first two weeks the
model had a stubborn problem: it found tumors but massively over-predicted them, flagging something on
92 percent of healthy scans. I tried the obvious knobs, the sampling ratio and the loss function, and
both came back as clean nulls, which told me the problem was structural rather than a hyperparameter.
The standard approach feeds the network random cropped patches of the scan, and it occurred to me that
a patch is a terrible way to look for a tumor in an organ, because the model never sees the whole
pancreas at once and has no sense of what is normal for that organ. So instead of random sub-patches I
fed the model the entire pancreas region as a single fixed cube every step. Pancreas accuracy jumped
from 0.72 to 0.81, the lesion score beat my previous best, and specificity went from 8 percent to 55
percent in one change. That became the recipe every later model was built on, and it is still the
architecture of the final registered model.

The second thing I am proud of is less glamorous but probably matters more: the experimental
discipline. I ran twenty-six numbered experiments, each with a hypothesis and an accept or reject bar
written down *before* I saw the result. That discipline paid for itself twice. Once when an
anatomy-aware experiment looked like a clear win at an intermediate checkpoint, and I made myself
train both arms to convergence before deciding, at which point the effect vanished and I rejected it.
And again when a specificity experiment cleared its specificity bar but missed the detection floor by
three cases, and I recorded it as a rejection instead of quietly moving the goalposts I had set for
myself. A result you stop at because it looks good is not a result you can trust, and learning that in
practice rather than in theory changed how I work.

## The biggest challenge

The hardest moment of the project was discovering, at the end of Week 3, that my headline number was
wrong. I had an adversarial code audit run against the repository, and it found that my data-scaling
script sampled training cases from the wrong column of the manifest, which meant my training set
overlapped my validation set. When I checked it myself, thirty of the forty cases I had been reporting
results on had been in training. My reported lesion score of 0.528 was inflated by leakage. That was a
genuinely bad feeling, because I had presented that number.

What I did about it is the part I would defend in an interview. I verified the bug myself rather than
taking the audit's word for it, I owned it in my documentation instead of quietly restating the number,
and then I fixed the root cause rather than the symptom: the split builder now samples only from the
carved training fold, and I added a guard that aborts training at startup if a training split ever
touches validation or test, so that entire class of bug cannot happen silently again. Then I rebuilt
clean splits, retrained, and re-reported. The honest number came back at 0.415 on validation and 0.474
on the untouched official test set. Lower than the number I had been carrying, but real, and it did
not collapse, which told me the underlying result was genuine and only the margin was contaminated.
The lesson I actually internalized is that the audit caught it before external validation rather than
after, which is exactly when you want to find it, and that being able to say "I was wrong, here is the
fix, here is the guard so it cannot recur" is worth more than a number that does not survive scrutiny.

## What I would do differently with five more weeks

Three things, in priority order. First, I would remove the oracle. The current model is handed the
pancreas region rather than searching the whole scan on its own, which is a documented scope choice but
it is not how the tool would be deployed, so I would finish the localize-then-segment cascade so a raw
CT goes in and a result comes out with no human hand-holding. Second, I would attack specificity
properly. Late in the project I found that the model's own confidence separates tumor from healthy
scans about 80 percent of the time, which means the low specificity is a badly-placed decision
threshold rather than an inability to tell the difference, and I proved that retraining the segmenter
to be more cautious is the wrong fix, because it makes the outlines worse. The right fix is a small
dedicated tumor-presence classifier sitting in front of the segmenter as a gate. Third, I would train
on all 9,000 scans instead of the roughly 1,400 I could fit in the time available, because scaling the
data was the single lever that moved accuracy all project, and I never got to see where it tops out.

## How this made me a stronger practitioner

In Week 1 I wrote that my takeaway goal was to learn how to set up a 3D image processing pipeline from
end to end, to step up from the 2D CNN work I had already done into volumetric data, and to prove I
could build something that holds up on real-world data rather than the clean, pre-organized datasets I
first learned on. I hit all three. The pipeline exists and runs end to end, from indexing 9,901 real CT
volumes on an external drive through preprocessing, training, evaluation, model registration, a
deployed inference endpoint, and a clinical review interface. I moved from 2D into 3D and learned what
actually changes, that memory becomes the binding constraint, that you cannot look at a whole volume at
once so how you crop is a modeling decision and not a preprocessing detail, and that a tumor occupying
0.04 percent of a scan breaks the loss functions that work fine on balanced problems.

The real-world part is what I underestimated. Roughly one in eight scans in this dataset had a broken
or empty mask, the volumes ranged from 8 to over 1,000 slices, and the scans came from four different
scanner manufacturers across many institutions. I spent far more time auditing data integrity than I
expected, and that turned out to be the work, not a distraction from it. And I said I would be thrilled
if the result had any real ability to flag cancer, even a modest one. It flags 96 percent of tumors on
a held-out test set I did not choose, with an outline quality near the published Johns Hopkins
benchmark. It is not a solved problem and I can name exactly where it falls short, but it points, at
least roughly, at where a tumor might be, which is what I set out to do. The bigger shift is in how I
work: I now write the bar down before I run the experiment, I assume my own results are wrong until
I have audited them, and I would rather report a smaller number I can defend than a larger one I
cannot.
