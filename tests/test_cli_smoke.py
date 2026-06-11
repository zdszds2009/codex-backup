import importlib.util
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
