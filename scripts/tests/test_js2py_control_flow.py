"""L03 maintainer checks; tests are not prerequisites of the learner chapter."""

import ast
import importlib.util
import itertools
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
LAB = ROOT / "examples/js2py/u03-control-flow"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
CASES = json.loads(
    (Path(__file__).parent / "fixtures/js2py-control-flow.json").read_text()
)
LESSONS = sorted((ROOT / "content/docs/js2py").glob("module-03-oop-functional*.mdx"))
SPEC = importlib.util.spec_from_file_location(
    "control_flow_checker", ROOT / "scripts/check-js2py-content.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def execute(code, cwd):
    path = Path(cwd) / "learner.py"
    path.write_text(code, encoding="utf-8")
    return subprocess.run(
        [PYTHON, "-I", str(path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
    )


def case_id(metadata):
    return next(part.split("=", 1)[1] for part in metadata if part.startswith("case="))


def set_input(code, name, value):
    """Replace only a top-level literal input, leaving all processing unchanged."""
    assignments = [
        node
        for node in ast.parse(code).body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    assert len(assignments) == 1, name
    node = assignments[0]
    lines = code.splitlines(keepends=True)
    return "".join(
        lines[: node.lineno - 1] + [f"{name} = {value!r}\n"] + lines[node.end_lineno :]
    )


def source(name):
    return (LAB / name).read_text()


def task(title, minutes=0, done=False):
    return {"title": title, "minutes": minutes, "done": done}


class ControlFlowChecks(unittest.TestCase):
    def check_behavior(self, result, expected):
        self.assertEqual(result.stdout, expected["stdout"])
        if "error" in expected:
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                result.stderr.splitlines()[-1].startswith(expected["error"] + ":"),
                result.stderr,
            )
            self.assertIn(f"line {expected['error_line']}", result.stderr)
        else:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")

    def test_shared_files_and_expected_errors_in_fresh_processes(self):
        self.assertEqual(len(CASES["files"]), 20)
        with tempfile.TemporaryDirectory() as directory:
            for name, expected in CASES["files"].items():
                with self.subTest(file=name):
                    self.check_behavior(execute(source(name), directory), expected)

    def test_each_translated_python_fence_has_a_behavior_contract(self):
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

    def test_javascript_truth_comparison_in_node(self):
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

    def test_outputs_closed_answers_and_teaching_order(self):
        for lesson in LESSONS:
            text = lesson.read_text()
            for group in ("files", "fences", "javascript"):
                for name, expected in CASES[group].items():
                    if expected["stdout"]:
                        with self.subTest(lesson=lesson.name, case=name):
                            self.assertIn(
                                "```text\n" + expected["stdout"] + "```", text
                            )
            self.assertEqual(re.findall(r"<details([^>]*)>", text), ["", "", ""])
            self.assertNotIn("canRun={true}", text)
            positions = [
                text.index(f"getControlFlowExample('{name}')")
                for name in (
                    "branches.py",
                    "truthiness.py",
                    "for_tasks.py",
                    "ranges.py",
                    "unpacking.py",
                    "numbered_tasks.py",
                    "dict_iteration.py",
                    "while_budget.py",
                    "loop_controls.py",
                    "safe_filter.py",
                    "comprehensions.py",
                    "task_summary.py",
                    "solutions/study_queue.py",
                )
            ]
            self.assertEqual(positions, sorted(positions))

    def test_scope_guard_allows_only_prior_or_explicitly_taught_syntax(self):
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
            ast.If,
            ast.For,
            ast.While,
            ast.Break,
            ast.Continue,
            ast.BoolOp,
            ast.And,
            ast.Or,
            ast.Not,
            ast.keyword,
            ast.ListComp,
            ast.comprehension,
        )
        samples = [source(name) for name in CASES["files"]]
        for lesson in LESSONS:
            for _, code, metadata in CHECKER.python_blocks(lesson.read_text()):
                if "expected-error=SyntaxError" in metadata:
                    with self.assertRaises(IndentationError):
                        ast.parse(code)
                else:
                    samples.append(code)
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
                                "bool",
                                "range",
                                "list",
                                "enumerate",
                            },
                        )
                    else:
                        self.assertIsInstance(node.func, ast.Attribute)
                        self.assertIn(
                            node.func.attr,
                            {
                                "get",
                                "append",
                                "pop",
                                "copy",
                                "add",
                                "discard",
                                "strip",
                                "lower",
                                "upper",
                                "replace",
                                "items",
                            },
                        )
                if isinstance(node, ast.keyword):
                    self.assertEqual(node.arg, "start")
                if isinstance(node, ast.ListComp):
                    self.assertEqual(len(node.generators), 1)
                    self.assertEqual(node.generators[0].is_async, 0)
                if isinstance(node, (ast.For, ast.While)):
                    self.assertFalse(node.orelse, "Loop else has not been taught")

    def test_branch_endpoints_and_zero_preserving_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            for minutes, label in (
                (-1, "Invalid estimate"),
                (0, "No time required"),
                (1, "Short session"),
                (25, "Short session"),
                (26, "Long session"),
            ):
                self.check_behavior(
                    execute(
                        set_input(source("branches.py"), "minutes", minutes), directory
                    ),
                    {"stdout": label + "\nChecked\n"},
                )
            for minutes, expected in ((None, "25\n25\n"), (5, "5\n5\n")):
                self.check_behavior(
                    execute(
                        set_input(source("logical.py"), "minutes", minutes), directory
                    ),
                    {"stdout": "False\nUntitled\nReady\nTrue\n" + expected},
                )

    def test_for_and_summary_zero_one_many_and_guarded_average(self):
        variants = [
            (
                [],
                "Tasks: 0; total: 0 minutes\nPending: 0\n",
                "Tasks: 0\nDone: 0; pending: 0\nRemaining: 0 minutes\nPending average: n/a\n",
            ),
            (
                [task("Zero")],
                "Tasks: 1; total: 0 minutes\nPending: 1\n",
                "Tasks: 1\nDone: 0; pending: 1\nRemaining: 0 minutes\nPending average: 0.0 minutes\n1. Zero\n",
            ),
            (
                [task("Done", 9, True), task("Also done", 0, True)],
                "Tasks: 2; total: 9 minutes\nPending: 0\n",
                "Tasks: 2\nDone: 2; pending: 0\nRemaining: 0 minutes\nPending average: n/a\n",
            ),
            (
                [
                    task("Read branches", 20, True),
                    task("Practice loops", 35),
                    task("Check boundaries"),
                    task("Extra", 5),
                ],
                "Tasks: 4; total: 60 minutes\nPending: 3\n",
                "Tasks: 4\nDone: 1; pending: 3\nRemaining: 40 minutes\nPending average: 13.3 minutes\n1. Practice loops\n2. Check boundaries\n3. Extra\n",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for tasks, for_output, summary_output in variants:
                for name, output in (
                    ("for_tasks.py", for_output),
                    ("task_summary.py", summary_output),
                ):
                    code = set_input(source(name), "tasks", tasks)
                    self.check_behavior(execute(code, directory), {"stdout": output})

    def test_while_terminates_with_explicit_progress_at_boundaries(self):
        cases = {
            0: "Blocks: 0; remaining: 0\n",
            1: "Block: 1 minutes\nBlocks: 1; remaining: 0\n",
            20: "Block: 20 minutes\nBlocks: 1; remaining: 0\n",
            21: "Block: 20 minutes\nBlock: 1 minutes\nBlocks: 2; remaining: 0\n",
            -1: "Blocks: 0; remaining: -1\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            for remaining, output in cases.items():
                self.check_behavior(
                    execute(
                        set_input(source("while_budget.py"), "remaining", remaining),
                        directory,
                    ),
                    {"stdout": output},
                )

    def test_continue_break_and_first_match_not_last_match(self):
        cases = [
            ([], 20, "No match\n"),
            ([task("Done", 0, True)], 20, "Check: Done\nNo match\n"),
            ([task("Long", 21)], 20, "Check: Long\nNo match\n"),
            (
                [task("Zero"), task("Ignored", 20)],
                0,
                "Check: Zero\nFirst match: Zero\n",
            ),
            (
                [task("Exact", 20), task("Ignored")],
                20,
                "Check: Exact\nFirst match: Exact\n",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for tasks, budget, output in cases:
                code = set_input(
                    set_input(source("loop_controls.py"), "tasks", tasks),
                    "budget",
                    budget,
                )
                self.check_behavior(execute(code, directory), {"stdout": output})

    def test_filter_and_comprehension_all_boolean_patterns_and_reference_boundaries(
        self,
    ):
        filter_code = source("safe_filter.py")
        compact_code = source("comprehensions.py")
        with tempfile.TemporaryDirectory() as directory:
            for size in range(5):
                for flags in itertools.product((False, True), repeat=size):
                    tasks = [
                        {"title": f"T{i}", "done": done} for i, done in enumerate(flags)
                    ]
                    expected = [item for item in tasks if not item["done"]]
                    kept = [i for i, done in enumerate(flags) if not done]
                    code = set_input(filter_code, "tasks", tasks)
                    code += f"print(tasks == {tasks!r})\n"
                    code += (
                        "print([pending_tasks[i] is tasks[j] for i, j in enumerate("
                        + repr(kept)
                        + ")])\n"
                    )
                    self.check_behavior(
                        execute(code, directory),
                        {
                            "stdout": f"{expected!r}\n{len(tasks)}\nFalse\nTrue\n{[True] * len(kept)!r}\n"
                        },
                    )
                    code = set_input(compact_code, "tasks", tasks)
                    titles = [item["title"] for item in expected]
                    self.check_behavior(
                        execute(code, directory),
                        {"stdout": f"{titles!r}\n{titles!r}\nTrue\nFalse\n"},
                    )
            code = (
                source("safe_filter.py")
                + 'pending_tasks[0]["title"] = "Changed"\nprint(tasks[2]["title"])\n'
            )
            self.check_behavior(
                execute(code, directory),
                {"stdout": CASES["files"]["safe_filter.py"]["stdout"] + "Changed\n"},
            )

    def test_exercise_prediction_repair_and_syntax_recovery(self):
        fences = {
            case_id(metadata): code
            for _, code, metadata in CHECKER.python_blocks(LESSONS[0].read_text())
        }
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute(
                    fences["missing_indent"].replace(
                        'print("Inside")', '    print("Inside")'
                    ),
                    directory,
                ),
                {"stdout": "Inside\nAfter\n"},
            )
            self.check_behavior(
                execute(
                    fences["exercise_predict"].replace("break", "continue"), directory
                ),
                {"stdout": "[10, 5]\n5\n"},
            )
            self.check_behavior(
                execute(
                    set_input(fences["exercise_predict"], "minutes_list", []), directory
                ),
                {"stdout": "[]\n", "error": "NameError", "error_line": 10},
            )
            self.check_behavior(
                execute(
                    set_input(fences["exercise_reset"], "minutes_list", []), directory
                ),
                {"stdout": "", "error": "NameError", "error_line": 5},
            )
            for values, expected in (([20, 35, 5], 60), ([], 0), ([0], 0)):
                self.check_behavior(
                    execute(
                        set_input(
                            source("solutions/fix_total.py"), "minutes_list", values
                        ),
                        directory,
                    ),
                    {"stdout": f"{expected}\n"},
                )

    def test_independent_queue_original_and_all_documented_variations(self):
        original = [
            task("Read branches", 20),
            task("Review loops", 30, True),
            task("Try empty input"),
            task("Estimate later", None),
            {"title": "Missing estimate", "done": False},
            task("Repair estimate", -5),
        ]
        completed = [dict(item, done=True) for item in original]
        over = [dict(item) for item in original]
        over[0]["minutes"] = 21
        estimated = [dict(item) for item in original]
        estimated[4]["minutes"] = 5
        cases = [
            (original, 20, 5, 20, 2, 1, ["Read branches", "Try empty input"]),
            ([], 20, 0, 0, 0, 0, []),
            (completed, 20, 0, 0, 0, 0, []),
            (original, 0, 5, 20, 2, 1, ["Try empty input"]),
            (over, 20, 5, 21, 2, 1, ["Try empty input"]),
            (
                estimated,
                20,
                5,
                25,
                1,
                1,
                ["Read branches", "Try empty input", "Missing estimate"],
            ),
            (
                original + [task("Long", 60)],
                20,
                6,
                80,
                2,
                1,
                ["Read branches", "Try empty input"],
            ),
            ([task("Unknown", None)], 20, 1, 0, 1, 0, []),
            ([task("Negative", -1)], 20, 1, 0, 0, 1, []),
            ([task("Zero")], 0, 1, 0, 0, 0, ["Zero"]),
            ([task("A", 20), task("B", 20)], 20, 2, 40, 0, 0, ["A", "B"]),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for tasks, budget, pending, known, unknown, invalid, titles in cases:
                expected = (
                    f"Tasks: {len(tasks)}; pending: {pending}\n"
                    f"Known pending time: {known} minutes\n"
                    f"Unknown: {unknown}; invalid: {invalid}\n"
                    f"Ready within {budget} minutes each: {len(titles)}\n"
                    + "".join(f"{i}. {title}\n" for i, title in enumerate(titles, 1))
                    + "True\n"
                )
                code = set_input(
                    set_input(source("solutions/study_queue.py"), "tasks", tasks),
                    "budget",
                    budget,
                )
                code += f"print(tasks == {tasks!r})\n"
                with self.subTest(tasks=tasks, budget=budget):
                    self.check_behavior(execute(code, directory), {"stdout": expected})

    def test_numbered_titles_empty_single_and_many_without_unsafe_indexing(self):
        with tempfile.TemporaryDirectory() as directory:
            for titles, expected in (
                ([], ""),
                (["One"], "1. One\nOne\n"),
                (["One", "Two", "Three"], "1. One\n2. Two\n3. Three\nOne\n"),
            ):
                self.check_behavior(
                    execute(
                        set_input(source("numbered_tasks.py"), "titles", titles),
                        directory,
                    ),
                    {"stdout": expected},
                )

    def test_additional_language_claims_not_just_main_examples(self):
        cases = [
            (
                'print(bool(()))\nprint(bool("0"))\nprint(bool(0.0))\n',
                {"stdout": "False\nTrue\nFalse\n"},
            ),
            (
                'titles = []\nprint(titles[0] == "Read" and titles)\n',
                {"stdout": "", "error": "IndexError", "error_line": 2},
            ),
            (
                "numbers = range(3)\nprint(list(numbers))\nprint(list(numbers))\nprint(list(range(1, 1)))\n",
                {"stdout": "[0, 1, 2]\n[0, 1, 2]\n[]\n"},
            ),
            (
                'numbered = enumerate(["Read"], start=1)\nprint(list(numbered))\nprint(list(numbered))\n',
                {"stdout": "[(1, 'Read')]\n[]\n"},
            ),
            (
                "number, title = (1,)\n",
                {"stdout": "", "error": "ValueError", "error_line": 1},
            ),
            (
                'for key, value in {"ab": 20}:\n    print(key, value)\n',
                {"stdout": "a b\n"},
            ),
            (
                "for number, title in enumerate([], start=1):\n    print(number, title)\nprint(start)\n",
                {"stdout": "", "error": "NameError", "error_line": 3},
            ),
            (
                'label = "Before"\nif True:\n    label = "After"\nprint(label)\n',
                {"stdout": "After\n"},
            ),
            (
                'data = {"a": 1}\nentries = data.items()\ndata["b"] = 2\nprint(list(entries))\n',
                {"stdout": "[('a', 1), ('b', 2)]\n"},
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for code, expected in cases:
                self.check_behavior(execute(code, directory), expected)

    def test_zip_contains_exactly_the_allowlisted_sources(self):
        names = json.loads(
            (ROOT / "examples/js2py/u03-control-flow-files.json").read_text()
        )
        self.assertEqual(set(names), {"README.md", *CASES["files"]})
        self.assertEqual(len(names), len(set(names)))
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u03-control-flow.zip"
        ) as archive:
            self.assertEqual(
                set(archive.namelist()), {f"u03-control-flow/{name}" for name in names}
            )
            for name in names:
                self.assertEqual(
                    archive.read(f"u03-control-flow/{name}"), (LAB / name).read_bytes()
                )


if __name__ == "__main__":
    unittest.main()
