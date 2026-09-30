import importlib.util
import io
import json
import re
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
    def test_current_learning_path_requires_product_integration(self):
        learning_path = (ROOT / "docs/js2py-learning-path.zh-cn.md").read_text()
        capstone = (ROOT / "docs/js2py-capstone-spec.zh-cn.md").read_text()
        self.assertTrue((ROOT / "docs/js2py-integration-spine.zh-cn.md").exists())
        for locale in ("", ".zh-cn", ".zh-tw"):
            guide = ROOT / "content/docs/js2py" / f"project-integration{locale}.mdx"
            self.assertTrue(guide.exists(), guide)
            self.assertIn("V4", guide.read_text())
        self.assertNotIn("/zh-cn/docs/js2py/", (ROOT / "content/docs/js2py/project-integration.zh-tw.mdx").read_text())
        self.assertNotIn("/zh-tw/docs/js2py/", (ROOT / "content/docs/js2py/project-integration.zh-cn.mdx").read_text())
        self.assertIn("/en/docs/js2py/project-integration", (ROOT / "content/docs/js2py/index.mdx").read_text())
        self.assertIn("/zh-cn/docs/js2py/project-integration", (ROOT / "content/docs/js2py/index.zh-cn.mdx").read_text())
        self.assertIn("/zh-tw/docs/js2py/project-integration", (ROOT / "content/docs/js2py/index.zh-tw.mdx").read_text())
        for locale in ("", ".zh-cn", ".zh-tw"):
            source_matrix = ROOT / "content/docs/js2py" / f"official-sources{locale}.mdx"
            self.assertTrue(source_matrix.exists(), source_matrix)
            self.assertIn("PostgreSQL", source_matrix.read_text())
        self.assertIn("/en/docs/js2py/official-sources", (ROOT / "content/docs/js2py/index.mdx").read_text())
        self.assertIn("/zh-cn/docs/js2py/official-sources", (ROOT / "content/docs/js2py/index.zh-cn.mdx").read_text())
        self.assertIn("/zh-tw/docs/js2py/official-sources", (ROOT / "content/docs/js2py/index.zh-tw.mdx").read_text())
        self.assertIn("贯穿整合项目：把实验合并成一份服务", learning_path)
        self.assertIn("33 章完成声明范围内的本地材料验收", learning_path)
        self.assertNotIn("当前 39 个逻辑章节中 15 个已实现", learning_path)
        self.assertIn("不透明随机 Bearer 会话", learning_path)
        self.assertIn("不透明随机 Bearer 会话", capstone)
        self.assertNotIn("pwdlib 的 Argon2 哈希 + PyJWT", learning_path)
        self.assertNotIn("使用经维护的密码哈希库与 JWT 库", capstone)

        stale_fragments = {
            "后续页面仍会逐章迁移",
            "后续页面仍在逐章迁移",
            "后续旧页面仍在迁移",
            "后续旧稿仍需重编",
            "The new standard is implemented through L06",
            "later historical pages are still being migrated",
            "Later historical pages still need rewriting",
            "later historical material still needs rewriting",
        }
        for path in sorted((ROOT / "content/docs/js2py").glob("module-0[0-5]-*.mdx")):
            text = path.read_text()
            self.assertTrue(
                stale_fragments.isdisjoint(text),
                f"stale migration status remains in {path.name}",
            )

    def test_product_delivery_templates_support_real_target_gates(self):
        delivery = ROOT / "examples/js2py/product-delivery"
        manifest = json.loads((delivery.parent / "product-delivery-files.json").read_text())
        expected = {
            ".dockerignore",
            ".github/workflows/verify-and-release.yml.template",
            "Caddyfile.template",
            "Dockerfile",
            "README.md",
            "README.zh-cn.md",
            "README.zh-tw.md",
            "app/healthcheck.py",
            "app/secret_config.py",
            "commands/backup.sh",
            "commands/migrate-start.sh",
            "commands/release.sh",
            "commands/restore.sh",
            "compose.production.yaml",
            "check_integration_record.py",
            "templates/integration-record.json",
            "product-workbook.md",
            "product-workbook.zh-cn.md",
            "product-workbook.zh-tw.md",
            "pg_service.conf.template",
            "product.service.template",
            "release-record.template",
            "rollback-record.template",
            "starter/.gitignore",
            "starter/.python-version",
            "starter/pyproject.toml",
            "starter/README.md",
            "starter/README.zh-cn.md",
            "starter/README.zh-tw.md",
            "starter/docs/README.md",
            "starter/docs/README.zh-cn.md",
            "starter/docs/README.zh-tw.md",
            "starter/src/README.md",
            "starter/src/README.zh-cn.md",
            "starter/src/README.zh-tw.md",
            "starter/tests/README.md",
            "starter/tests/README.zh-cn.md",
            "starter/tests/README.zh-tw.md",
            "templates/product-contract.md",
            "templates/product-contract.zh-cn.md",
            "templates/product-contract.zh-tw.md",
            "templates/incident-record.template",
            "templates/maintenance-record.template",
        }
        self.assertEqual(set(manifest), expected)

        starter = delivery / "starter"
        self.assertFalse((starter / "uv.lock").exists())
        self.assertFalse(list(starter.rglob("*.py")))
        gitignore = (starter / ".gitignore").read_text()
        self.assertNotIn("uv.lock", gitignore)
        self.assertNotIn("docs/", gitignore)
        pyproject = (starter / "pyproject.toml").read_text()
        self.assertIn('requires-python = ">=3.13,<3.14"', pyproject)
        self.assertIn("pytest==8.4.2", pyproject)
        self.assertIn("package = false", pyproject)

        dockerfile = (delivery / "Dockerfile").read_text()
        self.assertIn("UV_PROJECT_ENVIRONMENT=/opt/venv", dockerfile)
        self.assertIn("COPY --from=build /opt/venv /opt/venv", dockerfile)
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertIn("HEALTHCHECK", dockerfile)

        compose = (delivery / "compose.production.yaml").read_text()
        self.assertIn("read_only: true", compose)
        self.assertIn("cap_drop: [ALL]", compose)
        self.assertIn('security_opt: ["no-new-privileges:true"]', compose)
        self.assertIn("DATABASE_URL_FILE", compose)
        self.assertNotIn("POSTGRES_PASSWORD", compose)
        self.assertNotIn("ports:", compose.split("services:", 1)[1].split("  edge:", 1)[0])

        workflow = (delivery / ".github/workflows/verify-and-release.yml.template").read_text()
        self.assertIn("migration_db:", workflow)
        self.assertIn("test_db:", workflow)
        self.assertIn("environment: production", workflow)
        self.assertIn("ops/deploy-approved.sh", workflow)
        self.assertIn("alembic upgrade head", workflow)
        self.assertIn("alembic check", workflow)
        self.assertIn("pytest -q", workflow)

        restore = (delivery / "commands/restore.sh").read_text()
        self.assertIn("restore_[a-z0-9_]+", restore)
        self.assertIn("sha256sum --check", restore)
        self.assertIn("--single-transaction", restore)
        self.assertIsNone(re.search(r"pg_restore[^\n]*--clean", restore))
        self.assertNotIn("DROP ", restore.replace("DROP, production", ""))

        expected_refs = [
            "release-record.template",
            "Dockerfile",
            "product.service.template",
            "commands/migrate-start.sh",
            "Caddyfile.template",
            ".github/workflows/verify-and-release.yml.template",
            "commands/backup.sh",
            "commands/restore.sh",
            "rollback-record.template",
        ]
        for locale in ("", ".zh-cn", ".zh-tw"):
            contract = delivery / f"templates/product-contract{locale}.md"
            contract_text = contract.read_text()
            self.assertIn("Resource", contract_text) if locale == "" else self.assertIn("资源" if locale == ".zh-cn" else "資源", contract_text)
            self.assertIn("Failure policy" if locale == "" else "失败政策" if locale == ".zh-cn" else "失敗政策", contract_text)

        for locale in ("", ".zh-cn", ".zh-tw"):
            workbook = delivery / f"product-workbook{locale}.md"
            workbook_text = workbook.read_text()
            for stage in ("V0", "V1", "V2", "V3", "V3.5", "V4", "V5"):
                self.assertIn(f"## {stage}", workbook_text)
            for evidence_kind in (
                "environment_recovery",
                "real_process_requests",
                "existing_data_migration",
                "object_authorization_negative",
                "cancellation_cleanup",
                "public_https",
                "human_review",
            ):
                self.assertIn(evidence_kind, workbook_text)
            self.assertIn("templates/maintenance-record.template", workbook_text)

        for locale in ("", ".zh-cn", ".zh-tw"):
            runbook = ROOT / "content/docs/js2py" / f"deployment-runbook{locale}.mdx"
            text = runbook.read_text()
            refs = re.findall(r"getProductDeliveryExample\('([^']+)'\)", text)
            self.assertEqual(refs, expected_refs)
            self.assertIn("/learning-assets/js2py/product-delivery.zip", text)

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
