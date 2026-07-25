# M4A1: Tuning, Orchestration & Deployment Report

**Due:** Sunday 11:59pm (available until Jul 31 11:59pm) · **Points:** 30 · **Submit:** website URL or file upload (GitHub: branch → merge to main, inside a `week4/` documentation folder)

## Overview
This week the project transitions from experimentation to production. Tune the selected model, automate the full pipeline, and deploy a working model endpoint. By end of week the system should ingest real-time data, retrain or score on a schedule, and serve predictions via an API — ready for a front-end to consume in Week 5.

## Instructions

### 1. Hyperparameter Tuning — document the tuning process
- What tuning strategy (grid search, random search, Bayesian optimization) and why?
- What hyperparameters were tuned and what ranges were explored?
- Comparison of pre- and post-tuning performance metrics.
- Log all tuning runs in MLflow. Identify and register the final model.

### 2. Final Model Evaluation — evaluate the registered model on the held-out TEST set
- Final performance metrics with interpretation — what do they mean in business terms?
- Confusion matrix, residual plot, or equivalent visualization for the problem type.
- Any limitations, failure modes, or edge cases the model does not handle well.
- For CV tracks: include sample predictions with confidence scores on unseen images.

### 3. Pipeline Orchestration — document the end-to-end pipeline
- A description of each DAG (if real-time data) and task in plain language.
- The trigger mechanism (scheduled or event-based) and frequency.
- How data versioning, model logging, and error handling are managed across the pipeline.
- A diagram or flowchart of the full pipeline from ingestion to model serving.

### 4. Model Deployment — document the deployment
- How is the model registered and versioned in MLflow?
- What does the inference endpoint look like — how is it called and what does it return?
- Include a sample API call and response.
- Note any performance or latency considerations relevant to the business use case.

### 5. Orchestration & Deployment Decisions — one-paragraph reflection
- Key architectural decisions this week, trade-offs weighed, what you'd do differently with more time.

### 6. AI Documentation Files
- `claude.md` — update if context/instructions changed, particularly how AI was used for pipeline/deployment.
- `ai-usage-log.md` — Week 4 entry: tasks assisted, prompts that worked, cases where AI output needed correction.
- `implementation-plan.md` — Week 4 status + final adjustments heading into Week 5.

## Learning Outcomes
- **CO2** — Architect and automate a resilient data and training pipeline.
- **CO3** — Apply experiment tracking, hyperparameter tuning, and evaluation in model development.

## Deliverables (GitHub, inside `week4/`)
- `tuning-orchestration-report.md` — full report covering sections 1–5.
- Pipeline diagram / flowchart as an image file in the folder.
- MLflow screenshots of tuning runs + registered model (in the report or as image files).
- Root `docs/` updated in place: `implementation-plan.md` (Week 4 update), `claude.md` (if applicable), `ai-usage-log.md` (Week 4 entry).

## Rubric (30 pts)
| Criterion | Pts | What "Exceeds" needs |
|---|---|---|
| **Hyperparameter Tuning** | 8 | Strategy justified, ranges intentional, all runs in MLflow, pre/post metrics compared + interpreted, final model registered. |
| **Final Model Evaluation** | 8 | Test-set performance with business interpretation, appropriate visualization, honest limitations/failure modes. |
| **Pipeline Orchestration** | 4 | Full end-to-end pipeline in plain language + diagram; trigger, data versioning, model logging, error handling all described. |
| **Model Deployment** | 3 | Model registered/versioned in MLflow; inference endpoint documented with sample call + response; latency/performance noted. |
| **AI Documentation Files** | 7 | Specific Week 4 entry (esp. pipeline/deployment); honest status with what's at risk / complete heading into Week 5. |

**Note (our project fit):** this assignment is written for a real-time/MLOps pipeline (ingestion → scheduled retrain → API). Our project is a **static research dataset + a 3D segmentation model**, so parts (real-time ingestion, DAGs/scheduled retraining) don't literally apply and must be addressed honestly (document the actual script-based pipeline + justify why no scheduler), while the deployment section is satisfied by building a minimal inference API endpoint.
