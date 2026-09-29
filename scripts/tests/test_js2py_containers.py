"""L02 maintainer checks; learner scripts do not depend on this test framework."""

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
LAB = ROOT / "examples/js2py/u02-containers"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
CASES = json.loads(
    (Path(__file__).parent / "fixtures/js2py-containers.json").read_text()
)
LESSONS = sorted((ROOT / "content/docs/js2py").glob("module-02-module-system*.mdx"))
SPEC = importlib.util.spec_from_file_location(
    "containers_checker", ROOT / "scripts/check-js2py-content.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def execute(code, cwd, hash_seed=None):
    path = Path(cwd) / "learner.py"
    path.write_text(code, encoding="utf-8")
    # -I ignores PYTHONHASHSEED, so the explicit seed experiment must omit it.
    command = [PYTHON, "-I", str(path)] if hash_seed is None else [PYTHON, str(path)]
    env = None if hash_seed is None else dict(os.environ, PYTHONHASHSEED=hash_seed)
    return subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True, timeout=10
    )


def case_id(metadata):
    return next(part.split("=", 1)[1] for part in metadata if part.startswith("case="))


class ContainerChecks(unittest.TestCase):
    def check_behavior(self, result, expected):
        self.assertEqual(result.stdout, expected["stdout"])
        if "error" in expected:
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                result.stderr.splitlines()[-1].startswith(expected["error"] + ":")
            )
            self.assertIn(f"line {expected['error_line']}", result.stderr)
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")

    def test_shared_files_and_intentional_failures_in_fresh_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, expected in CASES["files"].items():
                with self.subTest(file=name):
                    self.check_behavior(
                        execute((LAB / name).read_text(), directory), expected
                    )

    def test_each_translated_python_fence_has_a_behavioral_contract(self):
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

    def test_javascript_identity_comparison_in_node(self):
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

    def test_prose_outputs_and_closed_answers_match_fixtures(self):
        for lesson in LESSONS:
            text = lesson.read_text()
            for group in ("files", "fences", "javascript"):
                for name, expected in CASES[group].items():
                    if expected["stdout"]:
                        with self.subTest(lesson=lesson.name, case=name):
                            self.assertIn(
                                "```text\n" + expected["stdout"] + "```", text
                            )
            for error in ("TypeError", "IndexError", "KeyError"):
                self.assertIn(error, text)
            self.assertEqual(re.findall(r"<details([^>]*)>", text), ["", "", ""])
            self.assertNotIn("canRun={true}", text)

    def test_examples_require_no_future_control_flow_imports_or_functions(self):
        allowed = (
            ast.Module,
            ast.Assign,
            ast.Expr,
            ast.Name,
            ast.Constant,
            ast.Call,
            ast.Load,
            ast.Store,
            ast.List,
            ast.Dict,
            ast.Tuple,
            ast.Set,
            ast.Subscript,
            ast.Slice,
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
            ast.BitAnd,
            ast.BitOr,
            ast.Compare,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.In,
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
                            {
                                "print",
                                "type",
                                "len",
                                "int",
                                "float",
                                "str",
                                "set",
                                "sorted",
                            },
                        )
                    else:
                        self.assertIsInstance(node.func, ast.Attribute)
                        self.assertIn(
                            node.func.attr,
                            {"append", "pop", "get", "copy", "add", "discard", "strip"},
                        )

    def test_changed_inputs_flow_through_the_independent_solutions(self):
        variations = [
            (
                "task_board.py",
                '"basics"',
                '"review"',
                CASES["files"]["task_board.py"]["stdout"].replace(
                    "'basics'", "'review'"
                ),
            ),
            (
                "task_board.py",
                '["minutes"] = 40',
                '["minutes"] = 55',
                CASES["files"]["task_board.py"]["stdout"].replace("\n40\n", "\n55\n"),
            ),
            (
                "solutions/fix_draft.py",
                '"python"',
                '"language"',
                "['language']\n['language', 'review']\nFalse\n",
            ),
            (
                "solutions/study_board.py",
                '["minutes"] = 35',
                '["minutes"] = 50',
                CASES["files"]["solutions/study_board.py"]["stdout"].replace(
                    "55 minutes", "70 minutes"
                ),
            ),
            (
                "solutions/study_board.py",
                '"python"',
                '"language"',
                CASES["files"]["solutions/study_board.py"]["stdout"].replace(
                    "'python'", "'language'"
                ),
            ),
            (
                "solutions/study_board.py",
                '"minutes": 20',
                '"minutes": 30',
                CASES["files"]["solutions/study_board.py"]["stdout"].replace(
                    "55 minutes", "65 minutes"
                ),
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for name, old, new, output in variations:
                code = (LAB / name).read_text()
                self.assertEqual(code.count(old), 1)
                with self.subTest(file=name, input=new):
                    self.check_behavior(
                        execute(code.replace(old, new), directory), {"stdout": output}
                    )

    def test_board_shares_tasks_but_not_template_tag_lists(self):
        name = "task_board.py"
        checks = """
print(board[0] is first)
print(board[1] is second)
print(first is second)
print(first is template)
print(first["tags"] is second["tags"])
print(second["tags"] is template["tags"])
first["tags"].append("later")
print(board[0]["tags"])
print(second["tags"])
print(template["tags"])
"""
        expected = CASES["files"][name]["stdout"] + (
            "True\nTrue\nFalse\nFalse\nFalse\nFalse\n"
            "['python', 'basics', 'later']\n['python']\n['python']\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute((LAB / name).read_text() + checks, directory),
                {"stdout": expected},
            )

    def test_independent_solution_preserves_absence_and_mutation_boundaries(self):
        name = "solutions/study_board.py"
        checks = """
print(plans[0] is first)
print(plans[1] is second)
print(first is template)
print(second is template)
print(first["topics"] is template["topics"])
print(second["topics"] is template["topics"])
first["topics"].append("later")
print(plans[0]["topics"])
print(second["topics"])
print(template["topics"])
print("owner" in template)
print(template["owner"] is None)
print("owner" in second)
print(first.get("owner"))
print(second.get("owner"))
"""
        expected = CASES["files"][name]["stdout"] + (
            "True\nTrue\nFalse\nFalse\nFalse\nFalse\n"
            "['python', 'later']\n['python', 'copy']\n['python']\n"
            "True\nTrue\nFalse\nNone\nNone\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute((LAB / name).read_text() + checks, directory),
                {"stdout": expected},
            )

    def test_set_display_is_stable_across_explicit_hash_seeds(self):
        with tempfile.TemporaryDirectory() as directory:
            for seed in ("1", "42", "123"):
                with self.subTest(seed=seed):
                    self.check_behavior(
                        execute(
                            (LAB / "sets.py").read_text(), directory, hash_seed=seed
                        ),
                        CASES["files"]["sets.py"],
                    )

    def test_additional_prose_boundaries_have_explicit_behavior_checks(self):
        cases = [
            (
                'items = ["Read"]\nitems[1] = "Review"\n',
                {"stdout": "", "error": "IndexError", "error_line": 2},
            ),
            (
                'data = {1: "integer", "1": "text"}\nprint(len(data))\nprint(data[1])\nprint(data["1"])\n',
                {"stdout": "2\ninteger\ntext\n"},
            ),
            (
                'data = {"none": None, "empty": "", "zero": 0, "flag": False}\nprint(data.get("none", "fallback"))\nprint("[" + data.get("empty", "fallback") + "]")\nprint(data.get("zero", "fallback"))\nprint(data.get("flag", "fallback"))\nprint("Read" in {"title": "Read"})\n',
                {"stdout": "None\n[]\n0\nFalse\nFalse\n"},
            ),
            (
                'print({"a": 1, "b": 2} == {"b": 2, "a": 1})\nprint(len({True, 1}))\nprint(len({True: "first", 1: "second"}))\n',
                {"stdout": "True\n1\n1\n"},
            ),
            (
                'data = {}\ndata[["title"]] = "Read"\n',
                {"stdout": "", "error": "TypeError", "error_line": 2},
            ),
            (
                'tags = set()\ntags.add(("task", []))\n',
                {"stdout": "", "error": "TypeError", "error_line": 2},
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for code, expected in cases:
                with self.subTest(code=code):
                    self.check_behavior(execute(code, directory), expected)

    def test_zip_contains_exactly_the_allowlisted_learning_material(self):
        names = json.loads(
            (ROOT / "examples/js2py/u02-containers-files.json").read_text()
        )
        self.assertEqual(set(names), {"README.md", *CASES["files"]})
        self.assertEqual(len(names), len(set(names)))
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u02-containers.zip"
        ) as archive:
            self.assertEqual(
                set(archive.namelist()), {f"u02-containers/{name}" for name in names}
            )
            for name in names:
                self.assertEqual(
                    archive.read(f"u02-containers/{name}"), (LAB / name).read_bytes()
                )


if __name__ == "__main__":
    unittest.main()
