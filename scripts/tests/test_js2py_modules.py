"""L06: test real multi-file entries, imports, contexts and independent transfer."""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "examples/js2py/u06-modules"
PYTHON = os.environ.get("JS2PY_PYTHON", sys.executable)
NAMES = json.loads((ROOT / "examples/js2py/u06-modules-files.json").read_text())
CASES = json.loads((Path(__file__).parent / "fixtures/js2py-modules.json").read_text())[
    "cases"
]
LESSONS = sorted((ROOT / "content/docs/js2py").glob("module-06-web-development*.mdx"))


def controlled_environment():
    # Do not inherit PYTHONPATH, safe-path or no-bytecode settings. No -I:
    # these experiments intentionally exercise ordinary local search behavior.
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env.pop("VIRTUAL_ENV", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def execute(lab, args, cwd=".", prefix=None):
    return subprocess.run(
        (prefix or [PYTHON]) + args,
        cwd=lab / cwd,
        env=controlled_environment(),
        capture_output=True,
        text=True,
        timeout=120,
    )


def normalized(text, lab):
    return text.replace(str(lab.resolve()), "<LAB>").replace(str(lab), "<LAB>")


def assert_case(test, lab, case, prefix=None):
    result = execute(lab, case["args"], case["cwd"], prefix)
    test.assertEqual(normalized(result.stdout, lab), case["stdout"], case["id"])
    if "error" in case:
        test.assertNotEqual(result.returncode, 0, case["id"])
        test.assertIn(case["error"] + ":", result.stderr, case["id"])
        for fragment in case.get("stderr_contains", []):
            test.assertIn(fragment, result.stderr, case["id"])
        if case["id"] == "circular-import":
            frames = re.findall(r'File "[^"\n]+/cycles/([^"/]+)"', result.stderr)
            test.assertEqual(frames, ["run.py", "cycle_a.py", "cycle_b.py"])
    else:
        test.assertEqual(result.returncode, 0, result.stderr)
        # uv may write environment notices. Actual Python must be quiet on stderr.
        if prefix is None:
            test.assertEqual(result.stderr, "", case["id"])
    return result


class ModulesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="js2py-modules-test-")
        self.addCleanup(self.temp.cleanup)
        self.lab = Path(self.temp.name) / "u06-modules"
        for name in NAMES:
            target = self.lab / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((LAB / name).read_bytes())

    def check_program(self, source, cwd="solutions/independent"):
        result = execute(self.lab, ["-c", textwrap.dedent(source)], cwd)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def test_all_documented_entry_groups_and_expected_failures(self):
        self.assertEqual(len(CASES), 28)
        self.assertEqual(sum("error" in c for c in CASES), 8)
        for case in CASES:
            with self.subTest(case=case["id"]):
                assert_case(self, self.lab, case)

    def test_three_locales_share_every_source_command_output_and_comparison(self):
        self.assertEqual(len(LESSONS), 3)
        references = []
        fences = []
        for lesson in LESSONS:
            text = lesson.read_text()
            references.append(re.findall(r"getModuleExample\('([^']+)'\)", text))
            fences.append(
                re.findall(
                    r"```(?:python|javascript|bash|text)[^\n]*\n(.*?)```", text, re.S
                )
            )
            self.assertIn("/learning-assets/js2py/u06-modules.zip", text)
            self.assertEqual(text.count("<details>"), 3)
            self.assertNotIn("<details open", text)
            self.assertIn("compare={true} canRun={false}", text)
            self.assertNotIn("getU00Example(", text)
            self.assertEqual(len(re.findall(r"^## \d+\.", text, re.M)), 14)
        self.assertEqual(references[0], references[1])
        self.assertEqual(references[1], references[2])
        self.assertEqual(fences[0], fences[1])
        self.assertEqual(fences[1], fences[2])
        self.assertEqual(set(references[0]), set(NAMES) - {"README.md"})
        self.assertEqual(len(references[0]), 37)

    def test_shared_sources_do_not_require_later_language_constructs(self):
        excluded = (
            (
                ast.ClassDef,
                ast.AsyncFunctionDef,
                ast.Await,
                ast.With,
                ast.AsyncWith,
                ast.Yield,
                ast.YieldFrom,
                ast.TryStar,
                ast.AnnAssign,
            )
            if hasattr(ast, "TryStar")
            else (
                ast.ClassDef,
                ast.AsyncFunctionDef,
                ast.Await,
                ast.With,
                ast.AsyncWith,
                ast.Yield,
                ast.YieldFrom,
                ast.AnnAssign,
            )
        )
        for name in NAMES:
            if not name.endswith(".py"):
                continue
            tree = ast.parse((LAB / name).read_text())
            for node in ast.walk(tree):
                self.assertNotIsInstance(node, excluded, name)
                if isinstance(node, ast.FunctionDef):
                    self.assertEqual(node.decorator_list, [], name)
                    self.assertIsNone(node.returns, name)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(
                        node.func.id, {"open", "eval", "exec", "__import__"}, name
                    )

    def test_repeated_import_and_new_process_have_separate_lifetimes(self):
        case = next(c for c in CASES if c["id"] == "import-twice")
        first = assert_case(self, self.lab, case)
        second = assert_case(self, self.lab, case)
        self.assertEqual(first.stdout, second.stdout)
        # Edit after one import inside a process: normal import reuses old state;
        # the following fresh process sees the new source. Maintainer-only I/O.
        source = self.lab / "first_import/task_rules.py"
        changed = source.read_text().replace(
            "DEFAULT_MINUTES = 20", "DEFAULT_MINUTES = 400"
        )
        output = self.check_program(
            f"""
            import task_rules
            from pathlib import Path
            Path("task_rules.py").write_text({changed!r})
            import task_rules as again
            print(task_rules is again, again.DEFAULT_MINUTES)
        """,
            "first_import",
        )
        self.assertEqual(output, "task_rules initialized\nTrue 20\n")
        self.assertEqual(
            self.check_program(
                "import task_rules; print(task_rules.DEFAULT_MINUTES)", "first_import"
            ),
            "task_rules initialized\n400\n",
        )

    def test_module_defined_globals_and_mutable_from_bindings(self):
        output = self.check_program(
            """
            import settings
            from settings import BUDGET, current_budget, tags
            assert tags is settings.tags
            settings.BUDGET = 80
            assert BUDGET == 20 and current_budget() == 80
            tags.append("from-caller")
            assert settings.tags == ["python", "from-caller"]
            tags = ["new"]
            assert tags is not settings.tags
            BUDGET = 7
            assert settings.BUDGET == 80 and BUDGET == 7
        """,
            "bindings",
        )
        self.assertEqual(output, "")

    def test_main_guards_import_silence_and_import_name(self):
        self.assertEqual(
            self.check_program(
                "import quiet_report; print(quiet_report.__name__)", "entry_points"
            ),
            "quiet_report\n",
        )
        self.assertEqual(
            self.check_program(
                "import task_tools.app; print(task_tools.app.__name__)", "package_demo"
            ),
            "task_tools.app\n",
        )
        self.assertEqual(
            self.check_program("import study_plan.app; print(study_plan.app.__name__)"),
            "study_plan.app\n",
        )

    def test_failing_entry_sentinel_is_not_reached_on_import_but_is_on_execution(self):
        for relative, cwd, entry, imported in [
            (
                "entry_points/quiet_report.py",
                "entry_points",
                ["quiet_report.py"],
                "quiet_report",
            ),
            (
                "package_demo/task_tools/app.py",
                "package_demo",
                ["-m", "task_tools.app"],
                "task_tools.app",
            ),
            (
                "solutions/independent/study_plan/app.py",
                "solutions/independent",
                ["-m", "study_plan.app"],
                "study_plan.app",
            ),
        ]:
            with self.subTest(file=relative):
                path = self.lab / relative
                text = path.read_text()
                self.assertEqual(text.count("def main():"), 1)
                path.write_text(
                    text.replace(
                        "def main():",
                        'def main():\n    raise RuntimeError("ENTRY_SENTINEL")',
                    )
                )
                self.assertEqual(self.check_program(f"import {imported}", cwd), "")
                result = execute(self.lab, entry, cwd)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("RuntimeError: ENTRY_SENTINEL", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_known_business_actions_and_dependency_direction_are_explicit(self):
        for package in ["package_demo/task_tools", "solutions/independent/study_plan"]:
            initializer = ast.parse((self.lab / package / "__init__.py").read_text())
            self.assertEqual(len(initializer.body), 1)
            self.assertIsInstance(initializer.body[0], ast.Expr)
            self.assertIsInstance(initializer.body[0].value, ast.Constant)
            app = ast.parse((self.lab / package / "app.py").read_text())
            self.assertEqual(
                [type(n) for n in app.body], [ast.ImportFrom, ast.FunctionDef, ast.If]
            )
            guard = app.body[-1]
            self.assertEqual(
                ast.dump(guard.test),
                ast.dump(ast.parse('__name__ == "__main__"', mode="eval").body),
            )
            self.assertEqual(
                ast.dump(guard.body[0]), ast.dump(ast.parse("main()").body[0])
            )
        rules = ast.parse(
            (self.lab / "solutions/independent/study_plan/rules.py").read_text()
        )
        self.assertFalse(
            any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(rules))
        )
        summary = ast.parse(
            (self.lab / "solutions/independent/study_plan/summary.py").read_text()
        )
        imports = [n for n in ast.walk(summary) if isinstance(n, ast.ImportFrom)]
        self.assertEqual([(n.module, n.level) for n in imports], [("rules", 1)])

    def test_shadowing_repair_uses_new_process_and_actual_standard_library(self):
        case = next(c for c in CASES if c["id"] == "shadowed-standard-module")
        assert_case(self, self.lab, case)
        # Retain the orphan __pycache__ to prove it does not keep loading the
        # renamed source as statistics in this ordinary CPython layout.
        (self.lab / "shadowing/statistics.py").rename(
            self.lab / "shadowing/practice_statistics.py"
        )
        result = execute(self.lab, ["shadowing/show_source.py"])
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[-1], "Average: 25")
        self.assertNotIn(str(self.lab), lines[0])
        self.assertTrue(lines[0].endswith("statistics.py"))

    def test_cache_files_are_bounded_and_source_is_unchanged(self):
        before = {name: (self.lab / name).read_bytes() for name in NAMES}
        for case in CASES:
            assert_case(self, self.lab, case)
        for name, data in before.items():
            self.assertEqual((self.lab / name).read_bytes(), data)
        new = {
            str(p.relative_to(self.lab)) for p in self.lab.rglob("*") if p.is_file()
        } - set(NAMES)
        self.assertTrue(new, "ordinary imports should exercise bytecode caching")
        for name in new:
            path = Path(name)
            self.assertEqual(path.parent.name, "__pycache__")
            self.assertEqual(path.suffix, ".pyc")
            original = path.parent.parent / (path.name.split(".", 1)[0] + ".py")
            self.assertIn(str(original), NAMES)

    def test_parser_types_values_and_explicit_cause(self):
        self.check_program("""
            from study_plan.rules import parse_minutes
            for raw, expected in [(" 20 ", 20), ("0", 0), ("+3", 3), ("0004", 4)]:
                assert parse_minutes(raw) == expected
            for raw in [None, True, 20, 2.5, [], {}, b"20"]:
                try:
                    parse_minutes(raw)
                except TypeError as error:
                    assert str(error) == "minutes must be text"
                else:
                    raise AssertionError(raw)
            for raw in ["", " ", "twenty", "2.5"]:
                try:
                    parse_minutes(raw)
                except ValueError as error:
                    assert str(error) == "minutes must be an integer"
                    assert isinstance(error.__cause__, ValueError)
                else:
                    raise AssertionError(raw)
            try:
                parse_minutes("-5")
            except ValueError as error:
                assert str(error) == "minutes must be non-negative"
                assert error.__cause__ is None
            else:
                raise AssertionError("negative accepted")
        """)

    def test_per_item_threshold_inclusive_zero_and_empty(self):
        self.check_program("""
            from study_plan.summary import build_plan
            rows = [
                {"title": "Read", "minutes": " 20 "},
                {"title": "Typo", "minutes": "twenty"},
                {"title": "Zero", "minutes": "0"},
                {"title": "Negative", "minutes": "-5"},
                {"title": "Practice", "minutes": "35"},
            ]
            for budget, titles, total in [(20, ["Read", "Zero"], 20), (40, ["Read", "Zero", "Practice"], 55), (0, ["Zero"], 0)]:
                plan = build_plan(rows, budget)
                assert [r["title"] for r in plan["accepted"]] == titles
                assert plan["total_minutes"] == total
                assert plan["rejected"] == [
                    {"row": 2, "title": "Typo", "reason": "minutes must be an integer"},
                    {"row": 4, "title": "Negative", "reason": "minutes must be non-negative"},
                ]
            assert build_plan(rows) == build_plan(rows, 20)
            rows[0]["minutes"] = "21"
            assert build_plan(rows)["accepted"] == [{"title": "Zero", "minutes": 0}]
            assert build_plan([]) == {"accepted": [], "rejected": [], "total_minutes": 0}
            all_bad = build_plan(rows[1:2] + rows[3:4])
            assert not all_bad["accepted"] and all_bad["total_minutes"] == 0
            assert [x["row"] for x in all_bad["rejected"]] == [1, 2]
        """)

    def test_budget_validation_also_applies_to_empty_rows(self):
        self.check_program("""
            from study_plan.summary import build_plan
            for rows in [[], [{"title": "A", "minutes": "0"}]]:
                for budget in [True, False, 20.0, "20", None, [], {}]:
                    try:
                        build_plan(rows, budget)
                    except TypeError as error:
                        assert str(error) == "budget must be an integer"
                    else:
                        raise AssertionError(budget)
                for budget in [-1, -100]:
                    try:
                        build_plan(rows, budget)
                    except ValueError as error:
                        assert str(error) == "budget must be non-negative"
                    else:
                        raise AssertionError(budget)
        """)

    def test_threshold_variations_order_and_row_number_matrix(self):
        self.check_program("""
            from itertools import permutations, product
            from study_plan.summary import build_plan
            options = [("0", 0, None), ("2", 2, None), ("-1", None, "minutes must be non-negative"), ("bad", None, "minutes must be an integer")]
            count = 0
            for length in range(4):
                for items in product(options, repeat=length):
                    for budget in [0, 1, 2, 3]:
                        rows = [{"title": str(i), "minutes": item[0]} for i, item in enumerate(items)]
                        result = build_plan(rows, budget)
                        accepted = [{"title": str(i), "minutes": item[1]} for i, item in enumerate(items) if item[2] is None and item[1] <= budget]
                        rejected = [{"row": i + 1, "title": str(i), "reason": item[2]} for i, item in enumerate(items) if item[2] is not None]
                        assert result == {"accepted": accepted, "rejected": rejected, "total_minutes": sum(r["minutes"] for r in accepted)}
                        count += 1
            assert count == 340
            for items in permutations(options):
                rows = [{"title": str(i), "minutes": item[0]} for i, item in enumerate(items)]
                result = build_plan(rows, 1)
                assert [x["row"] for x in result["rejected"]] == [i + 1 for i, item in enumerate(items) if item[2] is not None]
                assert result["accepted"] == [{"title": str(i), "minutes": 0} for i, item in enumerate(items) if item[0] == "0"]
        """)

    def test_unknown_failures_propagate_and_input_is_not_mutated(self):
        self.check_program("""
            from copy import deepcopy
            import study_plan.summary as summary
            for bad, kind in [({}, KeyError), ({"title": "X"}, KeyError), ({"minutes": "1"}, KeyError), ({"title": "X", "minutes": None}, TypeError), ({"title": "X", "minutes": 2}, TypeError)]:
                for position in range(3):
                    rows = [{"title": "A", "minutes": "1"}, {"title": "Bad", "minutes": "bad"}]
                    rows.insert(position, deepcopy(bad))
                    before = deepcopy(rows)
                    try:
                        summary.build_plan(rows)
                    except kind:
                        assert rows == before
                    else:
                        raise AssertionError("failure hidden")
            for kind in [RuntimeError, TypeError, KeyError, KeyboardInterrupt, SystemExit]:
                marker = kind("unexpected")
                def broken(raw):
                    raise marker
                summary.parse_minutes = broken
                try:
                    summary.build_plan([{"title": "A", "minutes": "1"}])
                except kind as error:
                    assert error is marker
                else:
                    raise AssertionError("unknown failure hidden")
        """)
        # Same-category internal failure in successful processing is outside try.
        path = self.lab / "solutions/independent/study_plan/summary.py"
        path.write_text(
            path.read_text().replace(
                "        else:\n",
                '        else:\n            raise ValueError("PLAN_BUG")\n',
            )
        )
        result = execute(
            self.lab,
            [
                "-c",
                'from study_plan.summary import build_plan; build_plan([{"title":"A","minutes":"1"}])',
            ],
            "solutions/independent",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ValueError: PLAN_BUG", result.stderr)

    def test_result_lists_and_records_are_owned_by_each_call(self):
        self.check_program("""
            from copy import deepcopy
            from study_plan.summary import build_plan
            rows = [{"title": "Read", "minutes": "20"}, {"title": "Bad", "minutes": "bad"}]
            before = deepcopy(rows)
            first, second = build_plan(rows), build_plan(rows)
            assert first is not second and first["accepted"][0] is not rows[0]
            first["accepted"][0]["minutes"] = 99
            first["accepted"].append({"title": "Extra", "minutes": 1})
            first["rejected"][0]["reason"] = "changed"
            first["rejected"].append({"row": 9, "title": "Extra", "reason": "changed"})
            assert rows == before and second == build_plan(rows)
            one, two = build_plan([]), build_plan([])
            one["accepted"].append({"title": "Extra", "minutes": 1})
            assert two == {"accepted": [], "rejected": [], "total_minutes": 0}
            assert two["accepted"] is not two["rejected"]
            rows[0]["minutes"] = "21"
            assert build_plan(rows)["accepted"] == []
        """)

    def test_reference_package_reconstructs_outside_the_download(self):
        empty = Path(self.temp.name) / "my_plan"
        empty.mkdir()
        self.assertEqual(list(empty.iterdir()), [])
        for name in NAMES:
            prefix = "solutions/independent/"
            if name.startswith(prefix):
                target = empty / name.removeprefix(prefix)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((LAB / name).read_bytes())
        for case in CASES:
            if case["id"] in {
                "independent-import",
                "independent-entry",
                "independent-direct-fails",
            }:
                assert_case(self, empty, dict(case, cwd="."))
        for forbidden in ["pyproject.toml", "uv.lock", ".venv"]:
            self.assertFalse((empty / forbidden).exists())

    def test_zip_is_exact_allowlist_without_caches_secrets_or_tooling(self):
        self.assertEqual(len(NAMES), 38)
        self.assertEqual(len(NAMES), len(set(NAMES)))
        with zipfile.ZipFile(
            ROOT / "public/learning-assets/js2py/u06-modules.zip"
        ) as archive:
            self.assertEqual(
                set(archive.namelist()), {"u06-modules/" + name for name in NAMES}
            )
            for name in NAMES:
                self.assertEqual(
                    archive.read("u06-modules/" + name), (LAB / name).read_bytes()
                )
                self.assertFalse(Path(name).is_absolute())
                self.assertNotIn("..", Path(name).parts)
                self.assertNotIn("__pycache__", name)
                self.assertNotIn(".env", name)


if __name__ == "__main__":
    unittest.main()
