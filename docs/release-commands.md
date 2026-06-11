# Release Commands

Run these after the empty GitHub repository has been created.

## Option 1: Use the helper script

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish_release.ps1
```

## Option 2: Run Git commands directly

```powershell
git remote remove origin
git remote add origin https://github.com/zdszds2009/codex-project-restore-packager.git
git push -u origin main
git tag -f v0.1.0
git push origin v0.1.0 --force
```

## Release body source

Use `docs/releases/v0.1.0.md` as the GitHub release note body.
