from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CODEX_HOME = Path.home() / ".codex"
STATE_DB = CODEX_HOME / "state_5.sqlite"
SESSION_INDEX = CODEX_HOME / "session_index.jsonl"
GLOBAL_STATE = CODEX_HOME / ".codex-global-state.json"

DEFAULT_EXCLUDE_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "restore-packages",
    "restore-temp",
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def strip_long_prefix(path_text: str) -> str:
    return path_text.replace("\\\\?\\", "")


def normalized_path_text(path_text: str) -> str:
    return str(Path(strip_long_prefix(path_text))).rstrip("\\/").casefold()


def safe_name(text: str, fallback: str = "item") -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip()).strip("-._")
    return value[:80] or fallback


def json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def connect_state(path: Path = STATE_DB) -> sqlite3.Connection:
    if not path.exists():
        raise SystemExit(f"Codex state database not found: {path}")
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "select 1 from sqlite_master where type='table' and name=?",
        (table,),
    ).fetchone()
    return row is not None


def table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in con.execute(f"pragma table_info({quote_ident(table)})")]


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def load_threads() -> list[dict[str, Any]]:
    with connect_state() as con:
        if not table_exists(con, "threads"):
            raise SystemExit("The Codex state database does not contain a threads table.")
        return [dict(row) for row in con.execute("select * from threads order by updated_at desc")]


def list_candidates() -> None:
    threads = load_threads()
    projects: dict[str, int] = {}
    for row in threads:
        cwd = row.get("cwd")
        if cwd:
            projects[str(Path(strip_long_prefix(cwd)))] = projects.get(str(Path(strip_long_prefix(cwd))), 0) + 1

    print("Projects with conversations:")
    for path, count in sorted(projects.items(), key=lambda item: (-item[1], item[0].casefold()))[:80]:
        print(f"  {count:>3}  {path}")

    print("\nRecent conversations:")
    for row in threads[:80]:
        title = row.get("title") or "(untitled)"
        archived = " archived" if row.get("archived") else ""
        print(f"  {row.get('id')}  {title}{archived}")


def select_threads(
    threads: list[dict[str, Any]],
    project_roots: list[Path],
    thread_ids: set[str],
    title_contains: list[str],
) -> list[dict[str, Any]]:
    wanted_roots = {normalized_path_text(str(path)) for path in project_roots}
    title_terms = [term.casefold() for term in title_contains if term.strip()]
    selected: list[dict[str, Any]] = []

    for row in threads:
        row_id = str(row.get("id") or "")
        cwd = str(row.get("cwd") or "")
        title = str(row.get("title") or "")
        matches_project = cwd and normalized_path_text(cwd) in wanted_roots
        matches_id = row_id in thread_ids
        matches_title = any(term in title.casefold() for term in title_terms)
        if matches_project or matches_id or matches_title:
            selected.append(row)

    return selected


def project_roots_for_selected(
    selected: list[dict[str, Any]],
    explicit_roots: list[Path],
    include_thread_cwd_files: bool,
) -> list[Path]:
    roots: dict[str, Path] = {}
    for root in explicit_roots:
        roots[normalized_path_text(str(root))] = root
    if include_thread_cwd_files:
        for row in selected:
            cwd = row.get("cwd")
            if not cwd:
                continue
            path = Path(strip_long_prefix(str(cwd)))
            if path.exists() and path.is_dir():
                roots.setdefault(normalized_path_text(str(path)), path)
    return list(roots.values())


def copy_subset_db(thread_ids: set[str], out_db: Path) -> None:
    shutil.copy2(STATE_DB, out_db)
    con = sqlite3.connect(out_db)
    try:
        if not thread_ids:
            raise SystemExit("No conversations selected.")
        all_thread_ids = [row[0] for row in con.execute("select id from threads")]
        delete_ids = [thread_id for thread_id in all_thread_ids if thread_id not in thread_ids]
        if delete_ids:
            delete_placeholders = ",".join("?" for _ in delete_ids)
            if table_exists(con, "threads"):
                con.execute(f"delete from threads where id in ({delete_placeholders})", delete_ids)
            if table_exists(con, "thread_dynamic_tools"):
                con.execute(f"delete from thread_dynamic_tools where thread_id in ({delete_placeholders})", delete_ids)
            if table_exists(con, "thread_spawn_edges"):
                con.execute(
                    f"delete from thread_spawn_edges where parent_thread_id in ({delete_placeholders})",
                    delete_ids,
                )
                con.execute(
                    f"delete from thread_spawn_edges where child_thread_id in ({delete_placeholders})",
                    delete_ids,
                )
        normalize_thread_table_provider(con)
        con.commit()
        con.execute("pragma wal_checkpoint(truncate)")
        con.execute("vacuum")
    finally:
        con.close()


def normalize_thread_table_provider(con: sqlite3.Connection) -> None:
    if not table_exists(con, "threads"):
        return
    columns = set(table_columns(con, "threads"))
    if "model_provider" in columns:
        con.execute("update threads set model_provider='custom' where model_provider is not null")


def iso_from_updated_at(value: Any) -> str:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, str) and value.strip():
        if value.isdigit():
            return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat().replace("+00:00", "Z")
        return value
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_subset_session_index(
    thread_ids: set[str],
    selected: list[dict[str, Any]],
    out_path: Path,
) -> int:
    kept: list[dict[str, Any]] = []
    seen: set[str] = set()
    if SESSION_INDEX.exists():
        for line in SESSION_INDEX.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = str(item.get("id") or item.get("thread_id") or "")
            if item_id in thread_ids:
                kept.append(item)
                seen.add(item_id)
    for row in selected:
        thread_id = str(row.get("id") or "")
        if thread_id and thread_id not in seen:
            kept.append(
                {
                    "id": thread_id,
                    "thread_name": row.get("title") or thread_id,
                    "updated_at": iso_from_updated_at(row.get("updated_at")),
                }
            )
            seen.add(thread_id)
    out_path.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in kept) + ("\n" if kept else ""),
        encoding="utf-8",
    )
    return len(seen)


def write_global_state_subset(
    out_path: Path,
    selected: list[dict[str, Any]],
    project_roots: list[Path],
) -> None:
    data: dict[str, Any] = {}
    if GLOBAL_STATE.exists():
        try:
            data = json.loads(GLOBAL_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}

    roots = [str(root) for root in project_roots]
    data["electron-saved-workspace-roots"] = roots
    data["active-workspace-roots"] = roots
    data["project-order"] = roots

    hints = data.setdefault("thread-workspace-root-hints", {})
    for row in selected:
        thread_id = str(row.get("id") or "")
        cwd = str(row.get("cwd") or "")
        if thread_id and cwd:
            hints[thread_id] = str(Path(strip_long_prefix(cwd)))

    selected_ids = {str(row.get("id") or "") for row in selected}
    data["projectless-thread-ids"] = [
        thread_id for thread_id in data.get("projectless-thread-ids", []) if thread_id not in selected_ids
    ]
    out_path.write_text(json_dumps(data), encoding="utf-8")


def normalize_rollout_line(item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    payload = item.get("payload")
    if isinstance(payload, dict) and "model_provider" in payload:
        payload["model_provider"] = "custom"
    if item.get("type") == "session_meta" and isinstance(payload, dict):
        payload["model_provider"] = "custom"
    return item


def copy_rollout_normalized(src: Path, dst: Path) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with src.open("r", encoding="utf-8", errors="replace") as reader, dst.open("w", encoding="utf-8") as writer:
        for line in reader:
            stripped = line.strip()
            if not stripped:
                writer.write(line)
                continue
            try:
                item = normalize_rollout_line(json.loads(stripped))
                writer.write(json.dumps(item, ensure_ascii=False) + "\n")
                count += 1
            except json.JSONDecodeError:
                writer.write(line)
    shutil.copystat(src, dst)
    return count


def copy_rollouts(selected: list[dict[str, Any]], codex_dir: Path) -> list[dict[str, Any]]:
    rollout_root = codex_dir / "rollouts"
    entries: list[dict[str, Any]] = []
    for row in selected:
        thread_id = str(row.get("id") or "")
        rollout_path = row.get("rollout_path")
        if not rollout_path:
            entries.append({"thread_id": thread_id, "missing": "empty rollout_path"})
            continue
        src = Path(strip_long_prefix(str(rollout_path)))
        if not src.exists():
            entries.append({"thread_id": thread_id, "missing": str(src)})
            continue
        try:
            rel = src.relative_to(CODEX_HOME)
        except ValueError:
            rel = Path("external-rollouts") / src.name
        dst = rollout_root / rel
        line_count = copy_rollout_normalized(src, dst)
        entries.append(
            {
                "thread_id": thread_id,
                "source": str(src),
                "path": f"codex/rollouts/{rel.as_posix()}",
                "target_codex_relative_path": rel.as_posix(),
                "line_count": line_count,
            }
        )
    return entries


def should_skip_dir(name: str, exclude_names: set[str]) -> bool:
    return name in exclude_names


def add_file(zipf: zipfile.ZipFile, src: Path, arcname: str) -> None:
    zipf.write(src, arcname.replace("\\", "/"))


def add_tree_to_package(root: Path, package_dir: Path, arc_root: str, exclude_names: set[str]) -> tuple[int, int]:
    count = 0
    total = 0
    dest_root = package_dir / arc_root
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if not should_skip_dir(name, exclude_names)]
        base = Path(dirpath)
        for name in filenames:
            src = base / name
            try:
                rel = src.relative_to(root)
            except ValueError:
                continue
            dst = dest_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            count += 1
            total += src.stat().st_size
    return count, total


def write_restore_instructions(package_dir: Path, manifest: dict[str, Any]) -> None:
    project_lines = []
    for project in manifest.get("projects", []):
        project_lines.append(
            f"- {project['key']}: source `{project['source_root']}`, files `{project['package_path']}`"
        )
    if not project_lines:
        project_lines.append("- No project files were included; this package restores conversation history only.")

    text = f"""# Codex restore package

Created: {manifest['created_at']}
Package name: {manifest['package_name']}

## Contents

- Conversations: {manifest['thread_count']}
- Project folders: {len(manifest.get('projects', []))}
- `codex/backup_state.sqlite`: selected Codex conversation metadata
- `codex/session_index.jsonl`: selected conversation index entries
- `codex/.codex-global-state.json`: project root hints for selected conversations
- `codex/rollouts`: selected conversation history JSONL files
- `project_files`: project files when available
- `tools/restore_package.py`: helper for restoring into another Windows Codex Desktop account

## Included projects

{chr(10).join(project_lines)}

## Restore on the target machine

1. Close Codex Desktop on the target machine.
2. Extract this zip.
3. Open PowerShell in the extracted folder.
4. Run:

```powershell
python .\\tools\\restore_package.py --package "."
```

To restore project files to a different folder, pass one mapping per project:

```powershell
python .\\tools\\restore_package.py --package "." --project-target "project_key=C:\\target\\folder"
```

5. Restart Codex Desktop.
6. Open the restored project or conversation and check that the conversation opens normally.

The restore helper backs up the target Codex state files before merging. It also keeps rollout `model_provider` metadata as `custom`, which is required by current Codex Desktop builds to show restored conversations reliably.
"""
    (package_dir / "RESTORE_INSTRUCTIONS.md").write_text(text, encoding="utf-8")


def script_path(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def write_manifest(
    package_dir: Path,
    package_name: str,
    selected: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    rollouts: list[dict[str, Any]],
    session_index_entries: int,
) -> dict[str, Any]:
    manifest = {
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "package_name": package_name,
        "source_codex_home": str(CODEX_HOME),
        "thread_count": len(selected),
        "session_index_entries": session_index_entries,
        "projects": projects,
        "threads": [
            {
                "id": str(row.get("id") or ""),
                "title": row.get("title"),
                "archived": bool(row.get("archived")),
                "cwd": str(Path(strip_long_prefix(str(row.get("cwd"))))) if row.get("cwd") else None,
                "rollout_path": str(Path(strip_long_prefix(str(row.get("rollout_path")))))
                if row.get("rollout_path")
                else None,
                "updated_at": row.get("updated_at"),
            }
            for row in selected
        ],
        "rollouts": rollouts,
    }
    (package_dir / "manifest.json").write_text(json_dumps(manifest), encoding="utf-8")
    return manifest


def build_package(args: argparse.Namespace) -> Path:
    project_roots = [Path(value).expanduser().resolve() for value in args.project]
    missing_projects = [str(path) for path in project_roots if not path.exists() or not path.is_dir()]
    if missing_projects:
        raise SystemExit("These project folders do not exist:\n" + "\n".join(missing_projects))

    threads = load_threads()
    selected = select_threads(threads, project_roots, set(args.thread_id), args.title_contains)
    if not selected:
        raise SystemExit("No matching Codex conversations were found.")

    selected_ids = {str(row.get("id") or "") for row in selected}
    package_roots = project_roots_for_selected(
        selected,
        project_roots,
        include_thread_cwd_files=args.include_thread_cwd_files,
    )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    package_name = args.name or f"codex-restore-{timestamp}"
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    package_dir = out_dir / package_name
    if package_dir.exists():
        raise SystemExit(f"Output folder already exists: {package_dir}")

    codex_dir = package_dir / "codex"
    tools_dir = package_dir / "tools"
    codex_dir.mkdir(parents=True, exist_ok=True)
    tools_dir.mkdir(parents=True, exist_ok=True)

    copy_subset_db(selected_ids, codex_dir / "backup_state.sqlite")
    session_index_entries = write_subset_session_index(selected_ids, selected, codex_dir / "session_index.jsonl")
    write_global_state_subset(codex_dir / ".codex-global-state.json", selected, package_roots)
    rollouts = copy_rollouts(selected, codex_dir)

    exclude_names = set(DEFAULT_EXCLUDE_NAMES)
    exclude_names.update(args.exclude_name)
    projects: list[dict[str, Any]] = []
    if not args.no_project_files:
        for index, root in enumerate(package_roots, start=1):
            key = safe_name(root.name, f"project-{index}")
            existing_keys = {project["key"] for project in projects}
            if key in existing_keys:
                key = f"{key}-{index}"
            arc_root = f"project_files/{key}"
            file_count, byte_count = add_tree_to_package(root, package_dir, arc_root, exclude_names)
            projects.append(
                {
                    "key": key,
                    "source_root": str(root),
                    "package_path": arc_root,
                    "file_count": file_count,
                    "byte_count": byte_count,
                }
            )

    restore_script = script_path("restore_package.py")
    if restore_script.exists():
        shutil.copy2(restore_script, tools_dir / "restore_package.py")

    manifest = write_manifest(
        package_dir,
        package_name,
        selected,
        projects,
        rollouts,
        session_index_entries,
    )
    write_restore_instructions(package_dir, manifest)

    zip_path = out_dir / f"{package_name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        for src in package_dir.rglob("*"):
            if src.is_file():
                add_file(zipf, src, src.relative_to(package_dir).as_posix())

    with zipfile.ZipFile(zip_path, "r") as zipf:
        names = set(zipf.namelist())
        required = {"manifest.json", "codex/backup_state.sqlite", "RESTORE_INSTRUCTIONS.md"}
        missing = sorted(required - names)
        if missing:
            raise SystemExit("Package validation failed; missing: " + ", ".join(missing))

    print(f"restore_package_zip={zip_path}")
    print(f"thread_count={len(selected)}")
    print(f"session_index_entries={session_index_entries}")
    print(f"project_count={len(projects)}")
    print(f"zip_bytes={zip_path.stat().st_size}")
    return zip_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package Codex Desktop projects or individual conversations into a restore-ready zip.",
    )
    parser.add_argument("--project", action="append", default=[], help="Project root folder to package.")
    parser.add_argument("--thread-id", action="append", default=[], help="Individual Codex conversation/thread ID.")
    parser.add_argument("--title-contains", action="append", default=[], help="Select conversations by title keyword.")
    parser.add_argument("--out", default=str(Path.home() / "Desktop"), help="Output folder for the restore package.")
    parser.add_argument("--name", help="Package folder/zip name.")
    parser.add_argument("--exclude-name", action="append", default=[], help="Extra folder name to exclude from project files.")
    parser.add_argument("--no-project-files", action="store_true", help="Only package Codex conversation data.")
    parser.add_argument(
        "--include-thread-cwd-files",
        action="store_true",
        help="Also copy the cwd folder for conversations selected by --thread-id or --title-contains.",
    )
    parser.add_argument("--list", action="store_true", help="List likely projects and recent conversations, then exit.")
    args = parser.parse_args(argv)
    if args.list:
        return args
    if not args.project and not args.thread_id and not args.title_contains:
        parser.error("Provide --project, --thread-id, --title-contains, or --list.")
    return args


def main(argv: list[str] | None = None) -> None:
    configure_stdio()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.list:
        list_candidates()
        return
    build_package(args)


if __name__ == "__main__":
    main()
