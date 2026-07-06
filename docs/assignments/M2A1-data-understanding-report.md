# M2A1: Data Understanding Report

> Due Sunday by 11:59pm · Points: 30 · Submit via GitHub · Available until Jul 19

## Overview

Move from proposal assumptions to validated reality. By the end of the week the dataset is ingested, cleaned, and understood well enough to make confident model decisions. Also finalize Core Requirements and the Proposed Schedule now that the data is real. The report is a living document referenced in future weeks when justifying modeling decisions.

## Required sections

1. Data Source & Ingestion
   - Source, access method (API, scheduled download, scrape), and update frequency.
   - How ingestion is automated using Airflow, including a brief description of the DAG structure.
   - Any surprises or changes from what was proposed in Week 1.
2. Data Profile
   - Row/column counts, data types, time range covered.
   - Missing values, duplicates, anomalies found and how they were handled.
   - Key statistical summaries for the most important features (mean, range, distribution shape).
   - Corrupted files (unreadable images, truncated files)? What percentage is usable out of the box?
   - Final counts (for 2D/3D vision: total images and spatial dimensions).
3. For Classical ML / Tabular (not applicable to this project).
4. For Deep Learning / Unstructured Data:
   - Ingestion Pipeline Architecture: how data goes from storage to GPU. Show the PyTorch Dataset/DataLoader code snippet. How batching and shuffling are handled.
   - Data Transformation & Standardization (2D/3D vision): spatial resizing, normalization, volumetric resampling (e.g., isotropic voxel spacing for 3D).
   - The "Overfit a Single Batch" Test: take 2–5 samples, pass them through the network, train until loss ~0, and provide the training curve graph proving the network can overfit the mini-batch.
5. Revised Core Requirements & Schedule
   - Finalize Core Requirements and the Proposed Schedule now that data is validated. Requirements must be granular, specific, and measurable.
   - implementation-plan.md: living 5-week plan of execution; add to it, do not rewrite history.
   - schedule.md: maps finalized Core Requirements to specific weeks with clear milestones.
6. Context Files (initialized/updated this week, maintained weekly):
   - claude.md: AI context file (project goal, how Claude should assist, tone/scope/constraints, best practices).
   - ai-usage-log.md: weekly running log (tasks AI assisted with, prompts/context that worked, cases needing correction).

## Deliverables

Submit via GitHub (branch → merge to main, inside a `week2/` documentation folder):

- `data-understanding-report.md` — full report covering sections 1–5.
- `eda-notebook.ipynb` — EDA notebook with all visualizations and analysis.

Live in root `docs/`, updated in place each week (not duplicated into weekly folders):

- `claude.md` — initialized/updated this week.
- `implementation-plan.md` — finalized this week with revised requirements and schedule.
- `ai-usage-log.md` — Week 2 entry added.
- `schedule.md` — schedule with core requirements and clear timeline.

## Rubric (30 pts)

| Criterion | Description | Pts |
|-----------|-------------|-----|
| Ingestion & Pipeline | Source, access method, update frequency confirmed and documented. Airflow DAG live (for real-time data) and documented. Deviations from the proposal explained. | 6 |
| Data Profile & Cleaning | Shape, types, missing values, duplicates, anomalies fully documented. Cleaning decisions explained and justified, not just listed. | 6 |
| Data Processing Pipeline | At least 3 visualizations with interpretation that goes beyond description and connects to the ML problem. All planned features listed with justification + transformations. Choices reflect EDA. Ingestion, standardization, transformation covered. | 12 |
| AI Documentation Files | Updated context files and usage plan. | 6 |
