# Codex Backup

Package local Codex Desktop projects or individual conversations into a portable restore package.

Status: pre-1.0, Windows-focused, designed for local Codex Desktop recovery and migration workflows.

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

Codex Desktop stores useful project and conversation state locally, but there is no built-in export flow for moving a project or a single thread between machines. This tool creates a restore-ready archive that keeps the minimum state needed for Codex Desktop to show the restored conversations again.

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

## Safety defaults

The project handles local conversation history and may copy project files. Public use needs conservative defaults.

- Selecting conversations by `--thread-id` or `--title-contains` packages conversation data only by default
- Project files are copied only when you pass `--project`, or when you explicitly opt in with `--include-thread-cwd-files`
- Existing target Codex state files are backed up before restore

You should still inspect package contents before sharing a restore archive with anyone else.

## Data handling

This project reads and copies local Codex Desktop state. Depending on the command you run, a package may include:

- conversation titles and thread IDs
- rollout history
- local filesystem paths
- project source code

Use thread-only exports when you do not need source files. Use project exports only for folders you intend to share or migrate.

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
