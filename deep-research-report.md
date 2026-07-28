# PanTS lesion segmentation evaluation on a time budget

## Executive judgment

Your approach is reasonable **if** you define the task narrowly as **conditional lesion segmentation given that a tumor is present**. It is **not** reasonable if you present that number as your model’s overall performance on PanTS. PanTS is set up as a mixed-cohort benchmark with both tumor-positive and tumor-negative scans, and the official benchmark reports not just Dice but also patient sensitivity, tumor sensitivity, specificity, and AUC. The current public release is organized as **PanTS-tr with 9,000 cases** and **PanTS-te with 901 cases**, while Johns Hopkins also keeps much larger hidden out-of-distribution test cohorts for third-party evaluation. If you only score tumor-positive cases, you are changing the evaluation target from “PanTS benchmark performance” to “conditional segmentation quality on positives,” which is valid only if you label it exactly that way. citeturn34view2turn34view0turn20view3turn38view0

So the short answer is:

**Use the full held-out PanTS test split for your final evaluation.**  
Within that evaluation, it is fine to report **lesion Dice on tumor-positive scans as your primary lesion-overlap metric**, because Dice is widely recommended for highly imbalanced medical segmentation tasks and focuses on the positive class rather than getting inflated by massive background true negatives. But you should pair that with **at least one negative-case control metric** on the full test set, such as specificity or false-positive tumor volume per case. If you do not, the result will look cherry-picked. citeturn38view0turn38view2turn34view0turn20view3

A second point: Claude’s suggestion to make training more lesion-heavy is directionally right, but the clean version of that idea is **oversampling positives or tumor-centered patches**, not **throwing away negatives entirely**. Recent PanTS work explicitly uses weighted sampling across tumor-positive and tumor-negative cases and biases patch extraction toward tumor-centered regions to handle class imbalance. That is very different from training only on positives. citeturn20view3turn36search1

## What PanTS actually benchmarks

PanTS was built as a large-scale pancreatic CT benchmark, not just a lesion-mask repository. The paper describes a total corpus of **36,390 CT scans from 145 medical centers**, with annotations for pancreatic tumors, pancreas head/body/tail, and 24 surrounding anatomical structures. The public-facing benchmark setup now exposed in the GitHub repository splits the public portion into **9,000 training** and **901 in-distribution test** cases, while Johns Hopkins retains much larger external out-of-distribution cohorts for centralized evaluation. That matters because the authors explicitly designed PanTS for **detection, localization, and segmentation**, not only segmentation. citeturn5view0turn34view2

PanTS is also highly imbalanced. In the paper’s public-partition accounting, the training partition had **1,076 tumor-positive scans out of 9,901**, or about **10.8% positive prevalence**. The hidden paper-level test partition had a similar tumor-positive proportion. In other words, the default problem is not “segment the tumor in an all-positive dataset”; it is “find and segment tumors in a mostly negative abdominal CT population.” That is exactly why the public benchmark table includes **patient sensitivity, tumor sensitivity, specificity, AUC, and DSC** rather than Dice alone. citeturn7view2turn34view0

Your choice to focus on segmentation rather than diagnosis is still aligned with the dataset’s scientific logic. PanTS was built around voxel-wise anatomy and lesion labels, and the authors show that adding richer anatomical context materially improves tumor segmentation: their comparison between a **2-class setup** and a **28-class setup** raised mean tumor Dice from **57.4% to 67.7%**. That strongly supports your decision to model pancreas and lesion jointly rather than build a pure yes/no classifier. citeturn6view2

## When tumor-positive-only Dice is valid

From a metric-design standpoint, Dice is a defensible primary metric for lesion segmentation. A widely cited evaluation guideline for medical image segmentation argues that in extreme background-heavy settings, metrics dominated by true negatives can be misleading, and that overlap metrics like **DSC** and **IoU** are preferred because they focus on the region of interest rather than rewarding background pixels. The same guideline also points out that lesion segmentation is intrinsically harder than organ segmentation because lesions are smaller and more variable. citeturn38view0

That said, Dice has a known limitation in lesion problems: it gives only a partial picture when the number of target objects is not known a priori or when the evaluation pool mixes positive and negative cases. A Johns Hopkins lesion-evaluation paper states that Dice is useful as a standardized overlap measure, but it offers a **“very limited picture”** in complex lesion segmentation tasks where the number of target objects is unknown, because algorithms can differ in important ways not reflected by Dice alone. citeturn38view2

Applied to your case, that means the following.

If you report:

- **Lesion Dice on tumor-positive scans only**

that is a **valid conditional segmentation metric**.

If you report:

- **Lesion Dice on tumor-positive scans only**  
and imply it is your overall PanTS test performance,

that is **not valid benchmark reporting**.

The reason is simple: once you exclude tumor-negative scans, you stop evaluating false-positive behavior on the cases where the model should predict nothing. PanGuide3D makes this distinction very clearly. It notes that PanTS contains many tumor-negative scans, so models must learn to suppress false positives, while the older MSD Task07 cohort is **entirely tumor-positive**, meaning performance there is dominated by delineation quality rather than negative-case rejection. citeturn20view3

So: **positive-only Dice is valid as a conditional statement, not as a whole-benchmark statement**. If you want to present it confidently, call it exactly what it is: **“Lesion Dice on tumor-positive PanTS-te cases.”** Then pair it with one or two full-test metrics that expose false positives on negative scans. citeturn20view3turn34view0

## How a 0.47 lesion Dice compares publicly

A lesion Dice of **0.47** is not ridiculous at all. It is actually in a credible range for pancreatic tumor segmentation.

The current public PanTS benchmark table in the official repository is still sparse, but the two visible entries are **MedFormer at 52.9% DSC** and **R-Super at 53.4% DSC** on the official in-distribution PanTS test set. R-Super is explicitly marked as using **additional external data** in the form of **1.8K pancreatic lesion reports**, so that number is not a pure like-for-like comparison against a simple transfer-learning baseline. The same table also shows that PanTS benchmarking is not Dice-only: MedFormer and R-Super are reported with patient sensitivity, tumor sensitivity, specificity, and AUC alongside Dice. citeturn34view0turn34view1

A more comparable research number comes from **PanGuide3D**, which trained on PanTS and reported **0.460 ± 0.041 tumor Dice on PanTS** and **0.475 ± 0.069 on MSD** under its own matched preprocessing and fold setup. That is not the official PanTS leaderboard, and its PanTS split is not identical to the official public benchmark split, but it shows that a tumor Dice around **0.46–0.48** is very much within the range that recent pancreas-tumor segmentation work is reporting. PanGuide3D also reports that plain nnU-Net can collapse badly under cohort shift, while pancreas-aware guidance tends to improve both overlap and false-positive control. citeturn13view0turn20view3

Public MSD numbers tell a similar story. The original Medical Segmentation Decathlon paper described pancreas tumor segmentation as one of the two hardest tasks in the benchmark, with the original challenge median tumor Dice around **0.21**. Later public engineering work improved on that substantially: MONAI’s Swin UNETR discussion reports **Task07 tumor Dice around 0.51–0.58 across validation folds**, and NVIDIA’s MONAI DiNTS bundle for Task07 reports a **mean Dice of 0.62 across both pancreas and tumor structures combined**, not tumor-only. Those are not directly comparable to your PanTS lesion Dice, but they show that pancreatic tumor segmentation is generally a hard problem where scores in the 0.4–0.5 band are not embarrassing. citeturn8search0turn28view1turn28view0

So the blunt reading is this: **0.47 lesion Dice is good enough to take seriously, but not strong enough to claim you solved PanTS.** It is probably a respectable result for a constrained setup on a Mac with partial training, especially if you are using **SegResNet** rather than a heavier transformer. SuPreM’s own model zoo lists the SegResNet backbone as only **4.70M parameters**, with released pretrained weights specifically for SegResNet, U-Net, and Swin UNETR; that makes your backbone choice technically sensible for a lower-resource environment. citeturn15view0

## What similar public work and datasets exist

There is public work in this space, but the ecosystem is still fragmented.

On **PanTS specifically**, the public benchmark is still early. The official repository literally says it is **“calling for more baseline methods”**, and in the visible benchmark table several rows—including **SuPreM**—are still blank. That means there is not yet a deep, stable public leaderboard for PanTS where you can easily compare your exact architecture against ten other papers. This is important: if you use SuPreM + SegResNet on PanTS, you are not walking into a saturated benchmark. citeturn34view0

What *is* public already is a set of adjacent or overlapping projects:

**R-Super** uses PanTS masks plus external pancreatic lesion reports and explicitly says it uses the **official PanTS train/test split** in its public demo. Its visible benchmark entry on the PanTS repo reaches **53.4% DSC** with external report supervision. citeturn3view4turn34view0

**PanGuide3D** trains on PanTS and tests both in-cohort and out-of-cohort on MSD, reporting tumor Dice, tumor sensitivity, patient sensitivity, pancreas Dice, and false-positive volume. Its training recipe uses **tumor-centered patch sampling** and a **weighted sampler** over tumor-positive and tumor-negative cases, which is exactly the kind of lesion-heavy but not lesion-only strategy that makes methodological sense. citeturn13view0turn20view3

Public engineering stacks around **MSD Task07** are common. The dataset itself consists of **420 portal-venous CT scans** from **Memorial Sloan Kettering**, targeting **pancreas and pancreatic tumor** segmentation. NVIDIA/MONAI publishes a DiNTS bundle for this task, and MONAI discussions and tutorials explicitly use Task07 as a segmentation benchmark rather than a diagnostic benchmark. In other words, a lot of the public scene is already doing what you want to do: **segment pancreas and tumor, not diagnose healthy vs unhealthy from scratch**. citeturn22search8turn28view0turn26search5turn26search3

Outside Johns Hopkins, public pancreatic CT resources do exist, but they are thinner than PanTS.

**MSD Task07** is the classic public tumor benchmark. It is effectively a lesion-focused segmentation cohort because it consists of patients undergoing resection of pancreatic masses, and PanGuide3D explicitly contrasts it with PanTS by noting that MSD is **entirely tumor-positive**. citeturn22search8turn20view3

**PANORAMA** is the biggest non-JHU public CT resource in this area, with **2,238 contrast-enhanced CT scans** and a challenge design centered on **PDAC detection/diagnosis**. Its public labels repository says there are **676 PDAC cases**, of which **482 have manual lesion annotations** and **194 have automatically generated lesion segmentations**. PANORAMA is useful, but it is narrower than PanTS: it is PDAC-oriented and does not cover the same tumor-type diversity that PanTS claims. citeturn24view1turn24view2turn21search21

**NIH Pancreas-CT** is public but not lesion-focused. It contains **82 contrast-enhanced CT scans** from the NIH Clinical Center with pancreas annotations, and many of the subjects have morphologically normal pancreas. It is useful for pancreas segmentation, not as a primary tumor-mask benchmark. citeturn23search1turn23search21

**Pancreatic-CT-CBCT-SEG** is also public, but it is really a radiotherapy/registration dataset: **40 patients** with planning CT and CBCT acquired during ablative radiation therapy for locally advanced pancreatic cancer. It is useful for specific technical questions, not as a general benchmark for pancreas-lesion segmentation in routine abdominal CT. citeturn21search23turn21search7

The PanTS paper itself summarizes the broader picture well: public pancreatic tumor datasets remain relatively scarce, and before PanTS the main public sets were small single-center resources such as **NIH Pancreas-CT**, **Pancreatic-CT-CBCT-SEG**, and **CPred-Sunitinib-panNET**, with **PANORAMA** as the main larger-scale predecessor. The same paper argues that PanTS is larger and more diverse than those prior public resources. citeturn5view0turn7view4turn37search9

## A reporting protocol you can defend

If you want a result you can present without looking like you graded your own exam, do this.

Report the model on the **full PanTS-te held-out set**. Then report a **segmentation-first metric bundle** that separates overlap quality from false-positive behavior:

- **Pancreas Dice on all test cases.** The pancreas exists in every scan, so this is clean and comparable. citeturn5view0turn34view0
- **Lesion Dice on tumor-positive test cases only.** Call it exactly that. Do not call it “PanTS test Dice” without the qualifier. citeturn38view0turn20view3
- **Patient sensitivity or tumor sensitivity on tumor-positive cases.** These are already part of the official PanTS benchmark language. citeturn34view0
- **Specificity or false-positive tumor volume on the full test set.** This is the minimum protection against the criticism that you ignored hallucinated tumors in negative scans. PanGuide3D uses false-positive tumor volume for exactly this reason. citeturn13view0turn20view3

If you only have time for one final experiment, the best single move is **not** to make the test set positive-only. The best single move is to run **one full-split evaluation** and then compute **conditional lesion Dice on the positive subset** plus **one whole-split false-positive metric**. That gives you a result that is both aligned with your scientific goal and still defensible against the obvious objection. citeturn34view0turn20view3turn38view2

For training, use a **lesion-heavy sampling strategy**, not a **lesion-only training corpus**. The most defensible version is: keep negatives in the training pool, but oversample tumor-positive cases and/or tumor-centered patches. That matches how recent PanTS work handles the class imbalance problem. If you train only on positives, you are likely to improve conditional Dice at the expense of false-positive control, which is fine for a toy ablation but weak as a final reported model. That last sentence is an inference, but it follows directly from PanTS’s low prevalence, the benchmark’s inclusion of specificity, and recent PanTS-style sampling practice. citeturn7view2turn34view0turn20view3turn36search1

The cleanest way to present your current result would be something like this:

**“Using SuPreM-initialized SegResNet on a compute-constrained setup, we obtained a lesion Dice of 0.47 on a held-out validation subset. For final reporting, we evaluate on the full PanTS-te split and report pancreas Dice on all cases, lesion Dice on tumor-positive cases, patient/tumor sensitivity on positives, and false-positive control on the full test set.”** That framing is technically honest, aligned with the benchmark, and does not pretend a positive-only Dice is the same thing as overall benchmark performance. citeturn15view0turn34view0turn20view3turn38view0