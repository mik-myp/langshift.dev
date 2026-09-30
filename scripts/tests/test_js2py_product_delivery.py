import copy
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "examples/js2py/product-delivery"


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "js2py_product_delivery_checker",
        DELIVERY / "check_integration_record.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_checker()


class ProductIntegrationRecordChecks(unittest.TestCase):
    def setUp(self):
        self.template = json.loads(
            (DELIVERY / "templates/integration-record.json").read_text(encoding="utf-8")
        )

    def test_blank_template_is_valid_but_proves_no_backend_or_release(self):
        result = checker.validate(self.template)
        self.assertTrue(result["format_valid"])
        self.assertFalse(result["backend_verified"])
        self.assertFalse(result["public_operation_verified"])
        self.assertFalse(result["redaction_claimed"])
        self.assertEqual(result["stage_status_counts"]["not_run"], 7)

    def test_complete_v0_declaration_can_pass_without_opening_referenced_files(self):
        data = copy.deepcopy(self.template)
        stage = data["stages"][0]
        stage.update(
            status="pass",
            product_revision="learner-commit-1",
            schema_revision="no-database-schema",
            environment="owned local machine",
            blocked_reason=None,
            next_action="begin V1 contract",
        )
        for evidence in stage["evidence"]:
            evidence.update(
                status="pass",
                reference=f"docs/evidence/{evidence['kind']}.md",
                observed_at="2026-09-30T08:00:00Z",
                summary="Learner declaration; subject to review",
            )
        data["redaction_reviewed"] = True
        result = checker.validate(data)
        self.assertTrue(result["format_valid"])
        self.assertTrue(result["redaction_claimed"])
        self.assertFalse(result["backend_verified"])

    def test_stage_pass_cannot_leave_required_evidence_not_run(self):
        data = copy.deepcopy(self.template)
        stage = data["stages"][0]
        stage["status"] = "pass"
        stage["product_revision"] = "learner-commit-1"
        stage["schema_revision"] = "no-database-schema"
        stage["environment"] = "owned local machine"
        with self.assertRaisesRegex(checker.FormatError, "cannot pass"):
            checker.validate(data)

    def test_non_relative_artifact_reference_is_rejected(self):
        data = copy.deepcopy(self.template)
        evidence = data["stages"][0]["evidence"][0]
        evidence.update(
            status="blocked",
            reference="../outside/secret.txt",
            observed_at="2026-09-30T08:00:00+00:00",
            summary="unsafe path",
        )
        data["stages"][0]["status"] = "blocked"
        data["stages"][0]["product_revision"] = "learner-commit-1"
        data["stages"][0]["environment"] = "owned local machine"
        data["stages"][0]["blocked_reason"] = "target unavailable"
        with self.assertRaisesRegex(checker.FormatError, "safe relative"):
            checker.validate(data)

    def test_release_script_refuses_an_unqualified_template_record(self):
        script = DELIVERY / "commands/release.sh"
        record = DELIVERY / "templates/integration-record.json"
        env = os.environ.copy()
        env.update(
            DOCKER_CONTEXT="reviewed-context",
            PROJECT_NAME="learner-product",
            DOMAIN="product.example.com",
            APP_IMAGE="ghcr.io/learner/product@sha256:" + "0" * 64,
            CADDY_IMAGE="library/caddy@sha256:" + "0" * 64,
            RELEASE_RECORD=str(record),
            RELEASE_APPROVAL_REFERENCE="approval-1",
            BACKUP_POLICY_REFERENCE="policy-1",
            ROLLBACK_OWNER="learner",
        )
        result = subprocess.run(
            [str(script)], cwd=DELIVERY, env=env, text=True, capture_output=True, timeout=20
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0-V3 must be pass", result.stderr)

    def test_release_script_requires_predeployment_operations_to_pass(self):
        data = copy.deepcopy(self.template)
        for stage in data["stages"]:
            if stage["id"] in {"V0", "V1", "V2", "V3"}:
                stage.update(status="pass", product_revision="abc", schema_revision="none", environment="isolated lab")
                for evidence in stage["evidence"]:
                    evidence.update(status="pass", reference="evidence.md", observed_at="2026-09-30T08:00:00Z", summary="declaration")
        v4 = next(stage for stage in data["stages"] if stage["id"] == "V4")
        v4.update(status="blocked", product_revision="abc", schema_revision="0001", environment="isolated target", blocked_reason="release-time gates remain")
        for evidence in v4["evidence"]:
            evidence.update(status="pass" if evidence["kind"] in {"build_identity", "controlled_migration", "backup_and_isolated_restore", "compatible_rollback"} else "not_run", reference="evidence.md", observed_at="2026-09-30T08:00:00Z", summary="declaration")
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "record.json"
            record.write_text(json.dumps(data), encoding="utf-8")
            env = os.environ.copy()
            env.update(
                DOCKER_CONTEXT="reviewed-context",
                PROJECT_NAME="learner-product",
                DOMAIN="product.example.com",
                APP_IMAGE="ghcr.io/learner/product@sha256:" + "0" * 64,
                CADDY_IMAGE="library/caddy@sha256:" + "0" * 64,
                RELEASE_RECORD=str(record),
                RELEASE_APPROVAL_REFERENCE="approval-1",
                BACKUP_POLICY_REFERENCE="policy-1",
                ROLLBACK_OWNER="learner",
            )
            result = subprocess.run([str(DELIVERY / "commands/release.sh")], cwd=DELIVERY, env=env, input="\n", text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertIn("interactive approval", result.stderr)

    def test_maintenance_record_template_requires_operational_evidence_fields(self):
        fields = (DELIVERY / "templates/maintenance-record.template").read_text(encoding="utf-8")
        for field in (
            "event_type:", "owner:", "product_revision:", "schema_revision:",
            "official_sources_reviewed:", "tests_run:", "backup_id:",
            "restore_target:", "restore_validation:", "notification_delivery_evidence:",
            "rollback_compatibility:", "unresolved_risks:", "reviewed_by:",
        ):
            self.assertIn(field, fields)

    def test_private_keys_and_embedded_database_credentials_are_rejected(self):
        data = copy.deepcopy(self.template)
        data["stages"][0]["next_action"] = (
            "postgresql+psycopg://user:password@example.invalid/product"
        )
        with self.assertRaisesRegex(checker.FormatError, "possible credential"):
            checker.validate(data)


if __name__ == "__main__":
    unittest.main()
