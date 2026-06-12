# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-06-12

### Added

- Public usage-feedback issue template for README reviews, list-command checks, package inspection, and test restores
- Chinese outreach kit for asking real GitHub users to review the project with their own accounts
- User feedback guide describing low-risk review paths and privacy-safe feedback
- Codex for Open Source application success plan with positioning, evidence targets, and final answer drafts

### Changed

- README now clarifies the intended audience, feedback request, and Codex Desktop maintainer value proposition

## [0.2.0] - 2026-06-11

### Added

- End-to-end fixture test covering package creation, restore, path remapping, rollout normalization, and target-state backups
- `scripts/inspect_package.py` for pre-share and pre-restore package review
- Compatibility note documenting current schema expectations and manifest schema snapshots

### Changed

- Packaging manifests now include a source-schema snapshot for easier compatibility debugging
- Rollout package-path metadata now matches the actual archive layout
- SQLite connections are explicitly closed in package and restore flows to avoid Windows file-lock issues

## [0.1.0] - 2026-06-11

### Added

- Public repository documentation for usage, safety, launch, and contribution flow
- Smoke tests for core selection and path-rewrite behavior
- GitHub issue templates and CI workflow
- Application draft materials for OpenAI Codex for Open Source

### Changed

- Thread-based exports now include conversation data by default without automatically copying cwd project files
- Skill documentation was rewritten and UTF-8 normalized for public release

### Notes

- This is the first public-release candidate for Codex Backup, not a compatibility guarantee across future Codex Desktop schema changes
