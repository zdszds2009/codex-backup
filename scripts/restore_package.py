from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "select 1 from sqlite_master where type='table' and name=?",
        (table,),
    ).fetchone()
    return row is not None


def table_columns(con: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in con.execute(f"pragma table_info({quote_ident(table)})")]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, backup)
    return backup


def extract_if_needed(package: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if package.is_dir():
        return package, None
    temp = tempfile.TemporaryDirectory(prefix="codex-restore-")
    with zipfile.ZipFile(package, "r") as zipf:
        zipf.extractall(temp.name)
    return Path(temp.name), temp


def parse_project_targets(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Invalid --project-target value: {value}")
        key, target = value.split("=", 1)
        result[key.strip()] = Path(target.strip()).expanduser().resolve()
    return result


def normalize_rollout_line(item: Any) -> Any:
    if isinstance(item, dict):
        payload = item.get("payload")
        if isinstance(payload, dict) and "model_provider" in payload:
            payload["model_provider"] = "custom"
        if item.get("type") == "session_meta" and isinstance(payload, dict):
            payload["model_provider"] = "custom"
    return item


def copy_rollout(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("r", encoding="utf-8", errors="replace") as reader, dst.open("w", encoding="utf-8") as writer:
        for line in reader:
            stripped = line.strip()
            if not stripped:
                writer.write(line)
                continue
            try:
                writer.write(json.dumps(normalize_rollout_line(json.loads(stripped)), ensure_ascii=False) + "\n")
            except json.JSONDecodeError:
                writer.write(line)
    shutil.copystat(src, dst)


def copy_project_files(package_root: Path, manifest: dict[str, Any], targets: dict[str, Path]) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for project in manifest.get("projects", []):
        key = project["key"]
        source_root = Path(project["source_root"])
        target = targets.get(key, source_root)
        src = package_root / project["package_path"]
        if not src.exists():
            continue
        target.mkdir(parents=True, exist_ok=True)
        for item in src.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(src)
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dst)
        resolved[key] = target
    return resolved


def thread_target_maps(manifest: dict[str, Any], project_targets: dict[str, Path]) -> dict[str, str]:
    source_to_target: dict[str, str] = {}
    for project in manifest.get("projects", []):
        source = str(Path(project["source_root"]))
        target = str(project_targets.get(project["key"], Path(project["source_root"])))
        source_to_target[source] = target
    return source_to_target


def mapped_cwd(cwd: str | None, source_to_target: dict[str, str]) -> str | None:
    if not cwd:
        return None
    value = str(Path(cwd.replace("\\\\?\\", "")))
    for source, target in source_to_target.items():
        if value.casefold() == source.casefold():
            return target
    return value


def copy_rollouts(package_root: Path, manifest: dict[str, Any], codex_home: Path) -> dict[str, str]:
    thread_rollout_paths: dict[str, str] = {}
    for rollout in manifest.get("rollouts", []):
        rel = rollout.get("target_codex_relative_path")
        thread_id = rollout.get("thread_id")
        package_path = rollout.get("path")
        if not rel or not package_path or not thread_id:
            continue
        src = package_root / package_path
        if not src.exists():
            continue
        dst = codex_home / rel
        copy_rollout(src, dst)
        thread_rollout_paths[str(thread_id)] = str(dst)
    return thread_rollout_paths


def delete_existing_thread_rows(con: sqlite3.Connection, thread_ids: list[str]) -> None:
    if not thread_ids:
        return
    placeholders = ",".join("?" for _ in thread_ids)
    if table_exists(con, "thread_dynamic_tools"):
        con.execute(f"delete from thread_dynamic_tools where thread_id in ({placeholders})", thread_ids)
    if table_exists(con, "thread_spawn_edges"):
        con.execute(f"delete from thread_spawn_edges where parent_thread_id in ({placeholders})", thread_ids)
        con.execute(f"delete from thread_spawn_edges where child_thread_id in ({placeholders})", thread_ids)
    if table_exists(con, "threads"):
        con.execute(f"delete from threads where id in ({placeholders})", thread_ids)


def copy_table_rows(
    src: sqlite3.Connection,
    dst: sqlite3.Connection,
    table: str,
    where_sql: str,
    where_args: list[str],
) -> int:
    if not table_exists(src, table) or not table_exists(dst, table):
        return 0
    src_cols = table_columns(src, table)
    dst_cols = table_columns(dst, table)
    common_cols = [col for col in src_cols if col in dst_cols]
    if not common_cols:
        return 0
    select_cols = ", ".join(quote_ident(col) for col in common_cols)
    insert_cols = ", ".join(quote_ident(col) for col in common_cols)
    placeholders = ", ".join("?" for _ in common_cols)
    rows = src.execute(f"select {select_cols} from {quote_ident(table)} {where_sql}", where_args).fetchall()
    for row in rows:
        dst.execute(
            f"insert into {quote_ident(table)} ({insert_cols}) values ({placeholders})",
            [row[index] for index in range(len(common_cols))],
        )
    return len(rows)


def merge_state_db(
    package_root: Path,
    manifest: dict[str, Any],
    codex_home: Path,
    source_to_target: dict[str, str],
    rollout_paths: dict[str, str],
) -> None:
    source_db = package_root / "codex" / "backup_state.sqlite"
    target_db = codex_home / "state_5.sqlite"
    if not source_db.exists():
        raise SystemExit(f"Missing source database: {source_db}")
    if not target_db.exists():
        raise SystemExit(f"Missing target Codex database: {target_db}")

    thread_ids = [thread["id"] for thread in manifest.get("threads", []) if thread.get("id")]
    placeholders = ",".join("?" for _ in thread_ids)
    src = sqlite3.connect(source_db)
    dst = sqlite3.connect(target_db)
    try:
        delete_existing_thread_rows(dst, thread_ids)
        copy_table_rows(src, dst, "threads", f"where id in ({placeholders})", thread_ids)
        copy_table_rows(src, dst, "thread_dynamic_tools", f"where thread_id in ({placeholders})", thread_ids)
        copy_table_rows(
            src,
            dst,
            "thread_spawn_edges",
            f"where parent_thread_id in ({placeholders}) or child_thread_id in ({placeholders})",
            thread_ids + thread_ids,
        )

        thread_cols = set(table_columns(dst, "threads")) if table_exists(dst, "threads") else set()
        for thread in manifest.get("threads", []):
            thread_id = thread.get("id")
            if not thread_id:
                continue
            if "cwd" in thread_cols:
                cwd = mapped_cwd(thread.get("cwd"), source_to_target)
                dst.execute("update threads set cwd=? where id=?", (cwd, thread_id))
            if "rollout_path" in thread_cols and thread_id in rollout_paths:
                dst.execute("update threads set rollout_path=? where id=?", (rollout_paths[thread_id], thread_id))
            if "model_provider" in thread_cols:
                dst.execute("update threads set model_provider='custom' where id=?", (thread_id,))
        dst.commit()
    finally:
        src.close()
        dst.close()


def patch_paths_in_json(value: Any, source_to_target: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: patch_paths_in_json(inner, source_to_target) for key, inner in value.items()}
    if isinstance(value, list):
        return [patch_paths_in_json(item, source_to_target) for item in value]
    if isinstance(value, str):
        result = value
        for source, target in source_to_target.items():
            result = result.replace(source, target)
        return result
    return value


def merge_session_index(package_root: Path, manifest: dict[str, Any], codex_home: Path, source_to_target: dict[str, str]) -> None:
    source_index = package_root / "codex" / "session_index.jsonl"
    target_index = codex_home / "session_index.jsonl"
    selected_ids = {thread["id"] for thread in manifest.get("threads", []) if thread.get("id")}

    existing: list[dict[str, Any]] = []
    if target_index.exists():
        for line in target_index.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = item.get("id") or item.get("thread_id")
            if item_id not in selected_ids:
                existing.append(item)

    incoming: list[dict[str, Any]] = []
    if source_index.exists():
        for line in source_index.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                incoming.append(patch_paths_in_json(json.loads(line), source_to_target))
            except json.JSONDecodeError:
                continue

    lines = [json.dumps(item, ensure_ascii=False) for item in existing + incoming]
    target_index.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def merge_global_state(package_root: Path, manifest: dict[str, Any], codex_home: Path, source_to_target: dict[str, str]) -> None:
    target_path = codex_home / ".codex-global-state.json"
    target: dict[str, Any] = {}
    if target_path.exists():
        try:
            target = load_json(target_path)
        except json.JSONDecodeError:
            target = {}

    roots = sorted(set(source_to_target.values()), key=str.casefold)
    for key in ["electron-saved-workspace-roots", "active-workspace-roots", "project-order"]:
        current = [item for item in target.get(key, []) if isinstance(item, str)]
        for root in roots:
            if root not in current:
                current.append(root)
        target[key] = current

    hints = target.setdefault("thread-workspace-root-hints", {})
    for thread in manifest.get("threads", []):
        thread_id = thread.get("id")
        cwd = mapped_cwd(thread.get("cwd"), source_to_target)
        if thread_id and cwd:
            hints[thread_id] = cwd

    selected_ids = {thread["id"] for thread in manifest.get("threads", []) if thread.get("id")}
    target["projectless-thread-ids"] = [
        thread_id for thread_id in target.get("projectless-thread-ids", []) if thread_id not in selected_ids
    ]
    target_path.write_text(json.dumps(target, ensure_ascii=False, indent=2), encoding="utf-8")


def restore(args: argparse.Namespace) -> None:
    package_arg = Path(args.package).expanduser().resolve()
    package_root, temp = extract_if_needed(package_arg)
    try:
        manifest = load_json(package_root / "manifest.json")
        codex_home = Path(args.codex_home).expanduser().resolve()
        codex_home.mkdir(parents=True, exist_ok=True)

        targets = parse_project_targets(args.project_target)
        resolved_targets = copy_project_files(package_root, manifest, targets)
        source_to_target = thread_target_maps(manifest, resolved_targets)

        backup_file(codex_home / "state_5.sqlite")
        backup_file(codex_home / "session_index.jsonl")
        backup_file(codex_home / ".codex-global-state.json")

        rollout_paths = copy_rollouts(package_root, manifest, codex_home)
        merge_state_db(package_root, manifest, codex_home, source_to_target, rollout_paths)
        merge_session_index(package_root, manifest, codex_home, source_to_target)
        merge_global_state(package_root, manifest, codex_home, source_to_target)

        print(f"restored_threads={manifest.get('thread_count', 0)}")
        print(f"restored_projects={len(resolved_targets)}")
        print(f"codex_home={codex_home}")
        print("Restart Codex Desktop, then open the restored project or conversation.")
    finally:
        if temp is not None:
            temp.cleanup()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore a Codex project/conversation restore package.")
    parser.add_argument("--package", default=".", help="Extracted package folder or restore package zip.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"), help="Target Codex home folder.")
    parser.add_argument(
        "--project-target",
        action="append",
        default=[],
        help='Project destination mapping, for example "skills=C:\\Users\\you\\Documents\\skills".',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    configure_stdio()
    restore(parse_args(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    main()
