"""L04 maintainer checks: execution contracts, bounded syntax and independent transfer."""

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
LAB = ROOT / "examples/js2py/u04-functions"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
CASES = json.loads(
    (Path(__file__).parent / "fixtures/js2py-functions.json").read_text()
)
LESSONS = sorted((ROOT / "content/docs/js2py").glob("module-04-async-programming*.mdx"))
SPEC = importlib.util.spec_from_file_location(
    "functions_checker", ROOT / "scripts/check-js2py-content.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def execute(code, cwd):
    path = Path(cwd) / "learner.py"
    path.write_text(code, encoding="utf-8")
    return subprocess.run(
        [PYTHON, "-I", str(path)], cwd=cwd, capture_output=True, text=True, timeout=10
    )


def source(name):
    return (LAB / name).read_text()


def definitions(name):
    """Execute exact function source spans without the file's demonstration calls."""
    code = source(name)
    lines = code.splitlines(keepends=True)
    return (
        "\n\n".join(
            "".join(lines[node.lineno - 1 : node.end_lineno])
            for node in ast.parse(code).body
            if isinstance(node, ast.FunctionDef)
        )
        + "\n\n"
    )


def case_id(metadata):
    return next(part.split("=", 1)[1] for part in metadata if part.startswith("case="))


def fence_cases():
    return {
        case_id(metadata): code
        for _, code, metadata in CHECKER.python_blocks(LESSONS[0].read_text())
    }


class FunctionChecks(unittest.TestCase):
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

    def test_shared_files_and_expected_failures_in_fresh_processes(self):
        self.assertEqual(len(CASES["files"]), 23)
        self.assertEqual(sum("error" in case for case in CASES["files"].values()), 8)
        with tempfile.TemporaryDirectory() as directory:
            for name, expected in CASES["files"].items():
                with self.subTest(file=name):
                    self.check_behavior(execute(source(name), directory), expected)

    def test_every_translated_python_fence_has_a_behavior_contract(self):
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

    def test_javascript_default_comparison_in_node(self):
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

    def test_prose_outputs_closed_answers_and_first_use_order(self):
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
            names = [
                "definition_and_call.py",
                "return_paths.py",
                "arguments.py",
                "keyword_only.py",
                "argument_binding.py",
                "default_values.py",
                "pitfalls/shared_default.py",
                "fresh_defaults.py",
                "local_scope.py",
                "function_values.py",
                "closure_factory.py",
                "closure_binding.py",
                "task_rules.py",
                "solutions/study_rules.py",
            ]
            positions = [text.index(f"getFunctionExample('{name}')") for name in names]
            self.assertEqual(positions, sorted(positions))

    def test_ast_scope_requires_no_later_imports_exceptions_annotations_or_classes(
        self,
    ):
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
            ast.FunctionDef,
            ast.arguments,
            ast.arg,
            ast.Return,
        )
        samples = [source(name) for name in CASES["files"]]
        for lesson in LESSONS:
            for _, code, metadata in CHECKER.python_blocks(lesson.read_text()):
                if "expected-error=SyntaxError" in metadata:
                    with self.assertRaises(SyntaxError):
                        ast.parse(code)
                else:
                    samples.append(code)
        for code in samples:
            tree = ast.parse(code)
            names = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            }
            names |= {
                "rule",
                "small_rule",
                "large_rule",
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
            }
            for node in ast.walk(tree):
                self.assertIsInstance(node, allowed, code)
                if isinstance(node, ast.FunctionDef):
                    self.assertEqual(node.decorator_list, [])
                    self.assertIsNone(node.returns)
                    self.assertIsNone(node.type_comment)
                    self.assertEqual(node.args.posonlyargs, [])
                    self.assertIsNone(node.args.vararg)
                    self.assertIsNone(node.args.kwarg)
                if isinstance(node, ast.arg):
                    self.assertIsNone(node.annotation)
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.assertIn(node.func.id, names)
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
                    self.assertIsNotNone(node.arg, "Call ** expansion is not taught")
                if isinstance(node, ast.ListComp):
                    self.assertEqual(len(node.generators), 1)
                    self.assertEqual(node.generators[0].is_async, 0)

    def test_binding_errors_have_specific_working_repairs(self):
        repairs = [
            (
                "errors/before_definition.py",
                lambda code: (
                    definitions("errors/before_definition.py")
                    + "print(add_buffer(20))\n"
                ),
                "25\n",
            ),
            (
                "errors/missing_argument.py",
                lambda code: code.replace("estimate(20)", "estimate(20, 2)"),
                "Body ran\n40\n",
            ),
            (
                "errors/duplicate_argument.py",
                lambda code: code.replace(
                    "estimate(20, minutes=30)", "estimate(minutes=30)"
                ),
                "Body ran\n30\n",
            ),
            (
                "errors/unknown_keyword.py",
                lambda code: code.replace("repeat=2", "repeats=2"),
                "Body ran\n40\n",
            ),
            (
                "errors/positional_option.py",
                lambda code: code.replace(
                    'make_label("Read", True)', 'make_label("Read", done=True)'
                ),
                "Body ran\n[done] Read\n",
            ),
            (
                "errors/printed_result.py",
                lambda code: code.replace("print(minutes + 5)", "return minutes + 5"),
                "35\n",
            ),
            (
                "errors/not_callable.py",
                lambda code: code.replace(
                    "rule = is_pending(task)", "rule = is_pending"
                ),
                "True\n",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for name, repair, expected in repairs:
                self.check_behavior(
                    execute(repair(source(name)), directory), {"stdout": expected}
                )
            code = fence_cases()["positional_after_keyword"]
            for call in ("estimate(20, 2)", "estimate(minutes=20, repeats=2)"):
                self.check_behavior(
                    execute(code.replace("estimate(minutes=20, 2)", call), directory),
                    {"stdout": "40\n"},
                )
            code = 'def label(title, *, done):\n    print("Body ran")\n    return title\n\nlabel("Read")\n'
            self.check_behavior(
                execute(code, directory),
                {"stdout": "", "error": "TypeError", "error_line": 5},
            )

    def test_return_paths_are_values_not_output_and_tuple_is_one_object(self):
        calls = """print(status_label({"done": True}))
print(status_label({"done": False}))
print(status_label({"done": False, "minutes": 0}))
value = maybe_announce("Practice")
print(value)
"""
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute(definitions("return_paths.py") + calls, directory),
                {"stdout": "done\nunknown\npending\nReady: Practice\nNone\n"},
            )
            code = (
                fence_cases()["tuple_result"]
                + "result = split_minutes(0)\nprint(type(result))\nprint(result)\nprint(split_minutes(60))\n"
            )
            self.check_behavior(
                execute(code, directory),
                {"stdout": "2\n15\n<class 'tuple'>\n(0, 0)\n(1, 0)\n"},
            )

    def test_default_timing_aliasing_and_explicit_input_copying(self):
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute(
                    source("default_values.py").replace(
                        "default_minutes = 35", "default_minutes = 50"
                    ),
                    directory,
                ),
                {"stdout": "20\n0\nNone\n50\n"},
            )
            code = (
                source("pitfalls/shared_default.py")
                + 'third = add_tag("review")\nprint(first)\nprint(third is first)\n'
            )
            self.check_behavior(
                execute(code, directory),
                {
                    "stdout": CASES["files"]["pitfalls/shared_default.py"]["stdout"]
                    + "['python', 'functions', 'review']\nTrue\n"
                },
            )
            code = (
                definitions("fresh_defaults.py")
                + """a = make_task("A")
b = make_task("B", None)
a["tags"].append("changed")
print(b["tags"])
print(a["tags"] is b["tags"])
empty = []
c = make_task("C", empty)
c["tags"].append("later")
print(empty)
print(c["tags"] is empty)
print(make_task("D")["tags"])
"""
            )
            self.check_behavior(
                execute(code, directory), {"stdout": "[]\nFalse\n[]\nFalse\n[]\n"}
            )

    def test_argument_rebinding_mutation_and_scope_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            code = (
                definitions("argument_binding.py")
                + """item = {"title": "Before", "tags": []}
other = replace_local(item)
print(item)
print(other is item)
print(add_topic(item, "one"))
print(item["tags"])
"""
            )
            self.check_behavior(
                execute(code, directory),
                {"stdout": "{'title': 'Before', 'tags': []}\nFalse\nNone\n['one']\n"},
            )
            code = (
                source("local_scope.py")
                + 'print(format_label("Practice"))\nprint(label)\nlimit = 0\nprint(current_limit())\n'
            )
            self.check_behavior(
                execute(code, directory),
                {
                    "stdout": CASES["files"]["local_scope.py"]["stdout"]
                    + "local: Practice\nmodule\n0\n"
                },
            )
            self.check_behavior(
                execute(
                    fence_cases()["scope_repair"].replace("budget = 20", "budget = 0"),
                    directory,
                ),
                {"stdout": "0\n5\n"},
            )

    def test_function_value_selection_call_counts_order_and_sharing(self):
        with tempfile.TemporaryDirectory() as directory:
            for size in range(4):
                for flags in itertools.product((False, True), repeat=size):
                    tasks = [
                        {"title": f"T{i}", "done": flag} for i, flag in enumerate(flags)
                    ]
                    expected = [item["title"] for item in tasks if not item["done"]]
                    kept = [i for i, flag in enumerate(flags) if not flag]
                    code = (
                        definitions("function_values.py")
                        + f"tasks = {tasks!r}\n"
                        + """seen = []
def recording_rule(task):
    seen.append(task["title"])
    return is_pending(task)
selected = select_tasks(tasks, recording_rule)
print([task["title"] for task in selected])
print(seen)
print(selected is tasks)
"""
                        + f"print(tasks == {tasks!r})\nprint([selected[i] is tasks[j] for i, j in enumerate({kept!r})])\n"
                    )
                    output = f"{expected!r}\n{[t['title'] for t in tasks]!r}\nFalse\nTrue\n{[True] * len(kept)!r}\n"
                    self.check_behavior(execute(code, directory), {"stdout": output})
            code = source("function_values.py").replace(
                'tasks = [\n    {"title": "Read", "done": True},\n    {"title": "Practice", "done": False},\n]',
                "tasks = []",
            )
            self.assertNotEqual(code, source("function_values.py"))
            self.check_behavior(
                execute(code, directory), {"stdout": "True\nTrue\n[]\nFalse\n"}
            )

    def test_closure_creation_lookup_and_independent_factory_calls(self):
        code = (
            definitions("closure_factory.py")
            + """budget = 20
small = make_budget_rule(budget)
budget = 40
large = make_budget_rule(budget)
for minutes in [-1, 0, 20, 21, 40, 41]:
    print(small(minutes), large(minutes))
print(small(25), large(25), small(25))
"""
        )
        expected = "False False\nTrue True\nTrue True\nFalse True\nFalse True\nFalse False\nFalse True False\n"
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(execute(code, directory), {"stdout": expected})
            self.check_behavior(
                execute(
                    source("closure_binding.py").replace("limit = 30", "limit = 15"),
                    directory,
                ),
                {"stdout": "False\n"},
            )
            # No stdout during factory creation; returned predicates run later.
            self.check_behavior(
                execute(
                    definitions("closure_factory.py") + "rule = make_budget_rule(20)\n",
                    directory,
                ),
                {"stdout": ""},
            )

    def test_classifier_and_report_empty_boundaries_and_repeated_call_isolation(self):
        tasks = [
            {"title": "Read", "minutes": 20, "done": False},
            {"title": "Finished", "minutes": 30, "done": True},
            {"title": "Zero", "minutes": 0, "done": False},
            {"title": "Unknown", "done": False},
            {"title": "Repair", "minutes": -5, "done": False},
        ]
        cases = [
            ([], 20, [0, 0, 0, 0, []]),
            (tasks, 20, [4, 20, 1, 1, ["Read", "Zero"]]),
            (tasks, 0, [4, 20, 1, 1, ["Zero"]]),
            ([dict(task, done=True) for task in tasks], 20, [0, 0, 0, 0, []]),
            (
                tasks + [{"title": "Long", "minutes": 60, "done": False}],
                20,
                [5, 80, 1, 1, ["Read", "Zero"]],
            ),
            (
                [{"title": "Unknown", "minutes": None, "done": False}],
                20,
                [1, 0, 1, 0, []],
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for data, budget, expected in cases:
                code = (
                    definitions("task_rules.py")
                    + f"tasks = {data!r}\nr = build_report(tasks, budget={budget})\n"
                    + 'print([r["pending"], r["known_minutes"], r["unknown"], r["invalid"], r["ready_titles"]])\n'
                    + f"print(tasks == {data!r})\n"
                )
                self.check_behavior(
                    execute(code, directory), {"stdout": repr(expected) + "\nTrue\n"}
                )
            code = (
                definitions("task_rules.py")
                + """for minutes in [None, -1, 0, 20]:
    print(classify_minutes(minutes))
first = build_report([])
second = build_report([])
first["ready_titles"].append("changed")
print(first is second)
print(second["ready_titles"])
print(first["ready_titles"] is second["ready_titles"])
"""
            )
            self.check_behavior(
                execute(code, directory),
                {"stdout": "unknown\ninvalid\nknown\nknown\nFalse\n[]\nFalse\n"},
            )

    def test_independent_constructor_defaults_and_copy_boundaries(self):
        code = (
            definitions("solutions/study_rules.py")
            + """supplied = ["python"]
first = create_task("First", tags=supplied)
second = create_task("Second", 0, supplied)
first["tags"].append("review")
print(supplied)
print(second["tags"])
print(first is second)
print(first["tags"] is supplied)
print(first["minutes"])
print(second["minutes"])
print(first["done"])
third = create_task("Third")
fourth = create_task("Fourth", tags=None)
third["tags"].append("later")
print(fourth["tags"])
print(third["tags"] is fourth["tags"])
empty = []
fifth = create_task("Fifth", tags=empty)
fifth["tags"].append("new")
print(empty)
print(fifth["tags"] is empty)
"""
        )
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute(code, directory),
                {
                    "stdout": "['python']\n['python']\nFalse\nFalse\nNone\n0\nFalse\n[]\nFalse\n[]\nFalse\n"
                },
            )

    def test_independent_predicates_selection_and_closure_acceptance(self):
        tasks = [
            {"title": "Done", "minutes": 0, "done": True},
            {"title": "None", "minutes": None, "done": False},
            {"title": "Missing", "done": False},
            {"title": "Negative", "minutes": -1, "done": False},
            *[
                {"title": str(n), "minutes": n, "done": False}
                for n in [0, 20, 21, 35, 40, 41]
            ],
        ]
        code = (
            definitions("solutions/study_rules.py")
            + f"tasks = {tasks!r}\n"
            + """small = make_budget_rule(20)
large = make_budget_rule(40)
for rule in [small, large, small, large]:
    selected = select_tasks(tasks, rule)
    print([task["title"] for task in selected])
print([is_ready(task) for task in tasks])
print([task["title"] for task in select_tasks(tasks, make_budget_rule(0))])
print(select_tasks([], small))
"""
            + f"print(tasks == {tasks!r})\n"
            + """seen = []
def tracked(task):
    seen.append(task)
    return True
print(select_tasks([], tracked))
print(seen)
selected = select_tasks(tasks, small)
selected[0]["title"] = "Changed"
print(tasks[4]["title"])
print(selected is tasks)
for task in tasks:
    task["done"] = True
print(select_tasks(tasks, small))
print(select_tasks(tasks, large))
"""
        )
        expected = (
            "['0', '20']\n['0', '20', '21', '35', '40']\n" * 2
            + "[False, False, False, False, True, True, False, False, False, False]\n"
            + "['0']\n[]\nTrue\n[]\n[]\nChanged\nFalse\n[]\n[]\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(execute(code, directory), {"stdout": expected})
            main = source("solutions/study_rules.py")
            changed = main.replace("small_budget = 20", "small_budget = 0")
            self.check_behavior(
                execute(changed, directory),
                {
                    "stdout": CASES["files"]["solutions/study_rules.py"][
                        "stdout"
                    ].replace("Within 20: ['Read', 'Zero']", "Within 0: ['Zero']")
                },
            )
            changed = main.replace(
                'create_task("Read", 20, source_tags)',
                'create_task("Read", 21, source_tags)',
            )
            self.check_behavior(
                execute(changed, directory),
                {
                    "stdout": CASES["files"]["solutions/study_rules.py"][
                        "stdout"
                    ].replace("Within 20: ['Read', 'Zero']", "Within 20: ['Zero']")
                },
            )
            changed = main.replace(
                "tasks = [first, second, zero, unknown, finished, invalid]",
                "tasks = []",
            )
            expected = (
                CASES["files"]["solutions/study_rules.py"]["stdout"]
                .replace("Within 20: ['Read', 'Zero']", "Within 20: []")
                .replace("Within 40: ['Read', 'Practice', 'Zero']", "Within 40: []")
                .replace("Source tasks: 6", "Source tasks: 0")
            )
            self.check_behavior(execute(changed, directory), {"stdout": expected})

    def test_exercise_alias_and_return_variations(self):
        code = fence_cases()["exercise_alias"]
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute(code.replace('source = ["Read"]', "source = []"), directory),
                {"stdout": "['Review']\n['Local']\nFalse\n"},
            )
            self.check_behavior(
                execute(code.replace('    titles = ["Local"]\n', ""), directory),
                {"stdout": "['Read', 'Review']\n['Read', 'Review']\nTrue\n"},
            )
            calls = "print(with_buffer(20, extra=10))\nprint(with_buffer(0))\nprint(with_buffer(0, extra=0))\nprint(with_buffer(20, extra=10))\n"
            self.check_behavior(
                execute(definitions("solutions/fix_return.py") + calls, directory),
                {"stdout": "30\n5\n0\n30\n"},
            )

    def test_zip_is_exactly_the_allowlisted_sources(self):
        names = json.loads(
            (ROOT / "examples/js2py/u04-functions-files.json").read_text()
        )
        self.assertEqual(set(names), {"README.md", *CASES["files"]})
        self.assertEqual(len(names), len(set(names)))
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u04-functions.zip"
        ) as archive:
            self.assertEqual(
                set(archive.namelist()), {f"u04-functions/{name}" for name in names}
            )
            for name in names:
                self.assertEqual(
                    archive.read(f"u04-functions/{name}"), (LAB / name).read_bytes()
                )


if __name__ == "__main__":
    unittest.main()
