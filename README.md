# Codex Backup

Package local Codex Desktop projects or individual conversations into a portable restore package.

Status: pre-1.0, Windows-focused, designed for local Codex Desktop recovery and migration workflows.

Codex Backup is a recovery and migration tool for local Codex Desktop state. It is built for a practical maintainer workflow: preserve useful Codex context before changing machines, rebuilding an environment, moving a repository, or recovering from local profile damage. Instead of manually copying `.codex` files or editing SQLite state by hand, the tool produces a reviewable package that contains only the selected conversation metadata, rollout history, workspace hints, and optional project files needed to restore the chosen work.

For open-source maintainers, the core value is straightforward:

- keep debugging and implementation context when moving between machines
- preserve important threads before resetting or repairing a development environment
- recover selected Codex work without copying an entire local profile
- avoid manual editing of Codex SQLite and JSONL state

This is not a generic backup of everything in `.codex`. It is a targeted export-and-restore workflow for the specific projects and conversations you choose.

## Typical maintainer use cases

- Move an active repository and its related Codex conversations to another Windows machine
- Preserve a long debugging thread before rebuilding a workstation or virtual machine
- Restore a specific project context after local Codex profile corruption
- Archive a meaningful piece of development history without exporting unrelated conversations

This repository contains:

- a Codex skill entry point in `SKILL.md`
- a packaging script in `scripts/build_restore_package.py`
- a restore helper in `scripts/restore_package.py`

Related project docs:

- [Launch Checklist](./docs/launch-checklist.md)
- [Codex for OSS Application Draft](./docs/codex-for-oss-application.md)
- [Demo Script](./docs/demo-script.md)
- [Usage Examples](./docs/usage-examples.md)
- [Release Notes v0.1.0](./docs/releases/v0.1.0.md)
- [Release Commands](./docs/release-commands.md)
- [Demo Page](./demo/index.html)
- [Roadmap](./ROADMAP.md)
- [Changelog](./CHANGELOG.md)

The resulting package can include:

- selected conversation rows from `~/.codex/state_5.sqlite`
- matching `session_index.jsonl` entries
- selected rollout JSONL history
- workspace-root hints from `.codex-global-state.json`
- project files when you explicitly include them

## Support matrix

| Area | Status |
| --- | --- |
| Operating system | Windows only |
| Python | 3.10+ |
| Third-party dependencies | None |
| Codex profile source | Local `%USERPROFILE%\\.codex` |
| Package output | Folder plus zip archive |
| Restore target | Another Windows Codex Desktop profile |

## Why this exists

Codex Desktop stores useful project and conversation state locally, but there is no built-in export flow for moving a project or a single thread between machines. In practice, that means maintainers end up doing one of three unsafe things:

- copying large parts of `.codex` without knowing which files matter
- manually editing `state_5.sqlite` and related JSONL files
- losing valuable thread history during machine migration or local recovery

Codex Backup exists to replace that ad hoc process with a repeatable workflow. It creates a restore-ready archive that keeps the minimum state needed for Codex Desktop to show the restored conversations again, while still allowing optional inclusion of the related project files when a full project migration is actually needed.

## What this tool actually does

At a high level, Codex Backup performs four jobs:

1. It identifies the conversations you want to preserve.
   - You can select them by project root, thread ID, or title keyword.
2. It extracts the relevant local Codex metadata.
   - This includes selected rows from `~/.codex/state_5.sqlite`, matching session index entries, workspace-root hints, and rollout history files.
3. It optionally copies the related project files.
   - Project-file inclusion is explicit and conservative by default.
4. It assembles everything into a portable package with restore instructions.
   - The output is a folder plus zip archive that can be reviewed, moved, archived, or restored on another Windows machine.

The result is not a generic backup of everything in `.codex`. It is a targeted restore package for the specific threads and project roots you selected.

## Why this is safer than manual copying

Manual migration usually mixes together too much state and too little structure. Codex Backup reduces that risk in three ways:

1. It narrows the export to selected threads and project roots.
2. It records what was exported in a manifest and restore instructions.
3. It backs up the target profile before any restore merge happens.

That combination matters because Codex Desktop state is spread across a database, JSONL indices, rollout files, and workspace-root metadata. Copying only one of those pieces is often insufficient; copying everything is often excessive. This tool sits in the middle and tries to keep the export both usable and reviewable.

## Features

- Package one or more Codex projects by project root
- Package one or more conversations by thread ID
- Package conversations by title keyword
- Keep archived conversations
- Normalize rollout and thread `model_provider` metadata to `custom` for current Codex Desktop compatibility
- Restore into another Windows Codex Desktop profile with automatic backups of existing local state

## Package contents

The generated archive contains a predictable layout:

- `manifest.json`
- `RESTORE_INSTRUCTIONS.md`
- `codex/backup_state.sqlite`
- `codex/session_index.jsonl`
- `codex/.codex-global-state.json`
- `codex/rollouts/...`
- `project_files/...` when project files were included
- `tools/restore_package.py`

Each part has a specific purpose:

- `backup_state.sqlite`
  - a narrowed copy of Codex thread metadata containing only the selected conversations and related rows
- `session_index.jsonl`
  - the conversation index entries needed for Codex Desktop to list restored threads
- `.codex-global-state.json`
  - workspace-root hints so restored threads still point to meaningful project locations
- `rollouts/...`
  - the underlying thread history files that preserve conversation context
- `project_files/...`
  - the optional source tree for actual project migration, not just thread restoration
- `restore_package.py`
  - the restore helper that merges selected state into the target profile and backs up the target files first

## Safety defaults

The project handles local conversation history and may copy project files. Public use needs conservative defaults.

- Selecting conversations by `--thread-id` or `--title-contains` packages conversation data only by default
- Project files are copied only when you pass `--project`, or when you explicitly opt in with `--include-thread-cwd-files`
- Existing target Codex state files are backed up before restore

You should still inspect package contents before sharing a restore archive with anyone else.

## What this tool does not try to do

- It does not back up every conversation in your local Codex profile unless you explicitly select them.
- It does not promise compatibility across future Codex Desktop storage changes.
- It does not solve collaborative cloud sync for Codex state.
- It does not merge two independently edited histories of the same conversation.

## Data handling

This project reads and copies local Codex Desktop state. Depending on the command you run, a package may include:

- conversation titles and thread IDs
- rollout history
- local filesystem paths
- project source code

Use thread-only exports when you do not need source files. Use project exports only for folders you intend to share or migrate.

## Detailed workflow

### Export flow

When you run `build_restore_package.py`, the tool performs the following sequence:

1. Load local Codex state from `%USERPROFILE%\.codex`.
   - It reads `state_5.sqlite`, `session_index.jsonl`, and `.codex-global-state.json`.
2. Resolve the target conversations.
   - By project root: select threads whose `cwd` matches the chosen root.
   - By thread ID: select those exact threads.
   - By title keyword: match against stored thread titles.
3. Build a reduced database.
   - The script copies the local database, deletes unrelated thread rows, and keeps only the selected thread-related records.
4. Rebuild the session index subset.
   - Only the selected thread entries are retained or synthesized when needed.
5. Capture workspace-root hints.
   - The package stores the project-root mappings needed to make the restored threads usable later.
6. Copy and normalize rollout history.
   - The tool copies each selected rollout file and normalizes `model_provider` metadata to `custom` for current Codex Desktop compatibility.
7. Optionally copy project files.
   - Explicit `--project` roots are included.
   - Thread-selected cwd folders are only included when `--include-thread-cwd-files` is passed.
8. Write a manifest and restore instructions.
   - The manifest records thread metadata, included projects, and rollout mappings.
9. Validate and zip the result.
   - The final archive is checked for required files before it is returned.

### Restore flow

When you run `restore_package.py`, the tool performs a controlled merge into another local Codex Desktop profile:

1. Open the package folder or extract the package zip.
2. Read `manifest.json`.
3. Resolve destination project folders.
   - If you pass `--project-target`, project files are restored to those explicit locations.
   - Otherwise the original source-root paths are reused when possible.
4. Back up the target profile files.
   - Existing `state_5.sqlite`, `session_index.jsonl`, and `.codex-global-state.json` are copied before any merge happens.
5. Restore rollout files.
   - The selected rollout history is copied into the target Codex home.
6. Merge thread metadata into the target database.
   - Existing rows for the selected thread IDs are removed first.
   - Replacement rows are then inserted from the package subset database.
7. Patch project and rollout paths.
   - The tool rewrites relevant paths so restored threads point to the correct target locations.
8. Merge session index and global state.
   - Selected conversations become visible again in the target profile, with updated workspace-root hints.
9. Restart Codex Desktop.
   - At that point the restored project or thread should appear in the target installation.

## Requirements

- Windows
- Python 3.10+
- A local Codex Desktop profile in `%USERPROFILE%\\.codex`

No third-party Python dependencies are required.

## Quick start

List likely projects and recent conversations:

```powershell
python .\scripts\build_restore_package.py --list
```

Package one project:

```powershell
python .\scripts\build_restore_package.py --project "C:\Users\you\Documents\MyProject" --out "$env:USERPROFILE\Desktop"
```

Package two projects:

```powershell
python .\scripts\build_restore_package.py --project "C:\path\project-a" --project "C:\path\project-b" --out "$env:USERPROFILE\Desktop"
```

Package a single conversation by thread ID:

```powershell
python .\scripts\build_restore_package.py --thread-id "thread_id_here" --out "$env:USERPROFILE\Desktop"
```

Package a conversation and also include its current working directory files:

```powershell
python .\scripts\build_restore_package.py --thread-id "thread_id_here" --include-thread-cwd-files --out "$env:USERPROFILE\Desktop"
```

Package conversation state only, without any project files:

```powershell
python .\scripts\build_restore_package.py --thread-id "thread_id_here" --no-project-files --out "$env:USERPROFILE\Desktop"
```

Restore on another machine:

```powershell
python .\tools\restore_package.py --package "."
```

Restore project files to a different target folder:

```powershell
python .\tools\restore_package.py --package "." --project-target "my-project=C:\target\folder"
```

## Verification after packaging

Before sharing or restoring a package:

1. Open the zip and confirm `manifest.json` is present.
2. Check whether `project_files/` exists when you did not intend to include source files.
3. Read `RESTORE_INSTRUCTIONS.md`.
4. Restore into a test profile first if the package contains important or sensitive work.

## Repository layout

```text
.
|-- SKILL.md
|-- README.md
|-- CHANGELOG.md
|-- LICENSE
|-- CODE_OF_CONDUCT.md
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- .github/
|   |-- ISSUE_TEMPLATE/
|   |-- pull_request_template.md
|   `-- workflows/ci.yml
|-- docs/
|   `-- codex-for-oss-application.md
|-- agents/
|   `-- openai.yaml
|-- scripts/
|   |-- build_restore_package.py
|   `-- restore_package.py
`-- tests/
    `-- test_cli_smoke.py
```

## How restore works

1. Copy the selected Codex database rows into a subset SQLite database.
2. Copy matching session-index entries and rollout JSONL files.
3. Record project-root hints in a package manifest and `.codex-global-state.json`.
4. Optionally copy project files into `project_files/`.
5. On restore, back up the target `.codex` state files.
6. Merge the selected threads and metadata into the target Codex profile.
7. Rewrite relevant project and rollout paths so restored threads point to the correct local locations.
8. Preserve current Codex Desktop visibility by normalizing stored provider metadata where needed.

## Limitations

- Built for Windows Codex Desktop paths
- Assumes a local `state_5.sqlite` schema compatible with the scripts
- Does not promise forward compatibility with future Codex Desktop storage changes
- Not intended to merge two independently edited versions of the same conversation

## Development

Run the standard-library smoke tests:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Validate syntax:

```powershell
python -m py_compile .\scripts\build_restore_package.py .\scripts\restore_package.py
```

## Launch checklist

Before publishing the repository and applying:

1. Record a short demo GIF or screenshot set.
2. Create the first GitHub release.
3. Add one or two real-world restore examples to the README or release notes.
4. Open at least one roadmap issue and one known-limitation issue publicly.
5. Verify the application answers in `docs/codex-for-oss-application.md` still match the repository state.

## License

MIT
