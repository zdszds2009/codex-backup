# Demo Script

Use this outline for a short GIF or video before making the repository public.

## Goal

Show one complete export-and-restore cycle in under 90 seconds.

## Suggested flow

1. Show a Codex Desktop project with an existing conversation.
2. Open PowerShell and run:

   ```powershell
   python .\scripts\build_restore_package.py --project "C:\path\demo-project" --out "$env:USERPROFILE\Desktop"
   ```

3. Show the resulting zip on the Desktop.
4. Open the zip and briefly show `manifest.json`, `codex/backup_state.sqlite`, and `RESTORE_INSTRUCTIONS.md`.
5. On a second test profile or machine, run:

   ```powershell
   python .\tools\restore_package.py --package "."
   ```

6. Reopen Codex Desktop and show that the conversation appears again.

## Recording notes

- Do not expose unrelated thread titles or project files.
- Blur or crop private paths if needed.
- Prefer one clean scenario over multiple partial clips.
