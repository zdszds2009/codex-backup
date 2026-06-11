# Security

This tool packages and restores local Codex Desktop state. That can include conversation history, workspace-root hints, rollout logs, and project files.

## Sensitive data

A restore package may contain:

- local conversation titles and IDs
- Codex rollout history
- project source code
- file paths and workspace hints

Do not share generated archives unless you have reviewed their contents.

## Safe usage guidance

- Prefer `--thread-id` or `--title-contains` without `--include-thread-cwd-files` when you only need conversation history.
- Prefer explicit `--project` roots when you do want project files.
- Inspect the generated zip before sending it to another person or machine.
- Restore into a test profile first when possible.

## Reporting

If you find a bug that can expose unrelated conversations, over-collect files, or corrupt a target Codex profile, report it privately to the maintainer before publishing details.
