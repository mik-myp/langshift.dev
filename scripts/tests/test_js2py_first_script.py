"""Maintainer tests: these are intentionally not prerequisites in the learner ZIP."""

import ast
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "examples/js2py/u00-first-script"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
SPEC = importlib.util.spec_from_file_location(
    "first_script_checker", ROOT / "scripts/check-js2py-content.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def execute(code, cwd):
    path = Path(cwd) / "learner.py"
    path.write_text(code, encoding="utf-8")
    return subprocess.run(
        [PYTHON, str(path)], cwd=cwd, capture_output=True, text=True, timeout=10
    )


class FirstScriptChecks(unittest.TestCase):
    def test_shared_program_and_answer_outputs(self):
        cases = [
            ("first_steps.py", "Hello!\nPython\n"),
            ("solutions/about_me.py", "My next skill:\nPython\nFastAPI\n"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for filename, expected in cases:
                with self.subTest(filename=filename):
                    result = execute((LAB / filename).read_text(), directory)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, expected)
                    self.assertEqual(result.stderr, "")

    def test_answer_really_reads_and_reassigns_the_name(self):
        code = (LAB / "solutions/about_me.py").read_text()
        with tempfile.TemporaryDirectory() as directory:
            result = execute(code.replace('"Python"', '"Python basics"', 1), directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "My next skill:\nPython basics\nFastAPI\n")
        assignments = [
            n for n in ast.walk(ast.parse(code)) if isinstance(n, ast.Assign)
        ]
        self.assertEqual(len(assignments), 2)
        self.assertTrue(all(n.targets[0].id == "subject" for n in assignments))

    def test_all_three_lessons_have_verified_fence_behavior(self):
        expected_outputs = [
            "Python\ncourse\n",
            "Python\n",
            "Python\n",
            "Python\nFastAPI\n",
            "Hello!\n",
            "",
            "Python\ntopic\nFastAPI\n",
        ]
        with tempfile.TemporaryDirectory() as directory:
            for lesson in sorted(
                (ROOT / "content/docs/js2py").glob("module-00-python-introduction*.mdx")
            ):
                blocks = list(CHECKER.python_blocks(lesson.read_text()))
                self.assertEqual(len(blocks), len(expected_outputs), lesson.name)
                for (line, code, metadata), stdout in zip(blocks, expected_outputs):
                    with self.subTest(lesson=lesson.name, line=line):
                        result = execute(code, directory)
                        expected_error = next(
                            (
                                s.split("=", 1)[1]
                                for s in metadata
                                if s.startswith("expected-error=")
                            ),
                            None,
                        )
                        self.assertEqual(result.stdout, stdout)
                        if expected_error:
                            self.assertNotEqual(result.returncode, 0)
                            self.assertIn(expected_error, result.stderr)
                        else:
                            self.assertEqual(result.returncode, 0, result.stderr)
                            self.assertEqual(result.stderr, "")

    def test_intro_code_does_not_require_future_python_constructs(self):
        lesson = ROOT / "content/docs/js2py/module-00-python-introduction.zh-cn.mdx"
        code_samples = [
            code
            for _, code, metadata in CHECKER.python_blocks(lesson.read_text())
            if "expected-error=SyntaxError" not in metadata
        ] + [
            (LAB / name).read_text()
            for name in ["first_steps.py", "solutions/about_me.py"]
        ]
        allowed = (
            ast.Module,
            ast.Assign,
            ast.Expr,
            ast.Name,
            ast.Constant,
            ast.Call,
            ast.Load,
            ast.Store,
        )
        for code in code_samples:
            for node in ast.walk(ast.parse(code)):
                self.assertIsInstance(node, allowed, code)
                if isinstance(node, ast.Call):
                    self.assertIsInstance(node.func, ast.Name)
                    self.assertEqual(node.func.id, "print")

    def test_download_only_contains_beginner_material_and_matches_source(self):
        data = (ROOT / "public/learning-assets/js2py/u00-first-script.zip").read_bytes()
        names = json.loads(
            (ROOT / "examples/js2py/u00-first-script-files.json").read_text()
        )
        self.assertEqual(
            set(names), {"README.md", "first_steps.py", "solutions/about_me.py"}
        )
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(
                set(archive.namelist()), {f"u00-first-script/{n}" for n in names}
            )
            for name in names:
                self.assertEqual(
                    archive.read(f"u00-first-script/{name}"), (LAB / name).read_bytes()
                )

    def test_chapter_contracts_only_depend_on_preceding_chapters(self):
        contracts = json.loads(
            (ROOT / "docs/js2py-chapter-contracts.json").read_text()
        )["chapters"]
        route = (ROOT / "docs/js2py-learning-path.zh-cn.md").read_text()
        seen = set()
        for chapter in contracts:
            self.assertNotIn(chapter["id"], seen)
            self.assertTrue(set(chapter["prerequisites"]) <= seen, chapter["id"])
            for field in ["teach", "acceptance", "boundary"]:
                self.assertTrue(chapter[field].strip())
            row = (
                f"| {chapter['id']} {chapter['title']} | "
                f"{', '.join(chapter['prerequisites']) or '仅既有前端基础'} | "
                f"{chapter['teach']} | {chapter['acceptance']} | {chapter['boundary']} |"
            )
            self.assertIn(row, route, chapter["id"])
            seen.add(chapter["id"])
        self.assertEqual(
            [c["id"] for c in contracts if c["status"] == "implemented"],
            [f"L{i:02d}" for i in range(15)]
            + [f"H{i:02d}" for i in range(1, 7)]
            + [f"D{i:02d}" for i in range(1, 7)]
            + [f"S{i:02d}" for i in range(1, 4)]
            + ["A01", "A02", "G01"],
        )
        self.assertEqual(
            [c["id"] for c in contracts if c["status"] == "environment_pending"],
            [f"O{i:02d}" for i in range(1, 7)],
        )


if __name__ == "__main__":
    unittest.main()
