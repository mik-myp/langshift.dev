"""Behavioral/teaching-boundary checks for L01; not part of the learner download."""

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "examples/js2py/u01-scalars"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
CASES = json.loads((Path(__file__).parent / "fixtures/js2py-scalars.json").read_text())
LESSONS = sorted((ROOT / "content/docs/js2py").glob("module-01-syntax-comparison*.mdx"))
SPEC = importlib.util.spec_from_file_location(
    "scalars_checker", ROOT / "scripts/check-js2py-content.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def execute(code, cwd):
    path = Path(cwd) / "learner.py"
    path.write_text(code, encoding="utf-8")
    return subprocess.run(
        [PYTHON, "-I", str(path)], cwd=cwd, capture_output=True, text=True, timeout=10
    )


def case_id(metadata):
    return next(part.split("=", 1)[1] for part in metadata if part.startswith("case="))


class ScalarChecks(unittest.TestCase):
    def check_behavior(self, result, expected):
        self.assertEqual(result.stdout, expected["stdout"])
        if "error" in expected:
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                result.stderr.splitlines()[-1].startswith(expected["error"] + ":")
            )
            if "error_line" in expected:
                self.assertIn(f"line {expected['error_line']}", result.stderr)
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")

    def test_shared_files_in_fresh_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, expected in CASES["files"].items():
                with self.subTest(file=name):
                    self.check_behavior(
                        execute((LAB / name).read_text(), directory), expected
                    )

    def test_all_translated_python_fences_in_fresh_processes(self):
        self.assertEqual(len(LESSONS), 3)
        with tempfile.TemporaryDirectory() as directory:
            for lesson in LESSONS:
                seen = []
                for line, code, metadata in CHECKER.python_blocks(lesson.read_text()):
                    name = case_id(metadata)
                    seen.append(name)
                    with self.subTest(lesson=lesson.name, line=line):
                        self.check_behavior(
                            execute(code, directory), CASES["fences"][name]
                        )
                self.assertEqual(set(seen), set(CASES["fences"]))
                self.assertEqual(len(seen), len(set(seen)))

    def test_javascript_comparison_is_real_not_assumed(self):
        for lesson in LESSONS:
            seen = []
            for match in CHECKER.FENCE.finditer(lesson.read_text()):
                metadata = match.group(1).split()
                if not metadata or metadata[0] != "javascript":
                    continue
                name = case_id(metadata)
                seen.append(name)
                result = subprocess.run(
                    ["node", "--input-type=module", "-e", match.group(2)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.check_behavior(result, CASES["javascript"][name])
            self.assertEqual(seen, list(CASES["javascript"]))

    def test_displayed_results_match_the_behavior_fixtures(self):
        for lesson in LESSONS:
            text = lesson.read_text()
            for group in ("files", "fences"):
                for name, case in CASES[group].items():
                    if case["stdout"]:
                        with self.subTest(lesson=lesson.name, case=name):
                            self.assertIn("```text\n" + case["stdout"] + "```", text)
            for name in ("errors/text_plus_number.py", "errors/invalid_integer.py"):
                self.assertIn(CASES["files"][name]["error"] + ":", text)
            details = re.findall(r"<details([^>]*)>", text)
            self.assertEqual(details, ["", "", ""])
            self.assertNotIn("canRun={true}", text)

    def test_input_variations_change_calculations_not_just_labels(self):
        cases = [
            (
                "task_estimate.py",
                '"95"',
                '"125"',
                "Task: Read Python basics\nEstimate: 2h 5m\nDecimal hours: 2.08\n",
            ),
            (
                "task_estimate.py",
                '"95"',
                '"60"',
                "Task: Read Python basics\nEstimate: 1h 0m\nDecimal hours: 1.00\n",
            ),
            ("solutions/fix_minutes.py", '"30"', '"50"', "65\nfinished\n"),
            (
                "solutions/reading_plan.py",
                '"4"',
                '"5"',
                "Topic: Python names\nSessions: 5\nTotal: 125 minutes (2h 5m)\n",
            ),
            (
                "solutions/reading_plan.py",
                '"  Python names  "',
                '"  Read slowly  "',
                "Topic: Read slowly\nSessions: 4\nTotal: 100 minutes (1h 40m)\n",
            ),
            (
                "solutions/reading_plan.py",
                "minutes_per_session = 25",
                "minutes_per_session = 30",
                "Topic: Python names\nSessions: 4\nTotal: 120 minutes (2h 0m)\n",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for name, old, new, output in cases:
                code = (LAB / name).read_text()
                self.assertEqual(code.count(old), 1)
                with self.subTest(file=name, replacement=new):
                    self.check_behavior(
                        execute(code.replace(old, new), directory), {"stdout": output}
                    )
            code = (
                (LAB / "solutions/reading_plan.py").read_text().replace('"4"', '"many"')
            )
            self.check_behavior(
                execute(code, directory),
                {"stdout": "", "error": "ValueError", "error_line": 6},
            )

    def test_scalar_sources_only_use_taught_constructs(self):
        allowed = (
            ast.Module,
            ast.Assign,
            ast.Expr,
            ast.Name,
            ast.Constant,
            ast.Call,
            ast.Load,
            ast.Store,
            ast.BinOp,
            ast.UnaryOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.Compare,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.Attribute,
            ast.JoinedStr,
            ast.FormattedValue,
        )
        samples = [(LAB / name).read_text() for name in CASES["files"]]
        for lesson in LESSONS:
            samples.extend(
                code for _, code, _ in CHECKER.python_blocks(lesson.read_text())
            )
        for code in samples:
            for node in ast.walk(ast.parse(code)):
                self.assertIsInstance(node, allowed, code)
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.assertIn(
                            node.func.id,
                            {"print", "type", "len", "int", "float", "str"},
                        )
                    else:
                        self.assertIsInstance(node.func, ast.Attribute)
                        self.assertEqual(node.func.attr, "strip")
                        self.assertEqual(node.args, [])

    def test_zip_is_exactly_the_allowed_beginner_sources(self):
        names = json.loads((ROOT / "examples/js2py/u01-scalars-files.json").read_text())
        self.assertEqual(set(names), {"README.md", *CASES["files"]})
        self.assertEqual(len(names), len(set(names)))
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u01-scalars.zip"
        ) as archive:
            self.assertEqual(
                set(archive.namelist()), {f"u01-scalars/{name}" for name in names}
            )
            for name in names:
                self.assertEqual(
                    archive.read(f"u01-scalars/{name}"), (LAB / name).read_bytes()
                )

    def test_parity_checker_catches_translation_and_reference_drift(self):
        lesson = {
            "loader": "getScalarExample",
            "refs": ["bindings.py"],
            "compare_text": True,
            "download": "/u01-scalars.zip",
            "forbidden": ["getU00Example("],
        }
        text = "getScalarExample('bindings.py')\n/u01-scalars.zip\n```python\nprint(30)\n```\n```text\n30\n```\n"
        texts = {locale: text for locale in ("en", "zh-cn", "zh-tw")}
        self.assertEqual(
            CHECKER.source_parity_errors(texts, ["bindings.py"], lesson), []
        )
        texts["en"] = text.replace("print(30)", "print(45)")
        self.assertTrue(CHECKER.source_parity_errors(texts, ["bindings.py"], lesson))
        texts["en"] = text.replace("bindings.py", "unknown.py")
        self.assertTrue(CHECKER.source_parity_errors(texts, ["bindings.py"], lesson))
        texts["en"] = text.replace("\n30\n", "\n45\n")
        self.assertTrue(CHECKER.source_parity_errors(texts, ["bindings.py"], lesson))
        del texts["en"]
        self.assertTrue(CHECKER.source_parity_errors(texts, ["bindings.py"], lesson))


if __name__ == "__main__":
    unittest.main()
