# PROWL checkout relocation — September 20, 2026

## Location and scope

Quinton moved and renamed the checkout from
`/Users/quintonevans/Desktop/Quinn/Desktop/GitHub/Neuro-data` to
`/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
This maintenance pass repairs environment launch paths and active navigation, not scientific
configuration or capstone scope. No proposals, experiment history, raw data, Git history, or
external-drive roots were rewritten. Existing unrelated working-tree changes remain intact.

## Completed fixes

- Preserved the previous capstone environment as `.venv-prowl-pre-relocation-20260920` (ignored
  by Git). It retains stale launch paths and is an archive, not the environment to activate.
- Created a new `.venv-prowl` at the new location with Python 3.12.13, pip 26.1, and the unchanged
  hash-verified `requirements/locks/macos-arm64-py312.txt`. All 59 installed distributions
  (58 locked dependencies plus pip) match the preserved environment's versions exactly.
- Left historical `.venv312` unchanged. Its old launch paths are not repaired or qualified.
- Added current capstone guidance above `CLAUDE.md`'s preserved five-week history; added a
  location-check reminder to `AGENTS.md`. The capstone hub remains authoritative for plan status.
- Separated current and historical setup instructions in the root README and corrected the
  clone destination. GitHub remote remains `https://github.com/QuinnEvans34/JHU-panTS.git`.
- Added `scripts/diagnostics/check_workspace.py` and four tests. The check requires invocation
  from its own Git root and checks for the capstone hub and lockfile. It supports renamed
  checkouts; it does not restrict filesystem permissions, run automatically before all commands,
  or distinguish two legitimate PROWL clones. The operator must confirm the intended checkout.

## Verification

Run from the new checkout root:

```sh
python3 scripts/diagnostics/check_workspace.py
.venv-prowl/bin/pip check
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv-prowl/bin/pytest tests -q -p no:cacheprovider
```

Results: workspace check passed; no broken requirements; **105 tests passed**, comprising the
101 existing tests and four new workspace checks. Two existing upstream PyTorch deprecation
warnings remain. Activation resolves `python` and `pytest` to the new `.venv-prowl/bin`.
No old-root references remain in its launcher directory or `pyvenv.cfg`. `git diff --check`
passed. These are fast/synthetic foundation checks, not real-data training, UI, or full G0 evidence.

The existing PANORAMA process was not restarted. Its receipt continued to report batch 4 progress
through 17,190,677,276 of 46,271,075,077 bytes at 20:13 UTC. This is a progress observation, not
a completed or verified archive claim. External source paths and partial payloads were untouched.

## Remaining app setting (manual)

The saved `capstone` project still points to the old checkout, and the current task's default
working directory is stale. Explicit shell working directories work. No project-edit API was
available; the UI automation runtime failed to start with `No such file or directory`.
No app settings were changed by this pass.

In the app's project menu, choose **Edit project**, replace the old folder with the new PROWL
folder, and make it the primary folder if needed. Keep unrelated projects separate. New tasks
use the primary folder; confirm the working directory again for resumed tasks. Updating the
project does not prove this existing task's recorded working directory has changed.
Official guidance: https://learn.chatgpt.com/docs/projects?surface=web&translationFallback=es-419

Do not add a compatibility symlink at the old path: that would conceal stale configuration.
Do not rewrite historical provenance paths. Before training, separately qualify extracted data
and source aliases; legacy `configs/level45.yaml` still references the failed JHU-PanTS drive
and is not the current capstone training configuration.
