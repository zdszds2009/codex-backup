# Compatibility Notes

Codex Backup is designed for local Windows Codex Desktop profiles that use a `state_5.sqlite` database plus adjacent JSONL and rollout files under `%USERPROFILE%\.codex`.

## Current assumptions

The packager and restore flow currently expect these tables when they are present:

- `threads`
- `thread_dynamic_tools`
- `thread_spawn_edges`

Only the overlapping columns between the source package and the target database are inserted during restore. This means the restore flow is intentionally tolerant of small additive schema changes, as long as the core thread identifiers and path fields still exist.

## Manifest schema snapshot

Each generated package includes a small `source_schema` snapshot inside `manifest.json`.

That snapshot records:

- the source database filename
- the detected table names relevant to packaging
- the column names present in those tables at packaging time

This is useful for:

- checking whether a package was created from a profile shape the current scripts still understand
- debugging restore failures after Codex Desktop storage changes
- documenting which local schema was used when maintainers report compatibility problems

## Known boundaries

- The tooling is built around Windows path handling.
- It does not guarantee forward compatibility with future Codex Desktop storage formats.
- It does not attempt to restore unknown tables or opaque profile features outside the packaged subset.
- It does not merge two divergent edits of the same thread history.

## Maintainer guidance

When validating a new Codex Desktop build against this repository:

1. Run `python .\scripts\build_restore_package.py --list` against a real local profile.
2. Create a small thread-only package.
3. Run `python .\scripts\inspect_package.py <package.zip>` and confirm the schema snapshot looks reasonable.
4. Restore into a disposable test profile before relying on the workflow for important recovery work.

If a future Codex Desktop build changes the thread schema substantially, update:

- `scripts/build_restore_package.py`
- `scripts/restore_package.py`
- `tests/test_cli_smoke.py`
- this compatibility note
