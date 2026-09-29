"""L05 checks: actual paths, recovery boundaries, state preservation and transfer."""

import ast
import contextlib
import copy
import importlib.util
import io
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
LAB = ROOT / "examples/js2py/u05-exceptions"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
CASES = json.loads(
    (Path(__file__).parent / "fixtures/js2py-exceptions.json").read_text()
)
LESSONS = sorted(
    (ROOT / "content/docs/js2py").glob("module-05-quality-testing-typing*.mdx")
)
SPEC = importlib.util.spec_from_file_location(
    "exceptions_checker", ROOT / "scripts/check-js2py-content.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def source(name):
    return (LAB / name).read_text()


def execute(code, directory, optimized=False):
    path = Path(directory) / "learner.py"
    path.write_text(code, encoding="utf-8")
    return subprocess.run(
        [PYTHON, "-I"] + (["-O"] if optimized else []) + [str(path)],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=10,
    )


def definitions(name):
    """Keep exact definition spans; demonstration calls are tested independently."""
    code = source(name)
    lines = code.splitlines(keepends=True)
    return "\n\n".join(
        "".join(lines[node.lineno - 1 : node.end_lineno])
        for node in ast.parse(code).body
        if isinstance(node, ast.FunctionDef)
    )


def functions(name):
    namespace = {}
    exec(compile(definitions(name), name, "exec"), namespace)
    return namespace


def case_id(metadata):
    return next(part.split("=", 1)[1] for part in metadata if part.startswith("case="))


def fence_cases():
    return {
        case_id(metadata): code
        for _, code, metadata in CHECKER.python_blocks(LESSONS[0].read_text())
    }


class ExceptionChecks(unittest.TestCase):
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

    def test_all_shared_scripts_and_expected_failures(self):
        self.assertEqual(len(CASES["files"]), 22)
        self.assertEqual(sum("error" in item for item in CASES["files"].values()), 9)
        with tempfile.TemporaryDirectory() as directory:
            for name, expected in CASES["files"].items():
                with self.subTest(file=name):
                    self.check_behavior(execute(source(name), directory), expected)

    def test_translated_fences_and_javascript_have_execution_contracts(self):
        self.assertEqual(len(LESSONS), 3)
        with tempfile.TemporaryDirectory() as directory:
            for lesson in LESSONS:
                seen = []
                for _, code, metadata in CHECKER.python_blocks(lesson.read_text()):
                    name = case_id(metadata)
                    seen.append(name)
                    with self.subTest(lesson=lesson.name, case=name):
                        self.check_behavior(
                            execute(code, directory), CASES["fences"][name]
                        )
                self.assertEqual(set(seen), set(CASES["fences"]))
                self.assertEqual(len(seen), 5)
                js_seen = []
                for match in CHECKER.FENCE.finditer(lesson.read_text()):
                    metadata = match.group(1).split()
                    if not metadata or metadata[0] != "javascript":
                        continue
                    name = case_id(metadata)
                    js_seen.append(name)
                    result = subprocess.run(
                        ["node", "--input-type=module", "-e", match.group(2)],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    self.check_behavior(result, CASES["javascript"][name])
                self.assertEqual(js_seen, ["raise-comparison"])

    def test_prose_outputs_closed_answers_and_introduction_order(self):
        for lesson in LESSONS:
            text = lesson.read_text()
            for group in ("files", "fences", "javascript", "optimized"):
                for name, expected in CASES[group].items():
                    if expected["stdout"]:
                        self.assertIn(
                            "```text\n" + expected["stdout"] + "```", text, name
                        )
            self.assertEqual(re.findall(r"<details([^>]*)>", text), ["", "", ""])
            self.assertEqual(len(re.findall(r"^## \d+\.", text, re.M)), 15)
            self.assertIn("compare={true} canRun={false}", text)
            names = [
                "errors/traceback_chain.py",
                "errors/debug_observation.py",
                "debug_fixed.py",
                "debug_logic.py",
                "recover_value.py",
                "validate_minutes.py",
                "handler_order.py",
                "pitfalls/wide_try.py",
                "errors/narrow_try.py",
                "errors/reraise.py",
                "errors/chained_error.py",
                "finally_paths.py",
                "pitfalls/partial_mutation.py",
                "apply_estimate.py",
                "assert_invariant.py",
                "pitfalls/assert_validation.py",
                "solutions/fix_boundary.py",
                "solutions/import_report.py",
            ]
            positions = [text.index(f"getExceptionExample('{name}')") for name in names]
            self.assertEqual(positions, sorted(positions))
            self.assertIn("python -O errors/negative_minutes.py", text)
            self.assertIn("L06", text)

    def test_ast_boundary_excludes_later_imports_classes_annotations_and_io(self):
        allowed = (
            ast.Module,
            ast.FunctionDef,
            ast.arguments,
            ast.arg,
            ast.Return,
            ast.Assign,
            ast.Expr,
            ast.Name,
            ast.Load,
            ast.Store,
            ast.Constant,
            ast.Call,
            ast.keyword,
            ast.List,
            ast.Dict,
            ast.Tuple,
            ast.Subscript,
            ast.Attribute,
            ast.If,
            ast.For,
            ast.Compare,
            ast.IsNot,
            ast.Eq,
            ast.Lt,
            ast.GtE,
            ast.BinOp,
            ast.Add,
            ast.Sub,
            ast.USub,
            ast.UnaryOp,
            ast.Try,
            ast.ExceptHandler,
            ast.Raise,
            ast.Assert,
        )
        samples = [(name, source(name)) for name in CASES["files"]]
        for lesson in LESSONS:
            for _, code, metadata in CHECKER.python_blocks(lesson.read_text()):
                if "expected-error=SyntaxError" in metadata:
                    with self.assertRaises(SyntaxError):
                        ast.parse(code)
                else:
                    samples.append((case_id(metadata), code))
        for name, code in samples:
            tree = ast.parse(code)
            calls = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef)
            } | {
                "print",
                "int",
                "type",
                "str",
                "repr",
                "len",
                "enumerate",
                "ValueError",
                "TypeError",
            }
            for node in ast.walk(tree):
                self.assertIsInstance(node, allowed, name)
                if isinstance(node, ast.FunctionDef):
                    self.assertFalse(node.decorator_list)
                    self.assertIsNone(node.returns)
                    self.assertIsNone(node.args.vararg)
                    self.assertIsNone(node.args.kwarg)
                    self.assertFalse(node.args.posonlyargs)
                if isinstance(node, ast.arg):
                    self.assertIsNone(node.annotation)
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.assertIn(node.func.id, calls, name)
                    else:
                        self.assertIsInstance(node.func, ast.Attribute)
                        self.assertEqual(node.func.attr, "append")
                if isinstance(node, ast.ExceptHandler):
                    self.assertIsNotNone(node.type, name)
                    if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                        self.assertEqual(name, "handler_order.py")

    def test_traceback_frames_and_successful_or_empty_variants(self):
        code = source("errors/traceback_chain.py")
        with tempfile.TemporaryDirectory() as directory:
            result = execute(code, directory)
            frames = re.findall(r"line (\d+), in ([^\n]+)", result.stderr)
            self.assertEqual(
                frames,
                [
                    ("17", "<module>"),
                    ("12", "build_total"),
                    ("6", "task_minutes"),
                    ("2", "parse_minutes"),
                ],
            )
            self.assertEqual(result.stdout, "Starting report\n")
            self.check_behavior(
                execute(code.replace('"25m"', '"25"'), directory),
                {"stdout": "Starting report\n25\nDone\n"},
            )
            self.check_behavior(
                execute(
                    code.replace('[{"title": "Read", "minutes": "25m"}]', "[]"),
                    directory,
                ),
                {"stdout": "Starting report\n0\nDone\n"},
            )
            result = execute(
                code.replace('"minutes": "25m"', '"other": "25m"'), directory
            )
            self.assertIn("KeyError: 'minutes'", result.stderr)
            self.assertNotIn("Done", result.stdout)

    def test_silent_logic_bug_repaired_and_regressed(self):
        code = source("debug_logic.py")
        self.assertEqual(code.count("        return total\n"), 1)
        repaired = code.replace("        return total\n", "")
        with tempfile.TemporaryDirectory() as directory:
            for values, total in [([], 0), ([0], 0), ([10, 20], 30), ([5, 7, 9], 21)]:
                self.check_behavior(
                    execute(repaired.replace("[10, 20]", repr(values)), directory),
                    {"stdout": f"{total}\n0\n"},
                )

    def test_handler_resumption_and_temporary_exception_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            result = execute(source("recover_value.py"), directory)
            self.assertEqual(result.stdout.count("Next item"), 3)
            self.assertEqual(result.stdout.count("Converted:"), 2)
            result = execute(source("recover_value.py") + "print(error)\n", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NameError", result.stderr)
            self.assertEqual(
                result.stdout, CASES["files"]["recover_value.py"]["stdout"]
            )

    def test_validation_distinguishes_text_shape_and_domain(self):
        parse = functions("validate_minutes.py")["parse_minutes"]
        for raw, value in [
            ("20", 20),
            (" 20 ", 20),
            ("0", 0),
            ("-0", 0),
            ("+3", 3),
            ("1_0", 10),
            ("３", 3),
        ]:
            self.assertEqual(parse(raw), value)
        for raw in ("bad", "", " ", "2.5", "-1"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse(raw)
        for raw in (None, 20, 2.5, False, [], {}):
            with (
                self.subTest(raw=raw),
                self.assertRaisesRegex(TypeError, "minutes must be text"),
            ):
                parse(raw)

    def test_narrow_try_exposes_same_category_business_bug(self):
        with tempfile.TemporaryDirectory() as directory:
            code = source("errors/narrow_try.py")
            result = execute(code, directory)
            self.assertEqual(result.stdout, "")
            self.assertIn("ValueError: display rule is broken", result.stderr)
            self.check_behavior(
                execute(code.replace('raw = "25"', 'raw = "bad"'), directory),
                {"stdout": "Bad input\nAfter display\n"},
            )
            result = execute(code.replace('raw = "25"', "raw = None"), directory)
            self.assertEqual(result.stdout, "")
            self.assertIn("TypeError", result.stderr)

    def test_bare_raise_preserves_exception_identity_and_original_frame(self):
        ns = functions("errors/reraise.py")
        marker = ValueError("marker")

        def fail(raw):
            raise marker

        ns["int"] = fail
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            try:
                ns["read_minutes"]("bad")
            except ValueError as error:
                self.assertIs(error, marker)
            else:
                self.fail("Original exception swallowed")
        self.assertEqual(output.getvalue(), "Context: parsing Read\n")
        with tempfile.TemporaryDirectory() as directory:
            result = execute(source("errors/reraise.py"), directory)
            self.assertIn("line 3, in read_minutes", result.stderr)
            self.assertNotIn("line 6, in read_minutes", result.stderr)

    def test_cause_chain_retains_original_conversion_not_unrelated_errors(self):
        parse = functions("errors/chained_error.py")["parse_minutes"]
        with self.assertRaisesRegex(ValueError, "minutes must be an integer") as caught:
            parse("bad")
        self.assertIsInstance(caught.exception.__cause__, ValueError)
        self.assertIsNot(caught.exception, caught.exception.__cause__)
        self.assertIn("bad", str(caught.exception.__cause__))
        with self.assertRaisesRegex(
            ValueError, "minutes must be non-negative"
        ) as negative:
            parse("-5")
        self.assertIsNone(negative.exception.__cause__)
        with self.assertRaises(TypeError):
            parse(None)
        with tempfile.TemporaryDirectory() as directory:
            result = execute(source("errors/chained_error.py"), directory)
            self.assertEqual(
                result.stderr.count("Traceback (most recent call last):"), 2
            )
            self.assertIn("The above exception was the direct cause", result.stderr)
            self.assertIn("line 5, in parse_minutes", result.stderr)
            self.assertIn("line 7, in parse_minutes", result.stderr)

    def test_finally_return_unhandled_and_normal_paths(self):
        ns = functions("finally_paths.py")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(ns["convert"]("0"), 0)
            self.assertIsNone(ns["convert"]("bad"))
            with self.assertRaises(TypeError):
                ns["convert"](None)
        self.assertEqual(output.getvalue(), "else\nfinally\nexcept\nfinally\nfinally\n")
        broken = functions("pitfalls/finally_return.py")["convert"]
        for raw in ("25", "bad", None):
            self.assertEqual(broken(raw), 0)
        with tempfile.TemporaryDirectory() as directory:
            # Mechanism checks for the prose table, not additional learner prerequisites.
            code = 'def f():\n    try:\n        return 3\n    except ValueError:\n        print("except")\n    else:\n        print("else")\n    finally:\n        print("finally")\nprint(f())\n'
            self.check_behavior(execute(code, directory), {"stdout": "finally\n3\n"})
            for statement in ("break", "continue"):
                code = f'for value in [1]:\n    try:\n        {statement}\n    except ValueError:\n        print("except")\n    else:\n        print("else")\n    finally:\n        print("finally")\nprint("end")\n'
                self.check_behavior(
                    execute(code, directory), {"stdout": "finally\nend\n"}
                )

    def test_predicted_paths_with_valid_and_unexpected_inputs(self):
        code = fence_cases()["prediction"]
        with tempfile.TemporaryDirectory() as directory:
            self.check_behavior(
                execute(code.replace('"bad"', '"0"'), directory),
                {"stdout": "start\nafter conversion\nelse\nfinally\nend\n"},
            )
            result = execute(code.replace('"bad"', "None"), directory)
            self.assertEqual(result.stdout, "start\nfinally\n")
            self.assertIn("TypeError", result.stderr)

    def test_validation_before_mutation_and_explicit_nontransaction_boundary(self):
        replace = functions("apply_estimate.py")["replace_estimate"]
        for raw, kind in [("bad", ValueError), ("-5", ValueError), (None, TypeError)]:
            task = {"title": "Read", "minutes": 20, "changes": []}
            before = copy.deepcopy(task)
            changes = task["changes"]
            with self.assertRaises(kind):
                replace(task, raw)
            self.assertEqual(task, before)
            self.assertIs(task["changes"], changes)
        task = {"title": "Read", "minutes": 20, "changes": []}
        self.assertIsNone(replace(task, "0"))
        self.assertEqual(
            task, {"title": "Read", "minutes": 0, "changes": ["estimate changed"]}
        )
        malformed = {"minutes": 20}
        with self.assertRaises(KeyError):
            replace(malformed, "0")
        self.assertEqual(malformed["minutes"], 0)  # Deliberately documented limitation.

    def test_optimization_removes_assert_not_explicit_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, expected in CASES["optimized"].items():
                with self.subTest(file=name):
                    self.check_behavior(
                        execute(source(name), directory, optimized=True), expected
                    )
            broken = source("assert_invariant.py").replace(
                "total + minutes", "total - minutes"
            )
            result = execute(broken, directory)
            self.assertIn("AssertionError", result.stderr)
            self.assertEqual(result.stdout, "")
            self.check_behavior(
                execute(broken, directory, optimized=True), {"stdout": "-30\n"}
            )

    def test_guided_boundary_does_not_replace_missing_or_wrong_types(self):
        read = functions("solutions/fix_boundary.py")["read_minutes"]
        for raw, expected in [("20", 20), ("0", 0), ("bad", None), ("-5", -5)]:
            self.assertEqual(read({"minutes": raw}), expected)
        with self.assertRaises(KeyError):
            read({})
        for raw in (None, 20, 2.5, False, [], {}):
            with (
                self.subTest(raw=raw),
                self.assertRaisesRegex(TypeError, "minutes must be text"),
            ):
                read({"minutes": raw})

    def test_report_all_short_input_patterns_and_ordering(self):
        ns = functions("solutions/import_report.py")
        build = ns["build_report"]
        choices = [
            ("0", 0, None),
            ("20", 20, None),
            ("bad", None, "minutes must be an integer"),
            ("-1", None, "minutes must be non-negative"),
        ]
        count = 0
        for length in range(4):
            for pattern in itertools.product(choices, repeat=length):
                count += 1
                rows = [
                    {"title": f"Task {i}", "minutes": raw}
                    for i, (raw, _, _) in enumerate(pattern)
                ]
                before = copy.deepcopy(rows)
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    report = build(rows)
                self.assertEqual(out.getvalue(), "")
                expected_accepted = [
                    {"title": rows[i]["title"], "minutes": value}
                    for i, (_, value, reason) in enumerate(pattern)
                    if reason is None
                ]
                expected_rejected = [
                    {"row": i + 1, "title": rows[i]["title"], "reason": reason}
                    for i, (_, _, reason) in enumerate(pattern)
                    if reason is not None
                ]
                self.assertEqual(
                    report,
                    {
                        "accepted": expected_accepted,
                        "rejected": expected_rejected,
                        "total_minutes": sum(
                            item["minutes"] for item in expected_accepted
                        ),
                    },
                )
                self.assertEqual(rows, before)
        self.assertEqual(count, 85)
        for permutation in itertools.permutations(
            [("A", "2"), ("B", "bad"), ("C", "0"), ("D", "-5")]
        ):
            rows = [{"title": title, "minutes": raw} for title, raw in permutation]
            report = build(rows)
            self.assertEqual(
                [x["title"] for x in report["accepted"]],
                [title for title, raw in permutation if raw in ("2", "0")],
            )
            self.assertEqual(
                [x["row"] for x in report["rejected"]],
                [
                    i + 1
                    for i, (_, raw) in enumerate(permutation)
                    if raw in ("bad", "-5")
                ],
            )

    def test_unknown_errors_propagate_without_partial_success_or_source_mutation(self):
        build = functions("solutions/import_report.py")["build_report"]
        for bad, kind in [
            ({}, KeyError),
            ({"title": "Missing"}, KeyError),
            ({"minutes": "1"}, KeyError),
            ({"title": "Wrong", "minutes": None}, TypeError),
            ({"title": "Wrong", "minutes": 20}, TypeError),
        ]:
            for index in range(3):
                rows = [
                    {"title": "A", "minutes": "2"},
                    {"title": "B", "minutes": "bad"},
                ]
                rows.insert(index, copy.deepcopy(bad))
                before = copy.deepcopy(rows)
                with self.assertRaises(kind):
                    build(rows)
                self.assertEqual(rows, before)
        # A same-category failure in successful processing must remain outside the catch.
        code = definitions("solutions/import_report.py").replace(
            "            accepted.append(",
            '            raise ValueError("report bug")\n            accepted.append(',
        )
        ns = {}
        exec(code, ns)
        with self.assertRaisesRegex(ValueError, "report bug"):
            ns["build_report"]([{"title": "Read", "minutes": "20"}])
        # Unrelated parser defects and exit intentions are never handled as bad text.
        for kind in (RuntimeError, KeyError, TypeError, KeyboardInterrupt, SystemExit):
            ns = functions("solutions/import_report.py")
            marker = kind("unexpected")

            def fail(raw):
                raise marker

            ns["parse_minutes"] = fail
            with self.assertRaises(kind) as caught:
                ns["build_report"]([{"title": "Read", "minutes": "20"}])
            self.assertIs(caught.exception, marker)

    def test_reports_own_results_and_repeated_empty_calls_do_not_contaminate(self):
        build = functions("solutions/import_report.py")["build_report"]
        rows = [{"title": "Read", "minutes": "20"}, {"title": "Bad", "minutes": "x"}]
        before = copy.deepcopy(rows)
        first, second = build(rows), build(rows)
        self.assertIsNot(first, second)
        self.assertIsNot(first["accepted"][0], rows[0])
        self.assertIsNot(first["accepted"][0], second["accepted"][0])
        self.assertIsNot(first["rejected"][0], second["rejected"][0])
        first["accepted"][0]["minutes"] = 99
        first["accepted"].append({"title": "Extra", "minutes": 1})
        first["rejected"][0]["reason"] = "changed"
        self.assertEqual(second, build(rows))
        self.assertEqual(rows, before)
        empty = build([])
        another = build([])
        empty["accepted"].append({"title": "Extra", "minutes": 1})
        self.assertEqual(another, {"accepted": [], "rejected": [], "total_minutes": 0})
        self.assertIsNot(another["accepted"], another["rejected"])
        rows[0]["minutes"] = "21"
        self.assertEqual(build(rows)["total_minutes"], 21)

    def test_zip_contains_only_exact_allowlisted_files(self):
        names = json.loads(
            (ROOT / "examples/js2py/u05-exceptions-files.json").read_text()
        )
        self.assertEqual(set(names), set(CASES["files"]) | {"README.md"})
        self.assertEqual(len(names), len(set(names)))
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u05-exceptions.zip"
        ) as archive:
            self.assertEqual(
                set(archive.namelist()), {f"u05-exceptions/{name}" for name in names}
            )
            for name in names:
                self.assertEqual(
                    archive.read(f"u05-exceptions/{name}"), (LAB / name).read_bytes()
                )


if __name__ == "__main__":
    unittest.main()
