import importlib.util
import json
import sqlite3
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).resolve().parents[1]
BUILD = load_module("build_restore_package", ROOT / "scripts" / "build_restore_package.py")
RESTORE = load_module("restore_package", ROOT / "scripts" / "restore_package.py")
INSPECT = load_module("inspect_package", ROOT / "scripts" / "inspect_package.py")


def init_state_db(path: Path) -> None:
    con = sqlite3.connect(path)
    try:
        con.execute(
            """
            create table threads (
                id text primary key,
                title text,
                cwd text,
                rollout_path text,
                updated_at integer,
                archived integer,
                model_provider text
            )
            """
        )
        con.execute(
            """
            create table thread_dynamic_tools (
                thread_id text,
                tool_name text
            )
            """
        )
        con.execute(
            """
            create table thread_spawn_edges (
                parent_thread_id text,
                child_thread_id text
            )
            """
        )
        con.commit()
    finally:
        con.close()


def read_jsonl(path: Path) -> list[dict]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


@contextmanager
def patched_codex_home(codex_home: Path):
    original_home = BUILD.CODEX_HOME
    original_state = BUILD.STATE_DB
    original_index = BUILD.SESSION_INDEX
    original_global = BUILD.GLOBAL_STATE
    BUILD.CODEX_HOME = codex_home
    BUILD.STATE_DB = codex_home / "state_5.sqlite"
    BUILD.SESSION_INDEX = codex_home / "session_index.jsonl"
    BUILD.GLOBAL_STATE = codex_home / ".codex-global-state.json"
    try:
        yield
    finally:
        BUILD.CODEX_HOME = original_home
        BUILD.STATE_DB = original_state
        BUILD.SESSION_INDEX = original_index
        BUILD.GLOBAL_STATE = original_global


class BuildScriptTests(unittest.TestCase):
    def test_safe_name_normalizes_text(self):
        self.assertEqual(BUILD.safe_name("Project Restore Packager"), "Project-Restore-Packager")
        self.assertEqual(BUILD.safe_name("  "), "item")

    def test_thread_selection_does_not_include_cwd_files_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "workspace"
            project.mkdir()
            selected = [{"cwd": str(project)}]
            roots = BUILD.project_roots_for_selected(selected, [], include_thread_cwd_files=False)
            self.assertEqual(roots, [])

    def test_thread_selection_can_include_cwd_files_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "workspace"
            project.mkdir()
            selected = [{"cwd": str(project)}]
            roots = BUILD.project_roots_for_selected(selected, [], include_thread_cwd_files=True)
            self.assertEqual(roots, [project])

    def test_parse_args_accepts_include_thread_cwd_files(self):
        args = BUILD.parse_args(["--thread-id", "abc", "--include-thread-cwd-files"])
        self.assertTrue(args.include_thread_cwd_files)


class RestoreScriptTests(unittest.TestCase):
    def test_patch_paths_in_json_rewrites_nested_strings(self):
        source = {"cwd": "C:\\src", "items": ["C:\\src\\file.py"]}
        rewritten = RESTORE.patch_paths_in_json(source, {"C:\\src": "D:\\dst"})
        self.assertEqual(rewritten["cwd"], "D:\\dst")
        self.assertEqual(rewritten["items"][0], "D:\\dst\\file.py")

    def test_normalize_rollout_line_sets_custom_provider(self):
        value = {"type": "session_meta", "payload": {"model_provider": "openai"}}
        normalized = RESTORE.normalize_rollout_line(value)
        self.assertEqual(normalized["payload"]["model_provider"], "custom")

    def test_build_and_restore_round_trip_with_fixture_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_codex = root / "source-codex"
            source_codex.mkdir()
            init_state_db(source_codex / "state_5.sqlite")

            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "main.py").write_text("print('hello')\n", encoding="utf-8")

            rollout_dir = source_codex / "rollouts"
            rollout_dir.mkdir()
            rollout_path = rollout_dir / "thread-1.jsonl"
            rollout_path.write_text(
                json.dumps({"type": "session_meta", "payload": {"model_provider": "openai"}}) + "\n",
                encoding="utf-8",
            )

            con = sqlite3.connect(source_codex / "state_5.sqlite")
            try:
                con.execute(
                    "insert into threads (id, title, cwd, rollout_path, updated_at, archived, model_provider) values (?, ?, ?, ?, ?, ?, ?)",
                    ("thread-1", "Demo thread", str(workspace), str(rollout_path), 1710000000, 0, "openai"),
                )
                con.execute(
                    "insert into threads (id, title, cwd, rollout_path, updated_at, archived, model_provider) values (?, ?, ?, ?, ?, ?, ?)",
                    ("thread-2", "Other thread", str(root / "other"), str(rollout_dir / "thread-2.jsonl"), 1710000100, 0, "openai"),
                )
                con.execute("insert into thread_dynamic_tools (thread_id, tool_name) values (?, ?)", ("thread-1", "tool-a"))
                con.execute(
                    "insert into thread_spawn_edges (parent_thread_id, child_thread_id) values (?, ?)",
                    ("thread-1", "thread-2"),
                )
                con.commit()
            finally:
                con.close()

            (source_codex / "session_index.jsonl").write_text(
                json.dumps({"id": "thread-1", "cwd": str(workspace)}) + "\n"
                + json.dumps({"id": "thread-2", "cwd": str(root / "other")}) + "\n",
                encoding="utf-8",
            )
            (source_codex / ".codex-global-state.json").write_text(
                json.dumps(
                    {
                        "electron-saved-workspace-roots": [str(workspace)],
                        "thread-workspace-root-hints": {"thread-1": str(workspace)},
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            out_dir = root / "out"
            out_dir.mkdir()
            with patched_codex_home(source_codex):
                build_args = BUILD.parse_args(
                    [
                        "--thread-id",
                        "thread-1",
                        "--include-thread-cwd-files",
                        "--out",
                        str(out_dir),
                        "--name",
                        "fixture-package",
                    ]
                )
                zip_path = BUILD.build_package(build_args)

            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path, "r") as zipf:
                names = set(zipf.namelist())
                self.assertIn("manifest.json", names)
                self.assertIn("codex/backup_state.sqlite", names)
                self.assertIn("codex/rollouts/thread-1.jsonl", names)
                manifest = json.loads(zipf.read("manifest.json").decode("utf-8"))

            self.assertEqual(manifest["thread_count"], 1)
            self.assertIn("source_schema", manifest)
            self.assertIn("threads", manifest["source_schema"]["tables"])

            target_codex = root / "target-codex"
            target_codex.mkdir()
            init_state_db(target_codex / "state_5.sqlite")
            (target_codex / "session_index.jsonl").write_text(
                json.dumps({"id": "existing-thread", "cwd": "C:\\existing"}) + "\n",
                encoding="utf-8",
            )
            (target_codex / ".codex-global-state.json").write_text(
                json.dumps({"electron-saved-workspace-roots": ["C:\\existing"]}, indent=2),
                encoding="utf-8",
            )

            restored_project = root / "restored-workspace"
            restore_args = RESTORE.parse_args(
                [
                    "--package",
                    str(zip_path),
                    "--codex-home",
                    str(target_codex),
                    "--project-target",
                    f"workspace={restored_project}",
                ]
            )
            RESTORE.restore(restore_args)

            con = sqlite3.connect(target_codex / "state_5.sqlite")
            try:
                row = con.execute("select cwd, rollout_path, model_provider from threads where id=?", ("thread-1",)).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], str(restored_project))
                self.assertTrue(str(row[1]).endswith("rollouts\\thread-1.jsonl") or str(row[1]).endswith("rollouts/thread-1.jsonl"))
                self.assertEqual(row[2], "custom")
            finally:
                con.close()

            restored_rollout = target_codex / "rollouts" / "thread-1.jsonl"
            self.assertTrue(restored_rollout.exists())
            rollout_lines = read_jsonl(restored_rollout)
            self.assertEqual(rollout_lines[0]["payload"]["model_provider"], "custom")

            restored_file = restored_project / "main.py"
            self.assertTrue(restored_file.exists())

            merged_index = read_jsonl(target_codex / "session_index.jsonl")
            self.assertEqual({item["id"] for item in merged_index}, {"existing-thread", "thread-1"})
            self.assertEqual(
                next(item for item in merged_index if item["id"] == "thread-1")["cwd"],
                str(restored_project),
            )

            merged_global = json.loads((target_codex / ".codex-global-state.json").read_text(encoding="utf-8"))
            self.assertIn(str(restored_project), merged_global["electron-saved-workspace-roots"])
            self.assertEqual(merged_global["thread-workspace-root-hints"]["thread-1"], str(restored_project))

            self.assertEqual(len(list(target_codex.glob("state_5.sqlite.bak-*"))), 1)
            self.assertEqual(len(list(target_codex.glob("session_index.jsonl.bak-*"))), 1)
            self.assertEqual(len(list(target_codex.glob(".codex-global-state.json.bak-*"))), 1)


class InspectScriptTests(unittest.TestCase):
    def test_summarize_manifest_reports_basic_package_details(self):
        manifest = {
            "package_name": "fixture-package",
            "created_at": "2026-06-11T23:59:00",
            "thread_count": 1,
            "projects": [{"key": "workspace", "source_root": "C:\\src", "file_count": 3}],
            "rollouts": [{"thread_id": "thread-1"}],
            "source_schema": {"tables": {"threads": ["id", "cwd"]}},
            "threads": [{"id": "thread-1", "title": "Demo", "cwd": "C:\\src", "archived": False}],
        }

        lines = INSPECT.summarize_manifest(manifest)

        self.assertIn("package_name=fixture-package", lines)
        self.assertIn("thread_count=1", lines)
        self.assertIn("project_count=1", lines)
        self.assertIn("rollout_count=1", lines)
        self.assertIn("schema_tables=threads", lines)
        self.assertTrue(any(line.startswith("project=") for line in lines))
        self.assertTrue(any(line.startswith("thread=") for line in lines))


if __name__ == "__main__":
    unittest.main()
