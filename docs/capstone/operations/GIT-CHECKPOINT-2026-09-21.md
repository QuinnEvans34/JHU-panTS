# Git checkpoint — September 21, 2026

User authorized practical local commits and non-destructive cleanup, not a perfectly tidy checkout.
No push, historical rewrite, file deletion, or external-drive access is part of this checkpoint.
Quinton reports the drive mounted again; its identity/readiness was not revalidated here.

## Included

- Capstone plans, contracts, decision records, reference catalogs, and living experiment notebook.
- Workspace/storage/acquisition safeguards, example configuration and schema (not real roots),
  dependency locks, synthetic tests, and required previously untracked `src/data/` source code.
- UI toolchain configuration and synthetic test foundation.

## Data and secret boundary

The root-anchored `/data/` ignore rule preserves data exclusion without hiding `src/data/`.
Additional ignores cover common medical-image/array/model/archive formats, partial downloads,
database files, credentials/key files, and environment variants (example/template exceptions).
Explicit staging, rather than blanket `git add .`, selected the checkpoint.

The selected 164-file initial index contained about 1.6 MB of text. A content/path/size scan found
no blocked dataset/checkpoint/archive formats, binary files, files over 2 MB, private-key headers,
or common GitHub/AWS/service token patterns. This is a bounded check, not proof that no possible
secret exists. The acquisition JSON contains public publisher URLs/checksums, not image data.

Thirteen older files under `ui/public/cases/` (12 thumbnails and `results.json`) were already tracked.
They are removed from the current index and the directory is ignored; local files remain intact.
Earlier commits still contain them. No history rewrite or remote deletion is implied. A separate
review is needed before redistributing historical demo assets or publishing their history.

Loose proposal drafts, generated document assets, downloaded literature samples, the separate
MedFormer checkout, and unrelated helper scripts remain untouched and outside this checkpoint.
Approved Word files remain local at their cataloged paths; this text/code checkpoint is not a
complete backup of every project document. No new model weights, scans, raw labels, local root
registry, virtual environment, build output, or runtime database is included.

## Verification

- Workspace identity checker passed.
- Python fast suite: 147 passed, two existing upstream deprecation warnings.
- UI: 18 unit/component tests and one synthetic Chromium smoke passed.
- Production UI build passed; large-bundle warning remains. No deployment occurred.
- Markdown hard-break spaces are retained intentionally; other staged whitespace issues checked.
- UI dependency advisories, full real-viewer/accessibility qualification, source extraction and
  reconciliation, and orchestration coding authorization/tool selection remain open.

Next: use this local baseline for further work. Pushing is a separate authorized action. The
stakeholder preparation task remains deferred until participant confirmation or Quinton's request.
