#!/usr/bin/env python3
"""D04–D06 only: allowlists/locale parity + extracted-ZIP, real-PG acceptance.

No shared registration changes. Requires uv, Python 3.13.15 and PostgreSQL 18.6
binaries. Starts/stops only pg_sandbox.py's owned clusters, never services.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LABS = {
    "d04-sqlalchemy": ("getOrmExample", "module-24-sqlalchemy", 10),
    "d05-migrations": ("getMigrationExample", "module-25-migrations", 9),
    "d06-database-testing": ("getDatabaseTestingExample", "module-26-database-testing", 26),
}
FENCES = re.compile(r"^```([^\n]*)\n(.*?)^```\s*$", re.M | re.S)
FORBIDDEN = {".venv", "__pycache__", ".pytest_cache", ".env", "data", "pgdata", "node_modules"}


def env_for_run():
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("PYTHON", "PG", "LAB_")) and key not in {
               "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_ACTIVE", "UV_PYTHON",
               "UV_INDEX", "UV_DEFAULT_INDEX", "UV_INDEX_URL", "UV_EXTRA_INDEX_URL",
               "DATABASE_URL", "TEST_DATABASE_URL"}}
    if os.environ.get("PG_BIN"):
        env["PG_BIN"] = os.environ["PG_BIN"]
    env.update(PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1", UV_NO_CONFIG="1")
    return env


def archive_bytes(lab):
    source = ROOT / "examples/js2py" / lab
    names = json.loads((source.parent / f"{lab}-files.json").read_text())
    assert names == sorted(set(names)), "allowlist must be sorted and unique"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            rel = Path(name)
            assert not rel.is_absolute() and ".." not in rel.parts and not set(rel.parts) & FORBIDDEN
            assert not name.endswith((".pyc", ".log", ".sqlite", ".db"))
            path = source / rel
            assert path.is_file() and not path.is_symlink(), path
            info = zipfile.ZipInfo(f"{lab}/{name}", (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return names, output.getvalue()


def check_content(lab, names):
    loader, slug, _ = LABS[lab]
    pages = [(ROOT / "content/docs/js2py" / (slug + suffix + ".mdx")).read_text()
             for suffix in ("", ".zh-cn", ".zh-tw")]
    refs = [re.findall(rf"{loader}\('([^']+)'\)", page) for page in pages]
    assert refs[0] == refs[1] == refs[2], f"{lab}: locale source references differ"
    assert set(refs[0]) <= set(names)
    sections = [len(re.findall(r"^## ", page, re.M)) for page in pages]
    assert sections[0] == sections[1] == sections[2] and sections[0] >= 12
    fences = [FENCES.findall(page) for page in pages]
    assert fences[0] == fences[1] == fences[2], f"{lab}: code/output fences differ"
    for page in pages:
        assert page.count("<details>") >= 3 and "<details open" not in page
        assert page.count("<details>") == page.count("</details>")
        assert f"/learning-assets/js2py/{lab}.zip" in page
        assert "2026-09-28" in page and "canRun={true}" not in page
    readmes = [(ROOT / "examples/js2py" / lab / name).read_text()
               for name in ("README.md", "README.zh-cn.md", "README.zh-tw.md")]
    assert FENCES.findall(readmes[0]) == FENCES.findall(readmes[1]) == FENCES.findall(readmes[2])
    return {"lab": lab, "loader": loader, "slug": slug,
            "sections": sections[0], "refs": refs[0]}


def run_command(directory, command, env, log_path, expected=0):
    process = subprocess.Popen(command, cwd=directory, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        output, _ = process.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            output, _ = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
        log_path.write_text(output)
        raise AssertionError(f"Timed out: {command}; inspect cleanup proof and {log_path}")
    log_path.write_text(output)
    if process.returncode != expected:
        raise AssertionError(f"{command}: expected {expected}, got {process.returncode}\n{output}")
    return output


def verify_cleanup(path, expected_exit=0):
    proof = json.loads(path.read_text())
    assert proof["server_version"] == "180006", proof
    assert proof["command_exit"] == expected_exit
    assert proof["stopped"] and proof["removed"] and proof["status_after_stop"] == 3
    assert proof["tcp"] is False and not Path(proof["cluster"]).exists()
    return proof


def run_lab(lab, evidence_dir, repeats):
    _, _, expected_count = LABS[lab]
    result = {"lab": lab, "runs": [], "demos": [], "cleanup": []}
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv not found; export PATH=$HOME/.local/bin:$PATH")
    with tempfile.TemporaryDirectory(prefix="ls-dbe-") as temp:
        with zipfile.ZipFile(ROOT / f"public/learning-assets/js2py/{lab}.zip") as archive:
            for name in archive.namelist():
                rel = Path(name)
                assert not rel.is_absolute() and ".." not in rel.parts
                assert rel.parts[0] == lab
            archive.extractall(temp)
        directory = Path(temp) / lab
        env = env_for_run()
        run_command(directory, [uv, "sync", "--locked"], env, evidence_dir / f"{lab}-install.log")
        versions = run_command(directory, [uv, "run", "--locked", "python", "-c", """
import platform, json
from importlib.metadata import version
print(json.dumps({'python': platform.python_version(), **{p: version(p) for p in
['SQLAlchemy','alembic','psycopg','fastapi','uvicorn','pydantic','httpx','starlette','anyio','pytest']}}))
"""], env, evidence_dir / f"{lab}-versions.json")
        result["versions"] = json.loads(versions)
        assert result["versions"] == {"python": "3.13.15", "SQLAlchemy": "2.0.54", "alembic": "1.20.0",
            "psycopg": "3.3.6", "fastapi": "0.135.1", "uvicorn": "0.42.0", "pydantic": "2.12.5",
            "httpx": "0.28.1", "starlette": "0.52.1", "anyio": "4.12.1", "pytest": "8.4.2"}
        def sandbox(tag, child, expected=0, extras=None):
            proof = evidence_dir / f"{lab}-{tag}-cleanup.json"
            output = run_command(directory, [uv, "run", "--locked", "python", "pg_sandbox.py",
                         "--evidence", str(proof), "--", *child], env | (extras or {}),
                         evidence_dir / f"{lab}-{tag}.log", expected)
            result["cleanup"].append(verify_cleanup(proof, expected))
            return output
        for repetition in range(1, repeats + 1):
            xml = evidence_dir / f"{lab}-pytest-{repetition}.xml"
            plan = evidence_dir / f"{lab}-plan-{repetition}.json"
            sandbox(f"pytest-{repetition}", ["python", "-m", "pytest", "-q", f"--junitxml={xml}"],
                    extras={"LAB_PLAN_EVIDENCE": str(plan)})
            suites = ET.parse(xml).getroot()
            tests = list(suites.iter("testcase"))
            assert len(tests) == expected_count
            assert all(case.find("failure") is None and case.find("error") is None
                       and case.find("skipped") is None for case in tests)
            result["runs"].append({"tests": len(tests), "failures": 0,
                                   "junit": str(xml), "repeat": repetition})
            if lab == "d06-database-testing":
                report = json.loads(plan.read_text())
                assert report["rows_seeded"] == 60000 and report["returned"] == 20
                result.setdefault("plans", []).append(str(plan))
        demos = {
            "d04-sqlalchemy": [("demo.py", "projects after failure: 0"),
                               ("commit_failure.py", "rollback restored Session"),
                               ("http_smoke.py", "loopback HTTP: 201 then 409 then 200")],
            "d05-migrations": [("history_demo.py", "refused downgrade left revision and data unchanged")],
            "d06-database-testing": [("query_plan.py", "same result rows: 20"),
                                     ("commit_failure.py", "rollback restored Session")],
        }[lab]
        for index, (script, expected_text) in enumerate(demos):
            output = sandbox(f"demo-{index}", ["python", script])
            assert expected_text in output
            result["demos"].append({"script": script, "passed": True})
        # Explicitly prove nonzero child exit still stops/removes the owned cluster.
        sandbox("child-failure", ["python", "-c", "raise SystemExit(7)"], expected=7)
        # No sandbox: refuse ordinary test invocation rather than skip or use another DB.
        guard = run_command(directory, [uv, "run", "--locked", "python", "-c",
                            "from safety import checked_url; checked_url()"], env,
                            evidence_dir / f"{lab}-no-sandbox-refusal.log", expected=1)
        assert "Refusing database access" in guard
        if lab == "d05-migrations":
            output = sandbox("cli", ["bash", "-c", "set -e; python -m alembic upgrade head; "
                             "python -m alembic current; python -m alembic history --verbose; "
                             "python -m alembic check; python -m alembic upgrade head --sql"])
            assert "003_contract" in output and "CREATE TABLE tasks" in output
            result["cli_upgrade_current_history_check_offline_sql"] = True
    result["extracted_directory_removed"] = not Path(temp).exists()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="Rebuild only these three owned ZIPs before checking")
    parser.add_argument("--check-only", action="store_true", help="Source/locale/archive checks; NOT database verification")
    parser.add_argument("--lab", choices=list(LABS))
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--evidence-dir", type=Path, default=Path("/tmp/langshift-d04-d06-verification"))
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    evidence = args.evidence_dir.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    summary = {"date": "2026-09-28", "mode": "source-only" if args.check_only else "real-postgresql",
               "metadata": [], "archives": [], "verification": []}
    for lab in [args.lab] if args.lab else LABS:
        names, expected = archive_bytes(lab)
        archive = ROOT / f"public/learning-assets/js2py/{lab}.zip"
        if args.build:
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive.write_bytes(expected)
        assert archive.read_bytes() == expected, f"Stale archive: {archive}; run with --build"
        summary["metadata"].append(check_content(lab, names))
        summary["archives"].append({"lab": lab, "files": len(names), "path": str(archive),
                                     "sha256": hashlib.sha256(expected).hexdigest()})
        if not args.check_only:
            summary["verification"].append(run_lab(lab, evidence, args.repeats))
        print(f"{lab}: source/locale/ZIP OK" + ("; real PostgreSQL PASS" if not args.check_only else ""))
    (evidence / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("Evidence:", evidence / "summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
