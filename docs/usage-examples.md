# Usage Examples

These examples are written for the public repository so a new user can quickly decide whether the tool fits their workflow.

## Example 1: Move one Codex project to another Windows machine

Use this when a project folder and its related conversations should move together.

```powershell
python .\scripts\build_restore_package.py --project "C:\Users\you\Documents\demo-project" --out "$env:USERPROFILE\Desktop"
```

Expected result:

- a timestamped package folder
- a matching zip archive
- selected thread metadata and rollout files for that project
- copied project files under `project_files/`

## Example 2: Preserve one debugging thread without copying source files

Use this when you only need the conversation history.

```powershell
python .\scripts\build_restore_package.py --thread-id "thread_id_here" --no-project-files --out "$env:USERPROFILE\Desktop"
```

Expected result:

- conversation metadata and rollout history are packaged
- `project_files/` is absent
- the package is safer to review before sharing

## Example 3: Restore into a different target folder

Use this when the original source path does not exist on the target machine.

```powershell
python .\tools\restore_package.py --package "." --project-target "demo-project=C:\Restored\demo-project"
```

Expected result:

- project files are copied to the mapped target folder
- thread metadata is merged into the target `.codex` profile
- existing target state files are backed up before merge

## Example 4: Review package contents before sending it

Minimum review checklist:

1. Open `manifest.json`.
2. Check whether `project_files/` exists.
3. Read `RESTORE_INSTRUCTIONS.md`.
4. Confirm the package does not include unrelated private work.
