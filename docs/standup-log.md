# Standup Log

Daily check-ins (Mon–Fri), added chronologically. Brief and honest — 3–5 sentences. **Do not edit or delete past entries.** In Weeks 1, 3, and 5, one entry is a 1-on-1 retrospective instead of the standard format.


All daily stand up entries were written by myself, and then cleaned up by AI for clarity. I believe this to be necessary due to this portion of the grading rubric: Treat it as a document you would be comfortable showing an employer.

**Standard entry template:**

```
## [Week X — Day] — [Date]
**Worked on:** What I actually worked on today.
**Up next:** What I'm doing next session.
**Blockers:** Any challenges/blockers, or "None."
```

**1-on-1 retrospective template (Weeks 1, 3, 5):**

```
## [Week X — 1-on-1 Retrospective] — [Date]
**What we discussed:** ...
**Feedback received:** ...
**Action items:** ...
**Reflection:** ...
```

---

## [Week 1 — Monday] — 2026-06-29
**Worked on:** I set up the project repository and added the three assignment briefs so I have that context saved in the repo. I decided I want to use the PanTS dataset, though the project still needs to be approved before I fully commit to it. I looked into as many details as I could: the dataset comes from Johns Hopkins University, it was released at the end of 2025, and there is a mini release that is around 346 GB, which is very large. I also spent time researching how I want to approach the project, and I settled on using a 3D CNN to identify the pancreas and its lesions. The main stakeholders would be hospitals and radiologists who have to read these scans.
**Up next:** Confirm the details of my hardware, scaffold out the code repo (configs, src, scripts), and download a small local subset of PanTS to work with.
**Blockers:** None.

## [Week 1 — Tuesday] — 2026-06-30
**Worked on:** Today was a big planning day, and the project was approved so I can move forward. I spent most of my time locking down the scope and the technical plan. I decided the main goal will be to segment the background, the pancreas, and the lesion, and then wrap that in a tool that flags "there could be a tumor here" instead of trying to actually diagnose anything, which keeps the project realistic and honest about what it can do. For the model, I chose to use a SegResNet and fine-tune it from a pretrained model called SuPreM that comes from the same Johns Hopkins lab, and I am going to compare that against a version trained from scratch so I can actually measure whether the pretraining helps. I also ran my whole plan through ChatGPT's deep research mode to get a second opinion, and it agreed with my model choice, which made me a lot more confident. I wrote all of my design decisions into a set of documents so that everything is planned out before I start coding, and I set up the external hard drive that will hold the dataset.
**Up next:** Download the dataset and the pretrained model onto the external drive, look at the real files to confirm exactly how everything is structured, and then start setting up the environment and the code.
**Blockers:** None.

## [Week 1 — 1-on-1 Retrospective] — 2026-07-01
**What we discussed:** I walked my instructor through the whole project, and we mostly talked about whether it is realistic to finish in five weeks and how the model actually works. We also talked about why I am personally interested in this, and the fact that I am thinking about carrying it forward as my capstone project.

**Feedback received:** The feedback was mostly positive. He asked a lot of good questions about how the project will actually work, the type of model I chose, how big the dataset is, and how I am storing the CT scans on my laptop and external drive. The part I was most excited about was when he asked if I could use 3D images in the UI, because that was already exactly my plan. I told him I want to build the interface around a 3D visualization of the pancreas and the tumor, so it was cool to already be on the same page.

**Action items:** My main action item is to go a lot deeper on the model itself, including how it works, how it learns, and the specific details of the SuPreM SegResNet I am using, so that I can clearly explain and defend why it is the best choice to both my classmates and my instructor. The model is the most complex part of this project, and it is where I most need to level up.

**Reflection:** A couple of things surprised me. First, how good the dataset is; the quality of the pancreas annotations really impressed me. Second, how much storage it takes, which ended up being around 410 GB on my drive. My biggest takeaway is that the model is the hardest part of this whole thing, so that is where I am going to focus my learning.

## [Week 1 — Thursday] — 2026-07-02
**Worked on:** I finished getting the full dataset downloaded, which turned out to be around 410 GB once everything was on the external drive. It was not totally smooth, because I had to work through a compatibility issue with the download scripts on macOS and a point where the drive disconnected in the middle of the download, but I got it all down and verified that everything is complete. I also looked at real cases for the first time and saved slice views of the CT with the pancreas and lesion outlines to make sure the data and the labels actually line up, and they did. On top of that, I gave my Week 1 pitch to the class and turned in my audience notes on Ted's, Gracie's, and Porter's presentations. Before the pitch I spent a good amount of time researching the model I chose using ChatGPT so that I could explain and defend it well.
**Up next:** Start building the actual code for the project, including the utilities, the manifest that pairs each scan with its labels, and the train and validation splits, and then move into the preprocessing and a sanity check.
**Blockers:** Nothing major, but I am on Python 3.14 and I need to make sure all of the machine learning libraries install cleanly before I get into training.

## [Week 1 — Friday] — 2026-07-03
**Worked on:** Today I built out the entire pipeline in code and got the model training for the first time, which felt like a big step. I wrote the code that builds a list of every scan and its labels, and when I ran it on the full dataset it confirmed that each scan is its own patient and that about 10.4% of the cases actually contain a tumor. I also wrote the code that splits the data by patient into training, validation, and test sets, then the preprocessing and a sanity check that ran on a real case and produced correct pancreas and lesion overlays, which was my Week 1 milestone. After that I wrote the model itself, matched it to the pretrained SuPreM weights, and added the loss, metrics, and training loop, and I ran an overfit test where the pancreas score climbed from zero up to about 0.89, which proved the whole pipeline works from end to end. By the end of the day I also got the lesion itself to start being detected, reaching around 0.7 on the overfit test once I adjusted the loss and made sure I was training on cases that actually have tumors, and I added a proper validation step and kicked off a real training run that is going overnight. I also ran into and fixed a lot of real problems along the way, including having to move my environment from Python 3.14 to 3.12 because 3.14 would not install MLflow.
**Up next:** Check the validation results in the morning to see how well the model generalizes to scans it has not trained on, then compare the pretrained model against the from-scratch version and start tuning from there. I plan to keep working through the weekend.
**Blockers:** The lesion score was reading zero at first, but I figured out that it was because my first test cases happened to have no tumor, and once I trained on tumor-positive cases it started learning. The main ongoing constraint is that training on my laptop's GPU is slow, so the runs take a while.




## [Week 2 — Monday] — 2026-07-06
**Worked on:** I moved from setup into really understanding the data and the model this week, and today was a big one. I built the Week 2 EDA notebook straight from my real manifest of 9,901 cases, so every chart in it is the actual data, not a placeholder. The findings that matter: only about 10 percent of scans have a tumor, lesion size spans five orders of magnitude with a median around 4,700 cubic millimeters, and the scans are wildly inconsistent in geometry (8 to over 1,000 slices), which is exactly why I resample everything to a common grid. My label also agrees with the dataset's own tumor flag 99.6 percent of the time, which gave me confidence the pipeline is wired right. I wrote the full data understanding report around those numbers, and I ran a proper evaluation of my current model.
**Up next:** Draft the Week 2 presentation and audience notes, and kick off a retrain with balanced patch sampling so I open Week 3 with fresh numbers.
**Blockers:** The evaluation exposed the real problem: my model finds tumors (pancreas Dice 0.72, lesion 0.17) but it over-predicts badly, with only 8 percent specificity on healthy scans, and my post-processing did not fix it. That is not really a blocker, it is the main thing I now have to solve, and I have a concrete plan for it in the implementation plan.
