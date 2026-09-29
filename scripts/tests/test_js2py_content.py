import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_module("js2py_checker", "check-js2py-content.py")
archive_builder = load_module("js2py_archive", "build-js2py-lab.py")


class ContentChecks(unittest.TestCase):
    def test_invalid_lambda_is_rejected_with_source_line(self):
        errors = checker.syntax_errors(
            "Heading\n```python !! py\nmultiply = lambda a: float, b: float: a * b\n```\n",
            "lesson.mdx",
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("lesson.mdx:3:", errors[0])

    def test_configuration_is_not_compiled_as_python(self):
        self.assertEqual(
            checker.syntax_errors("```text\nflask>=2.3.0\n```\n", "config.mdx"), []
        )

    def test_explicit_syntax_counterexample_is_allowed(self):
        self.assertEqual(
            checker.syntax_errors(
                "```python expected-error=SyntaxError\nif:\n```\n", "example.mdx"
            ),
            [],
        )

    def test_counterexample_must_actually_fail(self):
        self.assertTrue(
            checker.syntax_errors(
                "```python expected-error=SyntaxError\nprint(1)\n```\n", "example.mdx"
            )
        )

    def test_top_level_await_is_syntax_only_not_runtime_approval(self):
        self.assertEqual(
            checker.syntax_errors("```python\nawait main()\n```\n", "async.mdx"), []
        )


class DownloadChecks(unittest.TestCase):
    def test_deterministic_archive_contains_only_allowed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text("print('ok')\n")
            (root / ".env").write_text("DO_NOT_PUBLISH=secret\n")
            manifest = root / "files.json"
            manifest.write_text(json.dumps(["main.py"]))
            first = archive_builder.build_archive(root, manifest)
            self.assertEqual(first, archive_builder.build_archive(root, manifest))
            with zipfile.ZipFile(io.BytesIO(first)) as archive:
                self.assertEqual(archive.namelist(), ["u00-environment/main.py"])
                self.assertEqual(archive.read(archive.namelist()[0]), b"print('ok')\n")

    def test_parent_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "files.json"
            manifest.write_text(json.dumps(["../outside.py"]))
            with self.assertRaises(ValueError):
                archive_builder.build_archive(root, manifest)

    def test_missing_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "files.json"
            manifest.write_text(json.dumps(["missing.py"]))
            with self.assertRaises(ValueError):
                archive_builder.build_archive(root, manifest)

    def test_explicit_class_edit_fragment_checks_in_class_context(self):
        fragment = "```python fragment=class-body\n    value: int = 1\n```\n"
        self.assertEqual(checker.syntax_errors(fragment, "fragment.mdx"), [])

    def test_class_edit_fragment_still_rejects_invalid_syntax(self):
        fragment = "```python fragment=class-body\n    value: = 1\n```\n"
        errors = checker.syntax_errors(fragment, "fragment.mdx")
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("fragment.mdx:2:"))

    def test_unlabelled_indented_fragment_is_not_silently_accepted(self):
        fragment = "```python\n    value: int = 1\n```\n"
        self.assertEqual(len(checker.syntax_errors(fragment, "fragment.mdx")), 1)


if __name__ == "__main__":
    unittest.main()
