# Project Proposal

Project: 3D Pancreas-Aware Pancreatic Lesion Segmentation in Abdominal CT
Dataset: PanTS (The Pancreatic Tumor Segmentation Dataset), Johns Hopkins University
Author: Quinn (solo project)
Date: July 2026

---

## 1. What?

Radiologists and medical imaging annotators regularly have to outline the pancreas and any pancreatic tumor on 3D CT scans, tracing the organ and the tumor slice by slice through a volume that can be hundreds of images thick. Doing this by hand is slow. Just outlining the pancreas can take a trained reader tens of minutes per case, because the pancreas is small, soft edged, and easy to confuse with the organs around it, and the tumor is smaller still. My project builds a tool that does the first pass of that work automatically. It takes an abdominal CT scan and produces a 3D outline (a segmentation mask) of the pancreas and any lesion, and the annotator then reviews it and either accepts, edits, or rejects it instead of drawing everything from a blank screen. In machine learning terms, this is a supervised 3D image segmentation problem, and I am solving it with a patch based 3D U-Net using MONAI and PyTorch. The output the user actually sees is a color coded 3D overlay of the predicted pancreas and lesion, along with a measured lesion volume, shown in a simple viewer they can scroll through.

I want to be clear that this is not a diagnostic system. It does not decide whether a tumor is cancerous, stage disease, or make any clinical call. A human stays fully in the loop and makes every medical decision. The model only speeds up the manual outlining step that comes before that.

The specific user I have in mind is a medical imaging annotator or radiologist working in a research or clinical imaging pipeline, someone who has to produce pancreas and lesion contours for things like research dataset curation, tumor volume measurement, or preparing a case for review. The decision the system supports is simple: for each scan, the user accepts, edits, or rejects the outline the model proposes. The value is that it saves a lot of manual tracing time and gives more consistent outlines, while a qualified person still has the final say.

---

## 2. Why?

I chose this project because it genuinely fascinates me. When I read the paper Johns Hopkins published on the PanTS dataset, it struck me as something I would happily spend a lot of time on, and a big part of the appeal is exactly that it is hard. The fact that even PhD researchers have not been able to push the accuracy very high tells me this is a genuinely difficult problem, which means there is a lot I can learn by working on something where the ceiling clearly has not been reached yet. I am also drawn to the fact that the target is, in a way, invisible. Pancreatic tumors are often something the human eye cannot pick out on a scan, so building a model that can surface something a person would miss feels like exactly the kind of problem worth chasing. I have really enjoyed my previous work with CNNs, and moving from 2D into 3D medical imaging is the next step I most want to take. On a more personal level, Johns Hopkins is a school I would love to attend, and someone in their admissions office told me that working with a dataset they have made public is one of the stronger ways to show I can contribute. So this project sits right at the intersection of what excites me technically and where I want to go next.

---

## 3. Your Takeaway

My main goal is to learn how to set up a 3D image processing pipeline from end to end, stepping up from the 2D CNN work I have already done and enjoyed into volumetric data, which is the capability I most want to add. I would be genuinely thrilled if the result has any real ability to flag cancer, even a modest one, because that would mean the pipeline actually works on a problem that matters. Just as important to me is proving that I can build something that holds up on real world data. These are scans of actual, living people, not the clean, pre organized datasets I first learned on, and getting a model to perform against that kind of messiness is much harder and a skill I really want to own. If I come out of this able to stand up a 3D pipeline that survives real data and points, even roughly, at where a tumor might be, I will consider it a success.

---

## 4. Tech Stack

Here is everything I plan to use, from the data all the way to the interface, with a note on whether it is familiar to me or new, and how I plan to get up to speed on the new pieces.

- Python is my main language, and I am comfortable with it.
- The data is the PanTS dataset, which comes as NIfTI CT volumes and masks. This format is new to me, so I am reading the PanTS paper and GitHub README and starting with a small subset.
- For reading the medical images I am using NiBabel and SimpleITK, both new to me. I am learning them through the MONAI tutorials and each library's quickstart.
- MONAI is my main 3D deep learning framework, and it is the biggest new thing I am learning. I am working through its official 3D segmentation tutorials and transform documentation.
- PyTorch is the backend underneath it. I am comfortable with it in 2D, but working in 3D is new to me.
- The model is a 3D U-Net, specifically the SegResNet variant, built through MONAI. The architecture is new to me, so I am studying the reference implementations.
- NumPy and pandas handle the numbers and the manifest of cases, and I am comfortable with both.
- scikit-learn handles the train, validation, and test splitting, and MONAI provides the Dice and IoU metrics.
- Matplotlib is for the slice overlays and failure cases, which I have used plenty before.
- MLflow is my experiment tracker for the loss and accuracy curves. It is new to me but straightforward to pick up.
- PyYAML drives the config, which lets the same code run the different levels of the project.
- For the front end I am building a clean web app with React and NiiVue, a WebGL viewer made for medical images, styled with Tailwind. This is new to me and I plan to build it in Week 5, learning from the NiiVue and React docs. It reads predictions that were computed ahead of time, so it does not need a live backend for the demo.
- I am training on my 14 inch MacBook Pro with the Apple M5 Pro chip, which has a 20 core GPU and 64 GB of shared memory. Training runs on PyTorch's MPS backend instead of CUDA, which is a little new to me since some operations behave differently on Apple Silicon.
- The full dataset lives on an external drive, which keeps it off my laptop and out of the repo, and the path is set through config.
- For version control I am using Git and GitHub with a branch and merge workflow.

---

## 5. Dataset Validity

- The dataset is PanTS, the Pancreatic Tumor Segmentation Dataset, created by Johns Hopkins University and published at NeurIPS 2025.
- It is open source, released under the CC-BY-NC-SA-4.0 license, which is non commercial and share alike. My project is academic and non commercial, so that fits, and I am not making any commercial product claims.
- The sources are the GitHub repo at https://github.com/MrGiovanni/PanTS, the Hugging Face page at https://huggingface.co/datasets/BodyMaps/PanTSMini, and the paper at https://arxiv.org/abs/2507.01291.
- It is not a real time dataset, and I confirmed that directly. PanTS is a static, versioned research benchmark, not a daily or weekly feed, so there is no live ingestion. I download it once and use it as a fixed set.
- The full dataset has 36,390 CT volumes from 145 medical centers, with voxel level masks for pancreatic tumors, the pancreas head, body, and tail, and 24 surrounding structures. The public mini release that I am using has 9,000 training and 901 test volumes, which comes to about 346 GB.
- To access it, I clone the PanTS repo and run the provided download scripts. Because the full set is so large, I develop on a local subset with patch based training, and I never commit the raw data to the repo (my .gitignore enforces that).
- For my main target, each CT volume maps to a three class mask: 0 for background, 1 for pancreas, and 2 for the lesion.

---

## 6. ML Approach and Pipeline Plan

This is a supervised 3D image segmentation problem. For every voxel in the CT volume, the model classifies it as background, pancreas, or lesion. It is not detection, and it is not whole image classification.

I chose the 3D U-Net, and specifically the SegResNet variant, because it is the established standard for this kind of volumetric medical segmentation. Its encoder and decoder design with skip connections keeps the fine spatial detail you need to outline small structures, and MONAI gives me well tested implementations along with the transforms and sliding window inference I need. The hardest part of this problem is the extreme class imbalance, since the lesion is such a tiny fraction of the whole volume. I handle that in two ways: a Dice based loss (Dice combined with cross entropy, or a Dice Focal loss) that holds up under imbalance, and patch sampling that deliberately pulls a high fraction of patches that actually contain a lesion, so the model sees enough tumor during training. I also train the pancreas and the lesion together rather than the lesion alone, because segmenting the pancreas gives the model anatomical context, and that is why the pancreas aware version is my main target instead of a tumor only model.

The end to end flow goes like this. I start from the PanTS NIfTI files, which are the CT volumes and their masks, and build a manifest that pairs each scan with its label files and records whether it has a lesion. From there the data goes through MONAI preprocessing, which loads it, reorients it to a standard orientation, resamples it to a common voxel spacing, and windows the CT intensities into a soft tissue range before scaling everything to a 0 to 1 range. I split the cases by patient into training, validation, and test sets, and I am careful never to split by slice, which would leak information between them. Training happens on 3D patches with the positive and negative sampling and some light augmentation. Those patches go into the SegResNet, which is optimized with a Dice based loss and the AdamW optimizer. For evaluation I run sliding window inference across the full volume rather than scoring on patches, and I report the pancreas and lesion accuracy separately, because a single average would hide poor tumor performance. Finally, the saved predictions feed the viewer, where the user sees the outlines and the measured lesion volume.

The whole thing is config driven, so the same code can run three levels of the project. Level 4 is a lesion only mask with two classes, which is a riskier baseline that I build but is not my focus. Level 4.5 is the pancreas plus lesion version with three classes, and that is my primary target. Level 5 is the full multi structure version, with the pancreas subregions and the surrounding structures, at around 28 classes, and that is a stretch goal I can turn on by changing a config file once 4.5 is working.

One thing I built into the plan from the start is a discipline around how I evaluate. I use patient level splits, I always evaluate on full volumes with sliding window inference, I report the pancreas and lesion separately, and before any real training I run an overfit test on a single case to prove the pipeline is wired correctly.

---

## 7. Business-Facing Layer

The thing the user actually touches is a clean web app I am building with React and NiiVue, which is a WebGL viewer made for medical images. It makes no clinical device claims. For a given CT case, the user can do a few things. They can see the CT with the predicted pancreas and lesion overlaid in color across the axial, coronal, and sagittal views. They can scroll through the slices and toggle each mask on and off to compare the model's outline against the actual scan. They can read a short summary panel that shows the predicted lesion volume in cubic millimeters, whether a lesion was detected at all, and a confidence flag for cases the model is unsure about. And they can export the predicted mask so it can be opened in a real annotation tool like 3D Slicer and edited, which is the actual accept, correct, or reject step.

Put simply, the user loads a scan, sees the proposed pancreas and lesion outline from three angles with a measured lesion volume, and accepts or corrects it instead of drawing it from scratch.

---

## Open Items I Am Still Settling

- The patch size, which I plan to tune to whatever my laptop's memory and the MPS backend can handle well, rather than fixing a number up front.
- The exact size of the development subset I download, which I am aiming somewhere around 50 to 150 cases with a healthy fraction of tumor cases.
