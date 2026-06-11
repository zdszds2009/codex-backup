from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def extract_if_needed(package: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if package.is_dir():
        return package, None
    temp = tempfile.TemporaryDirectory(prefix="codex-inspect-")
    with zipfile.ZipFile(package, "r") as zipf:
        zipf.extractall(temp.name)
    return Path(temp.name), temp


def load_manifest(package_root: Path) -> dict[str, Any]:
    manifest_path = package_root / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"Missing manifest.json in package: {package_root}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def summarize_manifest(manifest: dict[str, Any]) -> list[str]:
    lines = [
        f"package_name={manifest.get('package_name', '(unknown)')}",
        f"created_at={manifest.get('created_at', '(unknown)')}",
        f"thread_count={manifest.get('thread_count', 0)}",
        f"project_count={len(manifest.get('projects', []))}",
        f"rollout_count={len(manifest.get('rollouts', []))}",
    ]

    schema = manifest.get("source_schema") or {}
    table_names = sorted((schema.get("tables") or {}).keys(), key=str.casefold)
    if table_names:
        lines.append("schema_tables=" + ",".join(table_names))

    projects = manifest.get("projects", [])
    if projects:
        for project in projects:
            lines.append(
                "project="
                + json.dumps(
                    {
                        "key": project.get("key"),
                        "source_root": project.get("source_root"),
                        "file_count": project.get("file_count"),
                    },
                    ensure_ascii=False,
                )
            )
    else:
        lines.append("project_files=absent")

    threads = manifest.get("threads", [])
    for thread in threads[:10]:
        lines.append(
            "thread="
            + json.dumps(
                {
                    "id": thread.get("id"),
                    "title": thread.get("title"),
                    "cwd": thread.get("cwd"),
                    "archived": bool(thread.get("archived")),
                },
                ensure_ascii=False,
            )
        )
    if len(threads) > 10:
        lines.append(f"thread_list_truncated={len(threads) - 10}")

    return lines


def inspect_package(package: Path) -> None:
    package_root, temp = extract_if_needed(package)
    try:
        manifest = load_manifest(package_root)
        for line in summarize_manifest(manifest):
            print(line)
    finally:
        if temp is not None:
            temp.cleanup()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a Codex Backup package before restore or sharing.")
    parser.add_argument("package", help="Extracted package folder or restore package zip.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    configure_stdio()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    inspect_package(Path(args.package).expanduser().resolve())


if __name__ == "__main__":
    main()
