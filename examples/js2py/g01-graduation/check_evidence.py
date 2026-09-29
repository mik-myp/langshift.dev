"""Check catalog/material FORMAT only. Never connect to or verify a backend.

Artifact paths/hashes are syntactically checked but files are NOT opened and
claims are NOT authenticated. A well-formed fictional report can pass. Exit 0
means format acceptance, never graduation, release approval or operational safety.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import re

BASE = Path(__file__).resolve().parent
CLAIMS = {"course_content", "author_reference_validation", "student_graduation", "public_operation"}
STATUSES = {"not_run", "pass", "fail", "blocked"}


class FormatError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise FormatError(message)


def read_json(path):
    def bad_constant(value):
        raise FormatError(f"Non-JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=bad_constant)


def check_catalog(base=BASE):
    requirements = read_json(base / "requirements.json")
    catalog = read_json(base / "scenarios.json")
    fixtures = read_json(base / "fixtures/actors-and-data.json")
    rubric = read_json(base / "rubric.json")
    require(requirements["spec_version"] == catalog["spec_version"] == "g01-comments-v1", "spec version mismatch")
    scenarios = catalog["scenarios"]
    ids = [s["id"] for s in scenarios]
    require(ids == [f"S{i:02}" for i in range(1, 25)], "catalog must contain ordered S01..S24 exactly once")
    for scenario in scenarios:
        for key in ["area", "name", "given", "action", "expected", "required_observation"]:
            require(isinstance(scenario[key], str) and bool(scenario[key]), f"missing scenario {key}")
        require(type(scenario["hard_gate"]) is bool, "hard_gate must be boolean")
    actors = {a["id"] for a in fixtures["actors"]}
    projects = {p["id"] for p in fixtures["projects"]}
    tasks = {t["id"] for t in fixtures["tasks"]}
    for group in ["actors", "projects", "tasks", "comments"]:
        values = [r["id"] for r in fixtures[group]]
        require(len(values) == len(set(values)), f"duplicate fixture {group}")
    for project in fixtures["projects"]:
        require(project["owner"] in actors, "fixture project owner missing")
    for member in fixtures["memberships"] + fixtures["removed_memberships"]:
        require(member["project"] in projects and member["actor"] in actors, "fixture membership dangling")
    for task in fixtures["tasks"]:
        require(task["project"] in projects, "fixture task project missing")
    for comment in fixtures["comments"]:
        require(comment["task"] in tasks and comment["author"] in actors, "fixture comment dangling")
    require(sum(d["points"] for d in rubric["dimensions"]) == rubric["total"] == 100, "rubric total must be 100")
    require(rubric["kind"] == "human-review-only", "rubric cannot award graduation automatically")
    return ids


def validate(data, expected_ids):
    require(isinstance(data, dict), "evidence must be an object")
    keys = {"schema_version", "spec_version", "project_revision", "environment", "claims", "scenarios", "artifacts", "decisions", "operations", "checkpoint"}
    require(set(data) == keys, "missing or unknown evidence fields")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "schema_version must be integer 1")
    require(data["spec_version"] == "g01-comments-v1", "wrong spec version")
    require(data["project_revision"] is None or isinstance(data["project_revision"], str), "invalid project revision")
    environment = data["environment"]
    require(isinstance(environment, dict) and set(environment) == {"label", "isolation", "baseline"}, "environment fields")
    require(all(isinstance(environment[k], str) and environment[k] for k in ["label", "isolation"]), "environment text required")
    require(environment["baseline"] is None or isinstance(environment["baseline"], str), "baseline must be text or null")
    require(isinstance(data["artifacts"], list), "artifacts must be a list")
    artifact_ids = set()
    for artifact in data["artifacts"]:
        require(isinstance(artifact, dict) and set(artifact) == {"id", "path", "sha256", "description"}, "artifact fields")
        require(isinstance(artifact["id"], str) and bool(artifact["id"]) and artifact["id"] not in artifact_ids, "duplicate/empty artifact ID")
        artifact_ids.add(artifact["id"])
        name = artifact["path"]
        require(isinstance(name, str) and name and "\\" not in name and ":" not in name, "artifact path must be a relative POSIX path")
        path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts and name != ".", "unsafe artifact path")
        require(isinstance(artifact["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]), "invalid SHA256 syntax")
        require(isinstance(artifact["description"], str) and bool(artifact["description"]), "artifact description missing")

    def refs(value):
        require(isinstance(value, list) and all(isinstance(x, str) for x in value), "evidence_refs must be string list")
        require(len(value) == len(set(value)) and set(value) <= artifact_ids, "unknown/duplicate artifact reference")

    require(isinstance(data["claims"], dict) and set(data["claims"]) == CLAIMS, "four separate claims are required")
    for claim in data["claims"].values():
        require(isinstance(claim, dict) and set(claim) == {"status", "evidence_refs"}, "claim fields")
        require(claim["status"] in {"not_assessed", "partial", "claimed_complete"}, "unknown claim status")
        refs(claim["evidence_refs"])
        if claim["status"] == "claimed_complete":
            require(bool(claim["evidence_refs"]), "completion claim needs a reference, not an automatic verdict")
    require(isinstance(data["scenarios"], list), "scenarios must be list")
    ids = []
    counts = {s: 0 for s in sorted(STATUSES)}
    for scenario in data["scenarios"]:
        require(isinstance(scenario, dict) and set(scenario) == {"id", "status", "observed_at", "evidence_refs", "notes"}, "scenario report fields")
        ids.append(scenario["id"])
        status = scenario["status"]
        require(status in STATUSES, "unknown scenario status")
        counts[status] += 1
        refs(scenario["evidence_refs"])
        require(isinstance(scenario["notes"], str), "notes must be text")
        if status in {"pass", "fail"}:
            require(bool(scenario["evidence_refs"]), "executed scenario needs artifact reference")
            require(bool(data["project_revision"]), "executed scenario needs project revision")
            require(environment["label"] != "not_recorded" and environment["isolation"] != "not_recorded", "executed scenario needs environment identity")
            require(isinstance(scenario["observed_at"], str), "executed scenario needs time")
            try:
                stamp = datetime.fromisoformat(scenario["observed_at"])
            except ValueError as error:
                raise FormatError("invalid observation timestamp") from error
            require(stamp.tzinfo is not None, "observation timestamp requires timezone")
        else:
            require(scenario["observed_at"] is None, "unexecuted case must not claim observation time")
            if status == "blocked":
                require(bool(scenario["notes"].strip()), "blocked needs a reason")
    require(sorted(ids) == sorted(expected_ids) and len(ids) == len(set(ids)), "missing/extra/duplicate scenario reports")
    require(isinstance(data["decisions"], list) and all(isinstance(x, str) for x in data["decisions"]), "decisions must be text list")
    operations = data["operations"]
    require(isinstance(operations, dict) and set(operations) == {"release_revision", "schema_revision", "rollback_result", "restore_result", "measured_rto_seconds", "measured_rpo_seconds", "pilot_status", "invited_testers"}, "operation fields")
    for key in ["rollback_result", "restore_result", "pilot_status"]:
        require(operations[key] in STATUSES, "invalid operations status")
    for key in ["measured_rto_seconds", "measured_rpo_seconds"]:
        require(operations[key] is None or (type(operations[key]) in {int, float} and operations[key] >= 0), "invalid recovery measurement")
    for key in ["release_revision", "schema_revision"]:
        require(operations[key] is None or isinstance(operations[key], str), "invalid operation revision")
    require(type(operations["invited_testers"]) is int and operations["invited_testers"] >= 0, "invalid tester count")
    if operations["pilot_status"] == "pass":
        require(2 <= operations["invited_testers"] <= 5, "claimed pilot count must be 2..5")
    checkpoint = data["checkpoint"]
    require(isinstance(checkpoint, dict) and set(checkpoint) == {"last_verified_fact", "unresolved", "next_evidence_to_collect", "stopped_resources"}, "checkpoint fields")
    for key in ["last_verified_fact", "next_evidence_to_collect"]:
        require(isinstance(checkpoint[key], str), "checkpoint text required")
    for key in ["unresolved", "stopped_resources"]:
        require(isinstance(checkpoint[key], list) and all(isinstance(x, str) for x in checkpoint[key]), "checkpoint list required")
    return {"format_valid": True, "backend_verified": False, "graduation_awarded": False,
            "public_operation_verified": False, "artifact_files_verified": False,
            "scenario_status_counts": counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", nargs="?", type=Path, default=BASE / "templates/evidence.json")
    args = parser.parse_args()
    try:
        result = validate(read_json(args.evidence), check_catalog())
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"format_valid": False, "backend_verified": False,
                          "graduation_awarded": False, "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
