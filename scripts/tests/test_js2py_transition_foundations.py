"""Static maintainer guards, distinct from actual CPython/uv integration."""

import ast
import hashlib
import importlib.util
import json
import re
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads(
    (ROOT / "scripts/tests/fixtures/js2py-transition-foundations.json").read_text()
)
spec = importlib.util.spec_from_file_location(
    "transition_content_checks", ROOT / "scripts/check-js2py-content.py"
)
CHECKS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CHECKS)


class TransitionFoundationTests(unittest.TestCase):
    def test_allowlists_are_unique_safe_and_complete_for_author_sources(self):
        for row in ROWS:
            lab = ROOT / "examples/js2py" / row["lab"]
            names = json.loads((lab.parent / (row["lab"] + "-files.json")).read_text())
            self.assertEqual(names, sorted(set(names)))
            for name in names:
                self.assertFalse(Path(name).is_absolute())
                self.assertNotIn("..", Path(name).parts)
                self.assertTrue((lab / name).is_file())
                self.assertFalse((lab / name).is_symlink())
                self.assertFalse(
                    set(Path(name).parts)
                    & {".venv", ".mypy_cache", "__pycache__", ".pytest_cache"}
                )
            for name in [
                "README.md",
                "README.zh-cn.md",
                "README.zh-tw.md",
                "uv.lock",
                "pyproject.toml",
                ".python-version",
            ]:
                self.assertIn(name, names)
            self.assertTrue(set(row["refs"]) <= set(names))

    def test_fixed_interpreter_dependencies_and_public_registry_artifacts(self):
        for row in ROWS:
            lab = ROOT / "examples/js2py" / row["lab"]
            config = tomllib.loads((lab / "pyproject.toml").read_text())
            self.assertEqual(config["project"]["requires-python"], ">=3.13,<3.14")
            self.assertEqual(config["project"]["dependencies"], [])
            self.assertFalse(config["tool"]["uv"]["package"])
            self.assertEqual((lab / ".python-version").read_text(), "3.13.15\n")
            self.assertIn("pytest==8.4.2", config["dependency-groups"]["dev"])
            for package in tomllib.loads((lab / "uv.lock").read_text())["package"]:
                if "registry" in package["source"]:
                    self.assertEqual(
                        package["source"]["registry"], "https://pypi.org/simple"
                    )
                    for artifact in package.get("wheels", []) + (
                        [package["sdist"]] if "sdist" in package else []
                    ):
                        self.assertTrue(
                            artifact["url"].startswith(
                                "https://files.pythonhosted.org/"
                            )
                        )
                        self.assertRegex(artifact["hash"], r"^sha256:[a-f0-9]{64}$")

    def test_three_locales_share_sources_commands_outputs_and_structure(self):
        for row in ROWS:
            texts = {
                p.name: p.read_text()
                for p in (ROOT / "content/docs/js2py").glob(row["slug"] + "*.mdx")
            }
            self.assertEqual(len(texts), 3)
            lesson = {
                **row,
                "compare_text": True,
                "download": "/learning-assets/js2py/" + row["lab"] + ".zip",
                "forbidden": [],
            }
            names = json.loads(
                (ROOT / f"examples/js2py/{row['lab']}-files.json").read_text()
            )
            self.assertEqual(CHECKS.source_parity_errors(texts, names, lesson), [])
            for text in texts.values():
                self.assertEqual(len(re.findall(r"^## ", text, re.M)), row["sections"])
                self.assertEqual(text.count("<details>"), 3)
                self.assertEqual(text.count("</details>"), 3)
                self.assertNotIn("<details open", text)

    def test_prerequisites_do_not_sneak_future_execution_forms_into_sources(self):
        for index, row in enumerate(ROWS):
            lab = ROOT / "examples/js2py" / row["lab"]
            names = json.loads((lab.parent / (row["lab"] + "-files.json")).read_text())
            for name in names:
                if not name.endswith(".py"):
                    continue
                for node in ast.walk(ast.parse((lab / name).read_text())):
                    self.assertNotIsInstance(
                        node,
                        (ast.AsyncFunctionDef, ast.Await, ast.AsyncWith, ast.AsyncFor),
                    )
                    if index < 3:
                        self.assertNotIsInstance(
                            node, (ast.Yield, ast.YieldFrom, ast.GeneratorExp)
                        )
                    if index == 0:
                        self.assertNotIsInstance(node, ast.ClassDef)
                        if isinstance(node, ast.FunctionDef):
                            self.assertEqual(node.decorator_list, [])

    def test_declared_smoke_scope_moved_to_actual_l11_and_is_opt_in(self):
        files = sorted(
            (ROOT / "content/docs/js2py").glob("module-11-pythonic-code*.mdx")
        )
        self.assertEqual(len(files), 3)
        self.assertEqual(
            sum(
                len(re.findall(r"^```python smoke=typing$", p.read_text(), re.M))
                for p in files
            ),
            9,
        )
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "lesson.mdx"
            page.write_text('```python\nraise RuntimeError("not selected")\n```\n')
            with patch.object(CHECKS.subprocess, "run") as runner:
                self.assertEqual(CHECKS.run_typing_snippets([page]), (0, []))
                runner.assert_not_called()

    def test_smoke_runner_reports_selected_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "lesson.mdx"
            page.write_text(
                '```python smoke=typing\nraise ValueError("intentional")\n```\n'
            )
            count, errors = CHECKS.run_typing_snippets([page])
            self.assertEqual(count, 1)
            self.assertEqual(len(errors), 1)
            self.assertIn("ValueError", errors[0])

    def test_current_worktree_archives_have_unchanged_bytes(self):
        for archive in ["js2py-u11-pythonic", "js2py-u12-typing"]:
            directory = ROOT / "docs/archive" / archive
            digests = json.loads((directory / "sha256.json").read_text())
            self.assertEqual(len(digests), 3)
            for name, digest in digests.items():
                self.assertEqual(
                    hashlib.sha256((directory / name).read_bytes()).hexdigest(), digest
                )

    def test_loader_archive_and_package_registration(self):
        loaders = (ROOT / "lib/js2py-examples.ts").read_text()
        builder = (ROOT / "scripts/build-js2py-lab.py").read_text()
        for row in ROWS:
            self.assertIn("export function " + row["loader"], loaders)
            self.assertIn(row["lab"] + "-files.json", loaders)
            self.assertIn('"' + row["lab"] + '": (', builder)
        scripts = json.loads((ROOT / "package.json").read_text())["scripts"]
        self.assertIn(
            "python3 scripts/test-js2py-transitions.py", scripts["test:js2py-lab"]
        )


if __name__ == "__main__":
    unittest.main()
