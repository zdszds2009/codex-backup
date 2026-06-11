---
name: codex-backup
description: Package local Codex Desktop projects or individual conversations into a portable restore package with project files, thread metadata, session index entries, rollout history, and restore tools.
metadata:
  short-description: Package Codex projects or conversations for restore
---

# Codex Backup

Use this skill when the user wants to package one or more local Codex Desktop projects, or one or more individual conversations, into a restore-ready archive.

Default user intent / prompt:

> 请把本机的某个项目或某几项项目打包成 Codex 可恢复的迁移包。

Also use this skill when the user says any of the following:

- 打包某个 Codex 项目用于恢复、迁移、虚拟机迁移或备份
- 打包几个项目里的全部对话和相关文件
- 单独打包某个对话、某个会话、某条 thread
- 从本机 Codex 登录资料或 `.codex` 状态中制作恢复包

## Workflow

1. Identify what to package.
   - For projects, collect one or more project root paths.
   - For conversations, collect one or more Codex thread IDs, or title keywords with enough context to avoid accidental matches.
   - If the user does not provide enough information, inspect `%USERPROFILE%\.codex\state_5.sqlite` and summarize likely project roots or matching conversation titles.
2. Run `scripts/build_restore_package.py`.
3. The script reads the local Codex state in `%USERPROFILE%\.codex` and creates a package containing:
   - `codex/backup_state.sqlite`
   - `codex/session_index.jsonl`
   - `codex/.codex-global-state.json`
   - `codex/rollouts/...`
   - `project_files/...` when project folders are included
   - `manifest.json`
   - `RESTORE_INSTRUCTIONS.md`
   - `tools/restore_package.py`
4. Always keep archived conversations too. They are still valid Codex conversations.
5. Match project paths in both normal Windows form and long-path form (`\\?\C:\...`).
6. Normalize rollout `session_meta.payload.model_provider` to `custom` for current Codex Desktop visibility.
7. Validate that the final zip opens and includes `manifest.json`, `codex/backup_state.sqlite`, and rollout JSONL files for selected conversations.
8. When the package will be shared or restored later, run `scripts/inspect_package.py` on the generated zip and review the thread and project summary first.

## Safety defaults

- When packaging by `--thread-id` or `--title-contains`, include conversation data by default.
- Only include workspace files when the user passes `--project`, or explicitly opts in with `--include-thread-cwd-files`.
- Remind the user to inspect the zip before sharing it with another person.

## Commands

Package one project:

```powershell
python scripts/build_restore_package.py --project "C:\Users\you\Documents\MyProject" --out "$env:USERPROFILE\Desktop"
```

Package several projects:

```powershell
python scripts/build_restore_package.py --project "C:\path\project-a" --project "C:\path\project-b" --out "$env:USERPROFILE\Desktop"
```

Package a single conversation by thread ID:

```powershell
python scripts/build_restore_package.py --thread-id "thread_id_here" --out "$env:USERPROFILE\Desktop"
```

Package a single conversation and also include the current working directory files:

```powershell
python scripts/build_restore_package.py --thread-id "thread_id_here" --include-thread-cwd-files --out "$env:USERPROFILE\Desktop"
```

Package conversations by title keyword:

```powershell
python scripts/build_restore_package.py --title-contains "skills" --out "$env:USERPROFILE\Desktop"
```

List likely projects and recent conversations before packaging:

```powershell
python scripts/build_restore_package.py --list
```

The package includes restore instructions, so the user does not need to send a separate operational prompt to Codex on the target machine.
