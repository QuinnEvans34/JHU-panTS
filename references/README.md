# Reference-material policy

This directory is the catalog for sources used by the PROWL capstone. It is separate from
`docs/`, which contains decisions and implementation plans.

## Directory roles

- `datasets/` — dataset versions, licenses, citations, download sources, checksums, label legends,
  and overlap/exclusion records. Never place raw CT volumes here.
- `literature/` — bibliographic records, search strategies, corpus manifests, question sets, and
  permitted text snapshots used by the evidence assistant.
- `governance/` — approved templates, instructor feedback summaries, evaluation specifications,
  and program requirements.
- `local/` — large, licensed, temporary, or machine-specific reference files. This directory is
  ignored by Git.

## Rules

1. Commit metadata, links, citations, licenses, hashes, and small reproducibility records.
2. Do not commit raw medical images, model checkpoints, licensed full text, secrets, or personal
   data.
3. Record a source version or retrieval date whenever a source can change.
4. A reference may inform a decision, but the resulting decision belongs in
   `docs/capstone/DECISIONS.md` or the relevant implementation plan.
5. Existing root-level reference files will remain in place until the cleanup plan is approved.
