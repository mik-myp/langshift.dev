"""Check integration-record FORMAT only; never run or approve the product.

A passing record is a learner's declaration with internally complete fields.
It does not open referenced artifacts, validate hashes, execute tests, inspect
a backend, prove redaction, award graduation, or authorize public operation.
"""
import argparse
from datetime import datetime
import json
import re
from pathlib import Path, PurePosixPath

STATUSES = {"not_run", "pass", "fail", "blocked"}
SPEC = "js2py-product-integration-v1"
STAGES = {
    "V0": {"environment_recovery", "business_tests", "failure_recovery"},
    "V1": {"http_contract", "api_tests", "real_process_requests"},
    "V2": {"empty_database_migration", "existing_data_migration", "transaction_failure_recovery", "isolated_database_tests"},
    "V3": {"identity_lifecycle", "object_authorization_negative", "revocation", "idempotency_and_retry"},
    "V3.5": {"external_failure_isolation", "cancellation_cleanup", "core_crud_regression"},
    "V4": {"build_identity", "controlled_migration", "public_https", "logs_and_delivered_alert", "backup_and_isolated_restore", "compatible_rollback", "invited_use_approval"},
    "V5": {"independent_feature", "feature_release_and_rollback", "feature_restore", "human_review"},
}
SENSITIVE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----|postgresql(?:\+psycopg)?://[^/\s:]+:[^@/\s]+@", re.I)


class FormatError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise FormatError(message)


def load(path):
    def reject_constant(value):
        raise FormatError(f"Non-JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant)


def timestamp(value, label):
    require(isinstance(value, str) and value.endswith(("Z", "+00:00")), f"{label} must be an aware UTC timestamp")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise FormatError(f"{label} is not an ISO-8601 timestamp") from None
    require(parsed.utcoffset().total_seconds() == 0, f"{label} must be UTC")


def artifact_reference(value, label):
    require(value is None or isinstance(value, str), f"{label} must be text or null")
    if value is None:
        return
    require(bool(value.strip()), f"{label} cannot be blank")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts, f"{label} must be a safe relative reference")
    require("://" not in value and not value.startswith("//"), f"{label} must reference an artifact location, not an arbitrary URL")
    require("\\" not in value and not re.match(r"^[A-Za-z]:", value), f"{label} must use portable POSIX-style path separators")


def inspect_strings(value, path="record"):
    if isinstance(value, str):
        require(not SENSITIVE.search(value), f"possible credential or private key at {path}")
    elif isinstance(value, dict):
        for key, child in value.items():
            inspect_strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            inspect_strings(child, f"{path}[{index}]")


def validate(data):
    require(isinstance(data, dict), "record must be an object")
    require(set(data) == {"schema_version", "spec_version", "product", "redaction_reviewed", "stages"}, "unknown or missing record fields")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "schema_version must be 1")
    require(data["spec_version"] == SPEC, "spec_version mismatch")
    product = data["product"]
    require(isinstance(product, dict) and set(product) == {"name", "repository", "reader"}, "product fields are invalid")
    require(all(isinstance(product[k], str) and product[k].strip() for k in product), "product fields cannot be blank")
    require(product["reader"] == "experienced frontend engineer", "this record is for the stated js2py reader")
    require(type(data["redaction_reviewed"]) is bool, "redaction_reviewed must be boolean")
    require(data["stages"] is not None and [s.get("id") for s in data["stages"]] == list(STAGES), "stages must be ordered V0..V5")
    counts = {status: 0 for status in STATUSES}
    for stage in data["stages"]:
        sid = stage.get("id")
        require(isinstance(stage, dict) and set(stage) == {"id", "title", "status", "product_revision", "schema_revision", "environment", "blocked_reason", "next_action", "evidence"}, f"{sid} fields are invalid")
        require(stage["status"] in STATUSES, f"{sid} status is invalid")
        require(isinstance(stage["title"], str) and stage["title"].strip(), f"{sid} title is required")
        require(stage["product_revision"] is None or isinstance(stage["product_revision"], str), f"{sid} product_revision is invalid")
        require(stage["schema_revision"] is None or isinstance(stage["schema_revision"], str), f"{sid} schema_revision is invalid")
        require(stage["environment"] is None or isinstance(stage["environment"], str), f"{sid} environment is invalid")
        require(stage["next_action"] is None or isinstance(stage["next_action"], str), f"{sid} next_action is invalid")
        counts[stage["status"]] += 1
        if stage["status"] in {"pass", "fail", "blocked"}:
            require(bool(stage["product_revision"]), f"{sid} needs a product revision for this status")
            require(bool(stage["environment"]), f"{sid} needs an environment for this status")
        if stage["status"] == "blocked":
            require(isinstance(stage["blocked_reason"], str) and stage["blocked_reason"].strip(), f"{sid} blocked_reason is required")
        else:
            require(stage["blocked_reason"] is None, f"{sid} blocked_reason must be null unless blocked")
        rows = stage["evidence"]
        require(isinstance(rows, list), f"{sid} evidence must be a list")
        kinds = [row.get("id") if isinstance(row, dict) and "id" in row else row.get("kind") if isinstance(row, dict) else None for row in rows]
        require(len(kinds) == len(set(kinds)), f"{sid} has duplicate evidence kinds")
        require(set(kinds) == STAGES[sid], f"{sid} evidence kinds mismatch")
        for row in rows:
            kind = row.get("kind")
            require(isinstance(row, dict) and set(row) == {"kind", "status", "reference", "observed_at", "summary"}, f"{sid}.{kind} fields are invalid")
            require(row["status"] in STATUSES, f"{sid}.{kind} status is invalid")
            artifact_reference(row["reference"], f"{sid}.{kind}.reference")
            require(row["summary"] is None or isinstance(row["summary"], str), f"{sid}.{kind}.summary is invalid")
            if row["observed_at"] is not None:
                timestamp(row["observed_at"], f"{sid}.{kind}.observed_at")
            if row["status"] in {"pass", "fail", "blocked"}:
                require(bool(row["reference"]), f"{sid}.{kind} needs a reference")
                require(bool(row["observed_at"]), f"{sid}.{kind} needs an observation time")
                require(bool(row["summary"] and row["summary"].strip()), f"{sid}.{kind} needs a summary")
        if stage["status"] == "pass":
            require(all(row["status"] == "pass" for row in rows), f"{sid} cannot pass until every declared evidence row passes")
            require(stage["schema_revision"] is not None, f"{sid} pass needs a schema revision or an explicit non-schema sentinel")
    inspect_strings(data)
    return {
        "format_valid": True,
        "backend_verified": False,
        "public_operation_verified": False,
        "redaction_claimed": data["redaction_reviewed"],
        "stage_status_counts": counts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record")
    args = parser.parse_args()
    try:
        result = validate(load(args.record))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"FORMAT FAIL: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
