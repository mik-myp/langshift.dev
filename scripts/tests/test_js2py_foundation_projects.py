"""Deterministic source/contracts for L08–L10; actual uv checks are separate."""

import ast
import hashlib
import importlib.util
import itertools
import json
import re
import subprocess
import sys
import tomllib
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads(
    (Path(__file__).parent / "fixtures/js2py-foundation-projects.json").read_text()
)
FENCE = re.compile(r"^```[^\n]*\n.*?^```", re.M | re.S)


class FoundationProjects(unittest.TestCase):
    def test_three_locale_sources_commands_outputs_and_answer_boundaries(self):
        for row in ROWS:
            editions = [
                (ROOT / f"content/docs/js2py/{row['slug']}{suffix}.mdx").read_text()
                for suffix in ["", ".zh-cn", ".zh-tw"]
            ]
            for text in editions:
                self.assertEqual(text.count("<details>"), 3)
                self.assertNotIn("<details open", text)
                self.assertEqual(
                    len(re.findall(r"^## \d+\.", text, re.M)), row["sections"]
                )
                self.assertEqual(
                    re.findall(rf"{row['loader']}\('([^']+)'\)", text), row["refs"]
                )
                self.assertIn(f"/learning-assets/js2py/{row['lab']}.zip", text)
                self.assertIn("2026-09-28", text)
            self.assertEqual(FENCE.findall(editions[0]), FENCE.findall(editions[1]))
            self.assertEqual(FENCE.findall(editions[1]), FENCE.findall(editions[2]))

    def test_exact_zip_allowlists_no_environment_or_generated_data(self):
        for row in ROWS:
            lab = row["lab"]
            names = json.loads((ROOT / f"examples/js2py/{lab}-files.json").read_text())
            self.assertEqual(len(names), len(set(names)))
            self.assertTrue(set(row["refs"]) <= set(names))
            with zipfile.ZipFile(
                ROOT / f"public/learning-assets/js2py/{lab}.zip"
            ) as archive:
                self.assertEqual(
                    sorted(archive.namelist()), sorted(f"{lab}/{n}" for n in names)
                )
                for name in names:
                    self.assertFalse(
                        set(Path(name).parts)
                        & {".venv", "__pycache__", "_output", ".pytest_cache"}
                    )
                    self.assertEqual(
                        archive.read(f"{lab}/{name}"),
                        (ROOT / "examples/js2py" / lab / name).read_bytes(),
                    )

    def test_project_declarations_and_public_lockfiles_are_consistent(self):
        for row in ROWS:
            lab = ROOT / "examples/js2py" / row["lab"]
            names = json.loads(
                (ROOT / f"examples/js2py/{row['lab']}-files.json").read_text()
            )
            for name in names:
                if not name.endswith("pyproject.toml"):
                    continue
                project = lab / name
                config = tomllib.loads(project.read_text())
                self.assertEqual(config["project"]["requires-python"], ">=3.13,<3.14")
                self.assertIs(config["tool"]["uv"]["package"], False)
                self.assertEqual(
                    project.with_name(".python-version").read_text(), "3.13.15\n"
                )
                lock = tomllib.loads(project.with_name("uv.lock").read_text())
                self.assertIn(
                    config["project"]["name"], [p["name"] for p in lock["package"]]
                )
                for package in lock["package"]:
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
                if row["lab"] != "u08-environments":
                    self.assertEqual(config["project"]["dependencies"], [])
                    self.assertEqual(
                        config["dependency-groups"]["dev"], ["pytest==8.4.2"]
                    )

    def test_no_unexplained_decorators_classes_async_or_fixture_parameters(self):
        for row in ROWS:
            lab = ROOT / "examples/js2py" / row["lab"]
            names = json.loads(
                (ROOT / f"examples/js2py/{row['lab']}-files.json").read_text()
            )
            for name in names:
                if not name.endswith(".py"):
                    continue
                tree = ast.parse((lab / name).read_text())
                for node in ast.walk(tree):
                    self.assertNotIsInstance(
                        node, (ast.ClassDef, ast.AsyncFunctionDef, ast.Await, ast.Yield)
                    )
                    if isinstance(node, ast.FunctionDef):
                        self.assertEqual(node.decorator_list, [])
                        self.assertIsNone(node.returns)
                        if node.name.startswith("test_"):
                            self.assertEqual(node.args.args, [])

    def test_all_archived_current_sources_retain_original_bytes(self):
        for folder in [
            "js2py-u08-projects",
            "js2py-u09-advanced",
            "js2py-u10-pitfalls",
        ]:
            archive = ROOT / "docs/archive" / folder
            hashes = json.loads((archive / "sha256.json").read_text())
            self.assertEqual(len(hashes), 3)
            for name, expected in hashes.items():
                self.assertEqual(
                    hashlib.sha256((archive / name).read_bytes()).hexdigest(), expected
                )

    def test_l09_function_matrix_is_independent_of_pytest(self):
        path = ROOT / "examples/js2py/u09-testing/study.py"
        spec = importlib.util.spec_from_file_location("tested_study", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        items = [
            {"minutes": m, "done": d} for m in [0, 1, 20, 21] for d in [False, True]
        ]
        self.assertEqual(module.pending_minutes([]), 0)
        for combination in itertools.product(items, repeat=3):
            tasks = [dict(item) for item in combination]
            before = [dict(item) for item in tasks]
            expected = sum(item["minutes"] for item in tasks if not item["done"])
            self.assertEqual(module.pending_minutes(tasks), expected)
            self.assertEqual(tasks, before)
        for bad in [
            None,
            (),
            {},
            [None],
            [{}],
            [{"minutes": 1}],
            [{"minutes": 1, "done": 1}],
            [{"minutes": 1, "done": False, "extra": 1}],
        ]:
            with self.assertRaises(ValueError):
                module.pending_minutes(bad)

    def test_l10_initial_fixture_and_factory_are_the_same_data(self):
        lab = ROOT / "examples/js2py/u10-local-project"
        tree = ast.parse((lab / "task_app/app.py").read_text())
        factory = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "initial_tasks"
        )
        self.assertEqual(
            ast.literal_eval(factory.body[0].value),
            json.loads((lab / "fixtures/initial.json").read_text()),
        )

    def test_l10_independent_planner_and_rules_on_fresh_process(self):
        lab = ROOT / "examples/js2py/u10-local-project"
        source = """import itertools
from task_app.rules import complete_title, summarize
from solutions.new_requirement import plan_within_budget
for minutes in itertools.product([0, 1, 20, 21], repeat=3):
    tasks = [{"title": str(i), "minutes": value, "done": False} for i, value in enumerate(minutes)]
    for budget in [0, 1, 20, 40]:
        expected = []
        total = 0
        for item in tasks:
            if total + item["minutes"] <= budget:
                expected.append(item["title"])
                total += item["minutes"]
        selected, used = plan_within_budget(tasks, budget)
        assert [item["title"] for item in selected] == expected and used == total
        if selected:
            selected[0]["done"] = True
        assert all(item["done"] is False for item in tasks)
    completed, count = complete_title(tasks, "1")
    assert count == 1 and tasks[1]["done"] is False
    assert summarize(completed)["pending_minutes"] == minutes[0] + minutes[2]
print("256 plans and 64 completion variants passed")
"""
        result = subprocess.run(
            [sys.executable, "-c", source],
            cwd=lab,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "256 plans and 64 completion variants passed\n")

    def test_reference_test_counts_are_explicit_not_silent_discovery(self):
        for folder, expected in [
            ("u09-testing/tests", 6),
            ("u09-testing/solutions/budget/tests", 9),
            ("u10-local-project/tests", 15),
        ]:
            count = 0
            for path in (ROOT / "examples/js2py" / folder).glob("test_*.py"):
                count += sum(
                    isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
                    for n in ast.parse(path.read_text()).body
                )
            self.assertEqual(count, expected)


if __name__ == "__main__":
    unittest.main()
