"""Integrated backend metadata guards; live service/DB/operations tests are separate."""

import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads(
    (ROOT / "scripts/tests/fixtures/js2py-backend-chapters.json").read_text()
)
spec = importlib.util.spec_from_file_location(
    "backend_content_checks", ROOT / "scripts/check-js2py-content.py"
)
CHECKS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CHECKS)


class BackendChapterTests(unittest.TestCase):
    def test_integrated_identifiers_are_unique_and_scoped(self):
        for key in ["lab", "loader", "slug"]:
            self.assertEqual(len({row[key] for row in ROWS}), len(ROWS))
        for row in ROWS:
            self.assertRegex(row["lab"], r"^[a-z]\d\d-[a-z0-9-]+$")
            self.assertRegex(row["slug"], r"^module-\d\d-[a-z0-9-]+$")
            self.assertRegex(row["loader"], r"^get[A-Za-z]+Example$")
            self.assertGreaterEqual(row["sections"], 8)

    def test_three_locales_have_canonical_examples_and_hidden_answers(self):
        for row in ROWS:
            names = json.loads(
                (ROOT / f"examples/js2py/{row['lab']}-files.json").read_text()
            )
            texts = {
                path.name: path.read_text()
                for path in (ROOT / "content/docs/js2py").glob(row["slug"] + "*.mdx")
            }
            self.assertEqual(len(texts), 3)
            lesson = {
                **row,
                "compare_text": True,
                "download": "/learning-assets/js2py/" + row["lab"] + ".zip",
                "forbidden": [],
            }
            self.assertEqual(CHECKS.source_parity_errors(texts, names, lesson), [])
            for text in texts.values():
                self.assertEqual(
                    len(re.findall(r"^## ", text, re.MULTILINE)), row["sections"]
                )
                self.assertGreaterEqual(text.count("<details>"), 3)
                self.assertEqual(text.count("<details>"), text.count("</details>"))
                self.assertNotIn("<details open", text)

    def test_parity_rejects_sql_http_and_configuration_drift(self):
        lesson = {
            "loader": "getExample",
            "refs": [],
            "download": "/lab.zip",
            "forbidden": [],
            "compare_text": True,
        }
        for language in ("sql", "http", "json", "toml", "ini", "yaml", "dockerfile"):
            with self.subTest(language=language):
                original = "/lab.zip\n```" + language + "\noriginal\n```\n"
                changed = original.replace("original", "changed")
                texts = {"en": original, "zh-cn": original, "zh-tw": changed}
                self.assertIn(
                    "getExample: translated code/output fences differ",
                    CHECKS.source_parity_errors(texts, [], lesson),
                )

    def test_full_course_map_links_each_retained_page_in_each_locale(self):
        chapters = json.loads((ROOT / "docs/js2py-chapter-contracts.json").read_text())[
            "chapters"
        ]
        self.assertEqual(len(chapters), 39)
        course = ROOT / "content/docs/js2py"
        for locale, suffix in (("en", ""), ("zh-cn", ".zh-cn"), ("zh-tw", ".zh-tw")):
            index = (course / ("index" + suffix + ".mdx")).read_text()
            self.assertNotIn("：**39", index, "Separate the closing emphasis delimiter from the following number")
            self.assertNotIn("结论：**教材", index)
            self.assertNotIn("結論：**教材", index)
            for number, chapter in enumerate(chapters):
                candidates = [
                    p
                    for p in course.glob(f"module-{number:02d}-*.mdx")
                    if not p.name.endswith((".zh-cn.mdx", ".zh-tw.mdx"))
                ]
                self.assertEqual(len(candidates), 1)
                slug = candidates[0].stem
                self.assertTrue((course / (slug + suffix + ".mdx")).is_file())
                self.assertIn(f"/{locale}/docs/js2py/{slug}", index)
                self.assertIn(chapter["id"], index)

    def test_download_allowlists_exclude_generated_or_sensitive_locations(self):
        for row in ROWS:
            lab = ROOT / "examples/js2py" / row["lab"]
            names = json.loads((lab.parent / (row["lab"] + "-files.json")).read_text())
            self.assertEqual(len(names), len(set(names)))
            self.assertTrue(set(row["refs"]) <= set(names))
            for name in names:
                self.assertFalse(Path(name).is_absolute())
                self.assertNotIn("..", Path(name).parts)
                self.assertFalse(
                    set(Path(name).parts)
                    & {".venv", "__pycache__", ".pytest_cache", ".mypy_cache", "pgdata"}
                )
                self.assertFalse((lab / name).is_symlink())
                self.assertTrue((lab / name).is_file())
            for readme in ["README.md", "README.zh-cn.md", "README.zh-tw.md"]:
                self.assertIn(readme, names)

    def test_global_loader_namespace_cannot_reuse_language_container_loader(self):
        source = (ROOT / "lib/js2py-examples.ts").read_text()
        declarations = re.findall(r"export function (get\w+Example)\(", source)
        self.assertEqual(len(declarations), len(set(declarations)))
        mappings = dict(re.findall(
            r"export function (get\w+Example)\([^)]*\): string \{\s*return readExample\('([^']+)'",
            source,
        ))
        self.assertEqual(mappings["getContainerExample"], "u02-containers")
        for row in ROWS:
            self.assertEqual(mappings[row["loader"]], row["lab"])

    def test_frontmatter_colon_space_strings_are_quoted(self):
        for row in ROWS:
            for page in (ROOT / "content/docs/js2py").glob(row["slug"] + "*.mdx"):
                header = page.read_text().split("---", 2)[1]
                for line in header.splitlines():
                    if line.startswith(("title: ", "description: ")):
                        value = line.split(": ", 1)[1]
                        if ": " in value:
                            self.assertTrue(value.startswith(("\"", "'")), page.name)

    def test_registered_loader_uses_the_correct_lab(self):
        source = (ROOT / "lib/js2py-examples.ts").read_text()
        for row in ROWS:
            self.assertIn("export function " + row["loader"] + "(", source)
            self.assertIn("'" + row["lab"] + "'", source)
            self.assertIn(row["lab"] + "-files.json", source)

    def test_database_runner_does_not_inherit_another_environment_or_database(self):
        spec = importlib.util.spec_from_file_location(
            "database_foundations_runner", ROOT / "scripts/test-js2py-database-foundations.py"
        )
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        source = {
            "PATH": "/synthetic/bin", "KEEP": "unchanged",
            "UV_PYTHON_INSTALL_DIR": "/synthetic/install", "UV_CACHE_DIR": "/synthetic/cache",
            "PG_BIN": "/synthetic/postgres/bin", "PGHOST": "wrong-host",
            "PGHOSTADDR": "wrong-address", "PGSERVICE": "wrong-service",
            "PGPASSFILE": "/synthetic/credentials", "DATABASE_URL": "wrong-database",
            "UV_PROJECT_ENVIRONMENT": "/synthetic/other-project", "VIRTUAL_ENV": "/synthetic/active",
            "UV_ENV_FILE": "/synthetic/secret-config", "UV_CONFIG_FILE": "/synthetic/uv.toml",
            "PYTHONHOME": "/synthetic/python", "PYTHONPATH": "/synthetic/modules",
            "PYTEST_PLUGINS": "synthetic_plugin", "PYTEST_ADDOPTS": "--wrong-option",
        }
        before = dict(source)
        env = runner.isolated_environment(source)
        self.assertEqual(source, before)
        for key in ("PATH", "KEEP", "UV_PYTHON_INSTALL_DIR", "UV_CACHE_DIR", "PG_BIN"):
            self.assertEqual(env[key], source[key])
        for key in ("PGHOSTADDR", "PGSERVICE", "PGPASSFILE", "UV_PROJECT_ENVIRONMENT",
                    "VIRTUAL_ENV", "UV_ENV_FILE", "UV_CONFIG_FILE", "PYTHONHOME",
                    "PYTHONPATH", "PYTEST_PLUGINS", "PYTEST_ADDOPTS"):
            self.assertNotIn(key, env)
        self.assertEqual(env["PGHOST"], "/nonexistent/langshift-test-ignore-environment")
        self.assertEqual(env["DATABASE_URL"], "postgresql://127.0.0.1:1/do_not_connect")
        self.assertEqual(env["UV_NO_CONFIG"], "1")
        self.assertEqual(env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"], "1")
        self.assertEqual([row["tests"] for row in runner.ROWS], [64, 66, 63])

    def test_reference_material_status_cannot_award_graduation_or_public_launch(self):
        data = json.loads((ROOT / "docs/js2py-chapter-contracts.json").read_text())
        chapters = data["chapters"]
        self.assertEqual(data["schema_version"], 2)
        self.assertEqual(len(chapters), 39)
        self.assertTrue(all(c["authoring_status"] == "complete" for c in chapters))
        self.assertTrue(all(c["learner_acceptance"] == "not_assessed" for c in chapters))
        self.assertEqual(data["completion_claims"]["public_deployment"], "not_performed")
        self.assertEqual(data["completion_claims"]["student_G01_scenarios_not_run"], 24)
        for chapter in chapters:
            if chapter["id"].startswith("O"):
                self.assertEqual(chapter["status"], "environment_pending")
                self.assertTrue(chapter["pending_environment_gates"])
        graduation = next(c for c in chapters if c["id"] == "G01")
        self.assertEqual(graduation["reference_validation"], "material_format_only_passed")

    def test_published_backend_chapters_require_review_evidence(self):
        chapters = json.loads((ROOT / "docs/js2py-chapter-contracts.json").read_text())[
            "chapters"
        ]
        by_id = {row["lab"][:3].upper(): row for row in ROWS}
        for chapter in chapters:
            if chapter["id"].startswith("L") or chapter["status"] not in {"implemented", "environment_pending"}:
                continue
            self.assertIn(chapter["id"], by_id)
            row = by_id[chapter["id"]]
            record_path = (
                ROOT
                / f"docs/reviews/js2py-{row['lab'][:3]}-implementation-review-2026-09-28.json"
            )
            self.assertTrue(record_path.exists())
            record = json.loads(record_path.read_text())
            names = json.loads(
                (ROOT / "examples/js2py" / (row["lab"] + "-files.json")).read_text()
            )
            required = {f"content/docs/js2py/{row['slug']}.mdx"}
            required.update(
                f"examples/js2py/{row['lab']}/{name}"
                for name in names
                if Path(name).name != "uv.lock"
            )
            self.assertTrue(required <= set(record["reviewed_source_paths"]))
            self.assertFalse(record["credential_persisted"])
            # Effective snapshot also binds translations, locks, allowlist and public ZIP.
            for name in record["source_sha256"]:
                self.assertEqual(
                    hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                    record["source_sha256"][name],
                )


if __name__ == "__main__":
    unittest.main()
