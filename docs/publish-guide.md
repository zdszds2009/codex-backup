# Publish Guide

Use this once the repository is ready to go public on GitHub.

## 1. Create the remote repository

Create a new public repository named `codex-backup` under the `zdszds2009` account.

Recommended settings:

- Public visibility
- No README initialization
- No `.gitignore` template
- No license template

## 2. Push the local history

From the repository root:

```powershell
git remote add origin https://github.com/zdszds2009/codex-backup.git
git push -u origin main
```

## 3. Create the first tag

```powershell
git tag v0.1.0
git push origin v0.1.0
```

## 4. Create the first GitHub release

Use `docs/releases/v0.1.0.md` as the release note body.

## 5. Final public checks

- Open the repository homepage
- Verify the README renders correctly
- Confirm the issue templates and workflow file are visible
- Confirm the release tag exists
