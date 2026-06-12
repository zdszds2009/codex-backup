# Demo

This folder contains demo assets for `Codex Backup`.

## Files

- `auto_demo.py` — automated end-to-end demo that runs a real export/inspect/restore cycle using actual Codex data
- `demo-video-script.ps1` — PowerShell script for screen recording (manual recording helper)
- `index.html` — static visual demo landing page
- `codex-backup-demo-cover.png` — demo cover image for GitHub releases

## How to use it

### Automated demo

```powershell
python demo\auto_demo.py
```

This will create a real restore package on your Desktop (~\codex-demo-output\)
using your local Codex projects, inspect it, and show restore instructions.
Use ScreenToGif or OBS to record the terminal for a demo video.

### Landing page

Open `index.html` in a browser, take a screenshot, or host it on GitHub Pages.

## Suggested release use

- Screenshot the hero section for the GitHub release
- Link the page from the README
- Use the auto_demo output as a demo asset in the Codex for Open Source application
