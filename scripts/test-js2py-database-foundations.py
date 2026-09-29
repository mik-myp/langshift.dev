#!/usr/bin/env python3
"""Verify ONLY D01-D03 from allowlisted archives on exclusively owned PostgreSQL.

No shared registration is required or modified. Output goes under /tmp, never into
public/. Every new cluster is stopped in finally; data/logs remain for evidence.
Requires the baseline uv and preinstalled PostgreSQL binaries; installs no system
software. This executes SQL, not merely syntax/MDX compilation.
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
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROWS = [
    {"lab": "d01-relational-data", "loader": "getRelationalExample", "slug": "module-21-relational-data", "tests": 64},
    {"lab": "d02-sql", "loader": "getSqlExample", "slug": "module-22-sql", "tests": 66},
    {"lab": "d03-transactions", "loader": "getTransactionExample", "slug": "module-23-transactions", "tests": 63},
]
EXPECTED_DEMO = {
    "d02-sql": '''todo [(1, 'Design API', 'todo', 30), (4, 'Read SQL', 'todo', 20)]
page [(3, 'Ship demo', 'done', 15), (4, 'Read SQL', 'todo', 20)]
totals [('Launch', 3, 90), ('Docs', 2, 60), ('Empty', 0, 0)]
unmatched payload []
literal stored [(6, "x' OR TRUE --")]
updated (6, 'doing')
deleted (6,)
tasks remaining 5
''',
    "d03-transactions": '''failed_second_step {"memberships": 4, "projects_remaining": 0, "sqlstate": "23503"}
read_committed [30, 40]
repeatable_read [30, 30]
lost_update 37
atomic_increment {"lock_wait_observed": true, "value": 42, "worker": "committed"}
unique_race {"lock_wait_observed": true, "value": 1, "worker": "23505"}
lock_timeout {"minutes_after_rollback": 30, "sqlstate": "55P03"}
serialization_conflict {"after_full_retry": 42, "sqlstate": "40001"}
''',
}


def static_and_archive(row, output):
    lab = row["lab"]
    base = ROOT / "examples/js2py" / lab
    names = json.loads((base.parent / (lab + "-files.json")).read_text())
    assert names == sorted(set(names))
    assert names == json.loads((base / "FILES.json").read_text())
    forbidden = {".venv", "__pycache__", ".pytest_cache", ".lab-state.json", ".env", "postmaster.pid", "PG_VERSION"}
    for name in names:
        p = Path(name)
        assert not p.is_absolute() and ".." not in p.parts
        assert not forbidden.intersection(p.parts), name
        assert (base / p).is_file() and not (base / p).is_symlink(), name
    contract = json.loads((base / "model-contract.json").read_text())
    assert contract["ddl_sha256"] == hashlib.sha256((base / "sql/schema.sql").read_bytes()).hexdigest()
    assert 'registry = "https://pypi.org/simple"' in (base / "uv.lock").read_text()
    refs, fences, sections = [], [], []
    for suffix in ["", ".zh-cn", ".zh-tw"]:
        text = (ROOT / "content/docs/js2py" / (row["slug"] + suffix + ".mdx")).read_text()
        current = re.findall(row["loader"] + r"\('([^']+)'\)", text)
        assert current and all(ref in names for ref in current)
        assert text.count("<details>") >= 3
        assert text.count("<details>") == text.count("</details>")
        assert 'open=' not in text and '<details open' not in text
        assert f"/learning-assets/js2py/{lab}.zip" in text
        assert "2026-09-28" in text and "18.6" in text
        refs.append(current)
        fences.append(re.findall(r"```[^\n]*\n[\s\S]*?```", text))
        sections.append(len(re.findall(r"^## ", text, re.M)))
    assert refs[0] == refs[1] == refs[2], "source parity"
    assert fences[0] == fences[1] == fences[2], "code/output parity"
    assert sections[0] == sections[1] == sections[2]
    readme_fences = [re.findall(r"```[^\n]*\n[\s\S]*?```", (base / file).read_text())
                     for file in ["README.md", "README.zh-cn.md", "README.zh-tw.md"]]
    assert readme_fences[0] == readme_fences[1] == readme_fences[2]
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:
            info = zipfile.ZipInfo(f"{lab}/{name}", (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (base / name).read_bytes())
    archive = output / (lab + ".zip")
    archive.write_bytes(data.getvalue())
    with zipfile.ZipFile(archive) as z:
        assert z.namelist() == [f"{lab}/{name}" for name in names]
        for name in names:
            assert z.read(f"{lab}/{name}") == (base / name).read_bytes()
        z.extractall(output / "extracted")  # Every member was validated above.
    return {k: row[k] for k in ["lab", "loader", "slug"]} | {
        "sections": sections[0], "refs": refs[0],
    }, archive


def isolated_environment(source):
    retained = {key: source[key] for key in ("UV_PYTHON_INSTALL_DIR", "UV_CACHE_DIR", "PG_BIN") if key in source}
    env = {key: value for key, value in source.items()
           if not key.startswith(("UV_", "PG", "PYTHON", "PYTEST", "PIP_", "CONDA_", "UVICORN_"))
           and key not in {"VIRTUAL_ENV", "DATABASE_URL", "__PYVENV_LAUNCHER__"}}
    env.update(retained)
    env.update(PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1", UV_NO_CONFIG="1",
               UV_DEFAULT_INDEX="https://pypi.org/simple", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               DATABASE_URL="postgresql://127.0.0.1:1/do_not_connect",
               PGHOST="/nonexistent/langshift-test-ignore-environment")
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", choices=[row["lab"] for row in ROWS])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = (args.output or Path(tempfile.mkdtemp(prefix="langshift-db-acceptance-", dir="/tmp"))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "extracted").exists():
        parser.error("Use a fresh output directory; never overwrite another run")
    env = isolated_environment(os.environ)
    uv = shutil.which("uv")
    if not uv:
        parser.error('uv missing; export PATH="$HOME/.local/bin:$PATH"')
    records, metadata = [], []

    def run(cwd, *args):
        result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, timeout=180)
        records.append({"cwd": str(cwd), "command": list(args), "returncode": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
        (output / "commands.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
        if result.returncode:
            raise AssertionError((args, result.returncode, result.stdout, result.stderr))
        return result

    results = []
    for row in ROWS:
        if args.lab and row["lab"] != args.lab:
            continue
        item, archive = static_and_archive(row, output)
        metadata.append(item)
        cwd = output / "extracted" / row["lab"]
        before = (cwd / "uv.lock").read_bytes()
        run(cwd, uv, "sync", "--locked")
        assert before == (cwd / "uv.lock").read_bytes()
        def python(*args):
            return run(cwd, uv, "run", "--locked", "python", *args)
        try:
            python("labctl.py", "start")
            python("labctl.py", "reset", "--yes-reset")
            fingerprint = json.loads(python("-c", '''import sys,json,psycopg,pytest,labctl
with labctl.connect(autocommit=True) as c:
 row=c.execute("SELECT current_setting('server_version'),current_setting('listen_addresses'),current_database(),current_user").fetchone()
 print(json.dumps({"python":sys.version.split()[0],"psycopg":psycopg.__version__,"pytest":pytest.__version__,"server":row,"version_num":c.info.server_version}))
''').stdout)
            assert fingerprint["python"] == "3.13.15"
            assert fingerprint["psycopg"] == "3.3.6" and fingerprint["pytest"] == "8.4.2"
            assert fingerprint["version_num"] == 180006 and fingerprint["server"][1] == ""
            # Safety check: a mismatched marker must refuse SQL without damaging anything.
            python("-c", '''import labctl
from pathlib import Path
s=labctl.load_state(); p=Path(s['root'])/labctl.MARKER; original=p.read_text()
try:
 p.write_text('{}')
 try: labctl.reset()
 except RuntimeError as e: assert 'marker mismatch' in str(e)
 else: raise AssertionError('reset accepted a tampered marker')
finally: p.write_text(original)
with labctl.connect(autocommit=True) as c: assert c.execute('SELECT count(*) FROM tasks').fetchone()==(5,)
print('tampered ownership refused; data unchanged')
''')
            for repeat in range(2):
                result = run(cwd, uv, "run", "--locked", "pytest", "-q")
                assert f"{row['tests']} passed" in result.stdout
                print(row["lab"], f"pass {repeat + 1}:", result.stdout.strip().splitlines()[-1], flush=True)
            python("labctl.py", "reset", "--yes-reset")
            if row["lab"] in EXPECTED_DEMO:
                assert python("demo.py").stdout == EXPECTED_DEMO[row["lab"]]
            if row["lab"] == "d01-relational-data":
                python("labctl.py", "psql", "--file", "sql/inspect.sql")
                result = python("labctl.py", "psql", "--file", "sql/expected_failures.sql")
                assert re.findall(r"ERROR:\s+(\d{5})", result.stderr) == ["23505", "23503", "23514", "23502"]
            elif row["lab"] == "d02-sql":
                python("labctl.py", "reset", "--yes-reset")
                result = python("labctl.py", "psql", "--file", "sql/queries.sql")
                assert "Empty" in result.stdout and "Design API" in result.stdout and "75" in result.stdout
            else:
                result = python("labctl.py", "psql", "--file", "sql/failed_transaction.sql")
                assert re.findall(r"ERROR:\s+(\w{5})", result.stderr) == ["23503", "25P02"]
                assert re.search(r"broken_remaining\s*\n-+\s*\n\s*0", result.stdout)
                assert re.search(r"connection_recovered\s*\n-+\s*\n\s*1", result.stdout)
            python("-c", "import labctl\nwith labctl.connect(autocommit=True) as c: c.execute(\"INSERT INTO users(login) VALUES ('restart_marker')\")")
            python("labctl.py", "stop")
            stopped = json.loads(python("labctl.py", "status").stdout)
            assert not stopped["running"] and stopped["pg_ctl_status"] == 3
            python("labctl.py", "start")
            python("-c", "import labctl\nwith labctl.connect(autocommit=True) as c: assert c.execute(\"SELECT count(*) FROM users WHERE login='restart_marker'\").fetchone()==(1,)\nprint('committed data survived stop/start')")
            results.append({"lab": row["lab"], "pytest_cases": row["tests"], "pytest_runs": 2,
                            "fingerprint": fingerprint, "archive": str(archive),
                            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                            "ownership_refusal": "passed", "normal_restart_persistence": "passed"})
        finally:
            if (cwd / ".lab-state.json").exists():
                python("labctl.py", "stop")
                cleanup = json.loads(python("labctl.py", "status").stdout)
                assert not cleanup["running"] and cleanup["pg_ctl_status"] == 3
                assert not (Path(cleanup["root"]) / "data/postmaster.pid").exists()
                if results and results[-1]["lab"] == row["lab"]:
                    results[-1]["cleanup"] = cleanup | {"postmaster_pid_exists": False, "data_retained": True}
    assert len({x["cleanup"]["root"] for x in results}) == len(results)
    report = {"checked_at": "2026-09-28", "metadata": metadata, "results": results,
              "commands": str(output / "commands.json"), "output": str(output),
              "scope": "Only D01-D03; real PostgreSQL, no public artifact/loader registration changes"}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
