"""Unit tests for fictional materials only; never an application acceptance suite."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from check_evidence import BASE, FormatError, check_catalog, read_json, validate


class MaterialFormatTests(unittest.TestCase):
    def setUp(self):
        self.data = read_json(BASE / "templates/evidence.json")
        self.ids = check_catalog()

    def test_unrun_template_is_valid_without_graduation(self):
        result = validate(self.data, self.ids)
        self.assertEqual(result["scenario_status_counts"]["not_run"], 24)
        for flag in ["backend_verified", "graduation_awarded", "public_operation_verified", "artifact_files_verified"]:
            self.assertFalse(result[flag])

    def test_four_claims_cannot_collapse_into_one(self):
        del self.data["claims"]["public_operation"]
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_missing_case(self):
        self.data["scenarios"].pop()
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_duplicate_case(self):
        self.data["scenarios"][-1] = copy.deepcopy(self.data["scenarios"][0])
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_pass_without_reference(self):
        self.data["scenarios"][0]["status"] = "pass"
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_unknown_reference(self):
        self.data["scenarios"][0]["evidence_refs"] = ["missing"]
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_blocked_requires_reason_not_fake_execution(self):
        case = self.data["scenarios"][0]
        case["status"] = "blocked"
        with self.assertRaises(FormatError): validate(self.data, self.ids)
        case["notes"] = "No approved deployment target."
        self.assertTrue(validate(self.data, self.ids)["format_valid"])

    def test_no_observation_time_for_not_run(self):
        self.data["scenarios"][0]["observed_at"] = "2026-09-28T09:00:00+00:00"
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_bool_is_not_version(self):
        self.data["schema_version"] = True
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_path_traversal_absolute_and_url_rejected(self):
        for path in ["../secret.txt", "/private/secret.txt", "https://example.invalid/log", "..\\secret.txt"]:
            with self.subTest(path=path):
                self.data["artifacts"] = [{"id":"a","path":path,"sha256":"0"*64,"description":"Fictional fixture"}]
                with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_fiction_can_pass_format_but_never_verify_backend(self):
        # Intentionally fictional IN MEMORY: this is the checker's limitation test,
        # not a saved successful student run or evidence that a log exists.
        self.data["project_revision"] = "fictional-unit-test-revision"
        self.data["environment"] = {"label":"fiction","isolation":"fiction","baseline":None}
        self.data["artifacts"] = [{"id":"fiction","path":"fiction/not-a-real-log.txt","sha256":"0"*64,"description":"Does not exist"}]
        case = self.data["scenarios"][0]
        case.update(status="pass", observed_at="2026-09-28T09:00:00+00:00", evidence_refs=["fiction"])
        result = validate(self.data, self.ids)
        self.assertTrue(result["format_valid"])
        self.assertFalse(result["artifact_files_verified"])
        self.assertFalse(result["backend_verified"])
        self.assertFalse(result["graduation_awarded"])
        case["observed_at"] = "2026-09-28T09:00:00"
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_recovery_measurements_cannot_be_negative(self):
        self.data["operations"]["measured_rto_seconds"] = -1
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_pilot_claim_count_boundary(self):
        self.data["operations"].update(pilot_status="pass", invited_testers=0)
        with self.assertRaises(FormatError): validate(self.data, self.ids)

    def test_catalog_dangling_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "materials"
            for name in ["requirements.json", "scenarios.json", "rubric.json", "fixtures/actors-and-data.json"]:
                target = dest / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(BASE / name, target)
            fixtures = read_json(dest / "fixtures/actors-and-data.json")
            fixtures["comments"][0]["task"] = "missing"
            (dest / "fixtures/actors-and-data.json").write_text(json.dumps(fixtures))
            with self.assertRaises(FormatError): check_catalog(dest)

    def test_cli_malformed_and_empty_data_fail_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            for body in ["{", "{}", "null", '{"schema_version": NaN}']:
                with self.subTest(body=body):
                    path.write_text(body)
                    result = subprocess.run([sys.executable, str(BASE / "check_evidence.py"), str(path)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 1)
                    self.assertFalse(json.loads(result.stdout)["format_valid"])
                    self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
