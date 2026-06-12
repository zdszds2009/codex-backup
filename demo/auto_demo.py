#!/usr/bin/env python3
"""Auto Demo for Codex Backup — one export/inspect/restore cycle with real data."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

OUT = Path.home() / "Desktop" / "codex-demo-output"
REPO = Path(__file__).resolve().parent.parent
DEMO_PROJECT = r"C:\Users\sunya\Documents\skills"

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def clean(text: str) -> str:
    return ansi_escape.sub("", text).replace("\xa0", " ").strip()


def run(cmd: list[str], label: str = "") -> str:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(cmd, capture_output=True, text=False, cwd=REPO, env=env)
    out = clean(result.stdout.decode("utf-8", errors="replace"))
    err = clean(result.stderr.decode("utf-8", errors="replace"))
    for line in out.splitlines():
        print(f"  {line}")
    if result.returncode != 0:
        for line in err.splitlines():
            if line.strip():
                print(f"  [stderr] {line}")
        print(f"  [exit={result.returncode}]")
    return out


def main():
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║        Codex Backup  —  Automated Demo              ║")
    print("  ║   One export-and-restore cycle with real data       ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()

    print("  ─── Step 1/5: Project overview ───")
    print(f"  Project : {REPO}")
    print(f"  Source  : {DEMO_PROJECT} (15 conversations)")
    print(f"  Scripts : build_restore_package.py, inspect_package.py, restore_package.py")
    print()

    print("  ─── Step 2/5: Clean output ───")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    print(f"  Output  : {OUT}")
    print()

    print("  ─── Step 3/5: Export package ───")
    cmd = [sys.executable, "scripts/build_restore_package.py",
           "--project", DEMO_PROJECT, "--out", str(OUT), "--name", "codex-backup-demo"]
    print(f"  $ python scripts/build_restore_package.py --project ... --out ... --name codex-backup-demo")
    print()
    run(cmd)
    print()

    zip_files = list(OUT.glob("*.zip"))
    if not zip_files:
        print("  ERROR: No package created!")
        return
    pkg_zip = zip_files[0]
    size_mb = pkg_zip.stat().st_size / 1_000_000

    print("  ─── Step 4/5: Inspect package ───")
    print(f"  Package: {pkg_zip.name} ({size_mb:.1f} MB)")
    print()
    print(f"  $ python scripts/inspect_package.py {pkg_zip.name}")
    print()
    run([sys.executable, "scripts/inspect_package.py", str(pkg_zip)])
    print()

    # Manifest summary
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(pkg_zip, "r") as zf:
            if "manifest.json" in zf.namelist():
                m = json.loads(zf.read("manifest.json"))
                print(f"  Manifest Summary:")
                print(f"    Name     : {m.get('package_name')}")
                print(f"    Created  : {m.get('created_at')}")
                print(f"    Threads  : {m.get('thread_count')}")
                print(f"    Sessions : {m.get('session_index_entries')}")
                if m.get("project_count", 0) > 0:
                    print(f"    Project  : skills ({Path(DEMO_PROJECT).name})")
                print()

    print("  ─── Step 5/5: Restore preview ───")
    print(f"  To restore on another machine run:")
    print(f"    python scripts/restore_package.py --package {pkg_zip.name}")
    print(f"  This will restore {size_mb:.0f} MB of Codex conversations to ~/.codex")
    print()

    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║  Demo Complete!                               ║")
    print(f"  ║  Package: {str(OUT / pkg_zip.name):<35s} ║")
    print(f"  ║  Size   : {size_mb:.0f} MB                                          ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()
    print("  Recording suggestion: ScreenToGif (free) or OBS")
    print("  Capture this terminal window from Step 1 through 5.")
    print()


if __name__ == "__main__":
    main()
