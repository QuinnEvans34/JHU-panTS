# Read-only duplicate-location inventory — September 20, 2026

Scope: the known old/new GitHub parents implicated in the relocation, not a whole-computer
duplicate search. Only PROWL guidance/report files were edited. Other project folders, services,
containers, credentials, and databases were not modified. No secret values were opened.

## Locations

| Location | Observation |
|---|---|
| `/Users/quintonevans/Desktop/GitHub` | Absent at inspection |
| `/Users/quintonevans/Desktop/Quinn/Desktop/GitHub/Neuro-data` | Absent at inspection |
| `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL` | Confirmed PROWL Git root; workspace check passed |
| `/Users/quintonevans/Desktop/Quinn/Desktop/GitHub` | Exists; observed child is `NU_Prospect_App` |
| `/Users/quintonevans/Desktop/Quinn/Desktop/GitHub/NU_Prospect_App` | Inspected tree contains `the_project/.docker/mssql-data`, including database files, logs, and a secrets directory; not an empty duplicate |
| `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/NU_Prospect_App` | Confirmed Git root; `the_project/.env`, `.env.example`, `docker-compose.yml`, and `.docker` exist |

The current GitHub parent also contains other distinctly named projects. Their presence alone
does not establish duplication; no reorganization or deduplication is proposed for them here.

## Service-path evidence

Read-only Docker inspection requested container names, status, and mount source/destination only,
not environment variables. Running `neumont_mssql` mounts:

`/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/NU_Prospect_App/the_project/.docker/mssql-data`
to `/var/opt/mssql`.

None of the inspected container mounts pointed at the old `Desktop/Quinn/Desktop/GitHub` tree
at inspection time. This does not establish that no non-Docker process uses it, who created it,
whether an earlier container used it, or whether it contains unique recoverable data.

## Comparison limits and disposition

The observed mismatch is an old database-data tree versus the current full checkout containing
configuration. It is not evidence that the current `.env` or Compose file is missing. No ordinary
duplicate configuration files were identified in the bounded old-tree listing for hash comparison.
Database and secret contents were not opened or hashed. File presence is not database equivalence.

**Preserve the old tree pending a separate database-aware review.** Before any cleanup, the owner
of that project should confirm intended database state, obtain a verified backup, assess whether
the old data is unique, and approve exact cleanup targets. Do not merge raw database directories.
The evidence is insufficient to attribute the old tree to Claude or any other agent.

The shared preventative agreement is [WORKSPACE-SAFETY.md](WORKSPACE-SAFETY.md). It is linked
from both PROWL agent entrypoints. No app permission settings were changed in this pass.

## Verification of this documentation pass

Workspace check and `git diff --check` passed. The four workspace-check tests passed when run
from the repository root with `.venv-prowl/bin/python -m pytest tests/test_workspace_check.py`.
The initial isolated invocation through `.venv-prowl/bin/pytest` failed collection because
`scripts` was not importable on that invocation's path; using `python -m pytest` supplies the
repository root. No test or application code was changed to mask that initial failure.
