# Release Commands

Run these after the empty GitHub repository has been created.

## Option 1: Use the helper script

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish_release.ps1
```

## Option 2: Run Git commands directly

```powershell
$version = "v0.2.0"
git push -u origin main
git tag $version
git push origin $version
```

## Release body source

Use the matching file under `docs/releases/`, for example `docs/releases/v0.2.0.md`.
