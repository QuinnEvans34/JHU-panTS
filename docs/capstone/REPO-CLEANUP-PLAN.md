# Repository cleanup plan

**Status:** Proposed; safe routing changes started, no historical files moved or deleted  
**Audit date:** 2026-09-07

The repository is not broken, but it currently mixes a completed five-week project, proposal
development artifacts, new capstone research, large ignored outputs, vendor code, and active source.
Cleanup must make the next action obvious without destroying provenance or breaking old links.

## Audit findings

- The root contains every proposal/appendix version plus program templates and source data notes.
- `docs/` contains more than 50 Markdown files spanning current research, completed assignments,
  superseded capstone drafts, audits, and build sources.
- `docs/capstone-planning.md` is a 1,288-line research log containing both strong evidence and dead
  ideas; it cannot safely serve as the execution plan.
- `docs/experiments.md` is a 1,945-line experiment history with existing uncommitted changes. It must
  be preserved and never mechanically reorganized during cleanup.
- `outputs/` is roughly 354 GB and ignored, which is appropriate for derived local artifacts but
  requires a retention/backup plan.
- `ui/` is roughly 547 MB locally, largely because installed/build artifacts are present and ignored.
- `MedFormerPanTS/` is an untracked vendor/reference tree of roughly 582 MB.
- The `.gitignore` entry `data/` unintentionally matched `src/data/`, hiding the core dataset and
  transform modules from Git. It was changed to `/data/` on 2026-09-07 so only a root raw-data
  directory is ignored. The newly visible source files still require deliberate review before add.
- Neither available Python environment currently has `pytest`, so the existing 37 test functions
  cannot be run from the documented environment.

## Target topology

```text
docs/
├── README.md                    # routes active vs historical documentation
├── capstone/                    # active capstone plans and control documents
│   ├── README.md
│   ├── MASTER-PLAN.md
│   ├── DECISIONS.md
│   ├── RISK-REGISTER.md
│   ├── REQUIREMENTS-TRACEABILITY.md
│   ├── implementation/
│   ├── templates/
│   └── weeks/
├── [existing technical/history files]
└── archive/                     # optional later, only after link-safe move approval

references/
├── README.md
├── datasets/                    # versions, licenses, labels, overlap/exclusion records
├── literature/                  # corpus/search/evaluation metadata
├── governance/                  # course requirements and feedback records
└── local/                       # ignored large/licensed/machine-specific sources
```

## Phase 1 — safe additions and visibility fixes

These changes do not relocate or delete existing evidence:

- [x] Create `docs/README.md` and the active `docs/capstone/` hub.
- [x] Add active-phase banners to `README.md` and `AGENTS.md`.
- [x] Create `references/` policy and local-only ignored area.
- [x] Root-anchor `/data/` in `.gitignore` so `src/data/` is no longer hidden.
- [ ] Review `src/data/dataset.py`, `src/data/transforms.py`, and `src/data/__init__.py`; then add them
      in a dedicated, understandable change if they are the intended current source.
- [ ] Add a documented development/test dependency path and verify all tests from a clean command.
- [ ] Inventory ignored output artifacts by type, reproducibility, and keeper status.

## Phase 2 — classify without moving

Create an inventory assigning each existing file one role:

- **Active source** — implementation used by the capstone.
- **Active evidence** — experiment/audit/reference needed for decisions.
- **Completed deliverable** — immutable course output.
- **Proposal history** — preserved but not active.
- **Generated/rebuildable** — can remain ignored with a recipe.
- **Local reference/vendor** — not project-owned source.
- **Unknown** — no move until ownership is resolved.

This classification must be reviewed before physical reorganization.

## Phase 3 — proposed non-destructive moves

Do not execute this phase without Quinton's approval and a link audit.

1. Keep approved proposal and appendix filenames explicit. If moved, put every version under a
   version-preserving `artifacts/proposals/` hierarchy; do not rename them `final` and do not delete
   earlier versions.
2. Move superseded proposal Markdown and build sources to
   `docs/archive/proposal-development/`, preserving filenames.
3. Keep completed course deliverables together. Moving `deliverables/week*` is optional and likely
   not worth the link churn; a clear historical label may be cleaner than relocation.
4. Move one-off proposal generation/revision scripts only after recording which document each
   produced. They are provenance, not junk.
5. Replace the untracked `MedFormerPanTS/` vendor checkout with a reference record containing source
   URL, commit, license, and local checkout instructions; move the working copy to
   `references/local/` rather than deleting it.
6. Move root-level `panorama_manual_ids.txt`, `pubmed_samples.xml`, and similar files only after the
   data/retrieval plans define whether they are authoritative inputs, samples, or disposable probes.

## Phase 4 — generated-artifact retention

Before removing any derived artifact, classify it:

- **Keeper:** required for a reported result or demonstration; back up with manifest and checksum.
- **Reproducible:** safe to regenerate from committed inputs/config/code; record the recipe.
- **Orphan:** provenance cannot be reconstructed; quarantine until resolved.
- **Disposable:** verified temporary output not referenced anywhere.

No bulk deletion is authorized by this plan. Material deletion requires an explicit target list and
recovery statement.

## Acceptance gate

Repository cleanup is complete when:

- a new contributor can identify the active capstone plan in under one minute;
- a clean clone contains every required source module;
- the test suite runs from one documented environment command;
- approved proposal/appendix versions and historical evidence are preserved;
- active documents contain no unresolved contradictions with the approved scope;
- raw/large/licensed materials remain excluded from version control;
- root-level and `docs/` files have documented roles;
- all links pass after any approved moves.

## Recommendation

Complete Phases 1–2 during Week 1. Delay broad moves until the architecture, data, and retrieval
plans establish where each source belongs. The current problem is ambiguity, not directory depth;
the active hub fixes the immediate ambiguity without risking the historical record.
