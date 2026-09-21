# Workspace safety agreement

Approved by Quinton on September 20, 2026. Applies to PROWL work by every coding agent.
This is working guidance, not an operating-system access boundary.

## Before writing

1. Use one authoritative checkout for the task. Creating another clone, worktree, or sibling
   project requires an explicit user decision. Do not infer permission from a missing path.
2. Confirm `pwd`, `git rev-parse --show-toplevel`, and the intended target files. Run
   `python3 scripts/diagnostics/check_workspace.py` from the PROWL root. Check `git status --short`
   to distinguish existing user changes. The checker is manual and cannot distinguish two valid
   PROWL clones; confirm the intended location with the user's latest instructions.
3. Set the working directory explicitly for commands, especially in resumed sessions after a move.
   The confirmed checkout is `/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.
   Treat that as a location record, not a path to embed in portable application code.
4. A missing known project directory means STOP and resolve its new location. Never recreate
   an old `GitHub`/project hierarchy, silently fall back to another checkout, or add a compatibility
   symlink. Creating ordinary implementation subdirectories inside the confirmed checkout is
   allowed when the task requires them; explain material new directories in the handoff.
5. Look for existing configuration before generating replacements. Missing `.env`, Compose, or
   other setup files first require checking the checkout and expected relative location. Do not
   fabricate secrets, copy credentials between projects, or print secret values. Ignored local
   configuration may not exist in another clone; its absence does not prove data loss.

## Boundaries and persistent data

- Keep unrelated projects in separate workspaces. Write only within the task's confirmed scope.
  PROWL's explicitly approved external data/artifact/backup roots remain legitimate destinations;
  use the storage registry and relevant plan, not guessed sibling directories.
- Prefer workspace-scoped write permissions where supported. Full filesystem access is not
  constrained by these Markdown rules or by the manual workspace checker. Never claim otherwise.
- Before moving or deleting suspected duplicates, inventory paths, file presence, sizes, and
  relevant Git identity. Compare ordinary files with hashes where appropriate; do not expose
  secrets or treat live database-file hashes as a reliable backup/equivalence test.
- Check service/container mount paths before proposing cleanup of persistent data. Do not stop
  services, merge database directories, migrate data, or delete files as part of a read-only audit.
  Resolve uncertain ownership and get explicit scope approval for any later cleanup.
- Preserve prior proposals, experiment history, and unrelated user changes. Never use a blanket
  path/name replacement across historical records to make an audit look clean.

## Handoff

Report files changed, material directories created, verification performed, and any unresolved
workspace settings. Review the scoped diff and run appropriate checks. Do not silently commit,
push, or expand the task into other projects. If the selected workspace disagrees with the user,
stop before writing and explain the mismatch.
