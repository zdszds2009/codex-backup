# Release Template

## Summary

Codex Backup packages selected Codex Desktop conversations and optional project files into a restore-ready archive for migration and recovery workflows.

## Highlights

- Safer default behavior for thread-based exports
- Restore helper with automatic backup of target Codex state files
- Package inspection output for pre-share review
- Dependency-free Python scripts for package creation and restore

## Typical use cases

- Move an active Codex project to another Windows machine
- Preserve a debugging conversation before resetting an environment
- Recover important Codex context after local profile changes

## Limitations

- Windows-focused path handling
- No guarantee across future Codex Desktop schema changes
- Users should inspect generated archives before sharing them

## Validation

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile .\scripts\build_restore_package.py .\scripts\restore_package.py .\scripts\inspect_package.py .\tests\test_cli_smoke.py
```
