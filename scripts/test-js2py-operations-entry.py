#!/usr/bin/env python3
"""O01–O03 own entry check. Never builds ZIPs, edits registries, or contacts Docker.

Default: validate allowlists/locales, restore a fresh copy, run POSIX/local HTTP/TLS
and independent tests. Container/systemd/Caddy/public gates remain pending.
--static-only is explicitly NOT runtime acceptance. Reports contain no credentials.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ROWS = [
    ("o01-operating-system", "getOperatingSystemExample", "module-32-operating-system",
     16, 1, "solutions/test_two_directories.py",
     ["process_lab.py", "environment_lab.py", "permissions_lab.py", "port_lab.py"]),
    ("o02-containers", "getContainerOpsExample", "module-33-containers",
     14, 3, "solutions/test_restore_copy.py",
     ["check_config.py", "local_probe.py", "secret_demo.py", "container_probe.py"]),
    ("o03-https-production", "getHttpsExample", "module-34-https-production",
     17, 7, "solutions/test_origin_policy.py",
     ["tls_lab.py", "check_config.py"]),
]


def fence_blocks(text):
    return re.findall(r"```[^\n]*\n[\s\S]*?```", text)


def audit(lab, loader, slug):
    directory = ROOT / "examples/js2py" / lab
    names = json.loads((directory.parent / f"{lab}-files.json").read_text())
    assert len(names) == len(set(names)), "duplicate manifest entry"
    assert (directory / ".python-version").read_text().strip() == "3.13.15"
    assert 'requires-python = ">=3.13,<3.14"' in (directory / "pyproject.toml").read_text()
    hashes = {}
    for name in names:
        path = Path(name)
        assert not path.is_absolute() and ".." not in path.parts
        assert not any(part in {".venv", "__pycache__", ".pytest_cache", ".git", ".env"} for part in path.parts)
        assert path.suffix not in {".key", ".pem", ".crt", ".pyc", ".zip"}
        source = directory / path
        assert source.is_file() and not source.is_symlink(), name
        text = source.read_text()
        assert not re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text)
        hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    snapshots = []
    for suffix in ("", ".zh-cn", ".zh-tw"):
        text = (ROOT / "content/docs/js2py" / f"{slug}{suffix}.mdx").read_text()
        refs = re.findall(rf"{loader}\('([^']+)'\)", text)
        assert refs and all(ref in names for ref in refs)
        assert text.count("<details>") >= 3
        assert text.count("<details>") == text.count("</details>")
        assert f"/learning-assets/js2py/{lab}.zip" in text
        assert "2026-09-28" in text and "environment_pending" in text
        snapshots.append((len(re.findall(r"^## ", text, re.M)), refs, fence_blocks(text)))
    assert snapshots[0] == snapshots[1] == snapshots[2], f"locale drift: {lab}"
    readmes = [fence_blocks((directory / f"README{suffix}.md").read_text())
               for suffix in ("", ".zh-cn", ".zh-tw")]
    assert readmes[0] == readmes[1] == readmes[2], f"README command drift: {lab}"
    environment = json.loads((directory / "ENVIRONMENT.json").read_text())
    assert environment["environment_status"] == "environment_pending"
    assert environment["actually_run"] and environment["unavailable_here"] and environment["user_must_supply"]
    sources = json.loads((directory / "SOURCES.json").read_text())
    assert all(row["verified_date"] == "2026-09-28" and row["http_status"] == 200 for row in sources)
    return {"lab": lab, "loader": loader, "slug": slug, "sections": snapshots[0][0],
            "refs": snapshots[0][1], "manifest_count": len(names), "source_sha256": hashes,
            "environment_matrix": environment}, names


def isolated_environment(source):
    """Keep only explicit uv install/cache directories from uv ambient settings.

    Each clean copy owns its .venv; caller active/project interpreters, env-file
    loading, resolver switches and external pytest/Python injection must not win.
    Do not print the caller environment or its values.
    """
    env = dict(source)
    retained = {key: env[key] for key in ("UV_PYTHON_INSTALL_DIR", "UV_CACHE_DIR") if key in env}
    prefixes = ("UV_", "PYTHON", "PYTEST", "PIP_", "VIRTUAL_ENV", "CONDA_", "_CE_", "TOX_", "HATCH_", "POETRY_")
    for key in list(env):
        if key.startswith(prefixes) or key in {"__PYVENV_LAUNCHER__", "PY_PYTHON", "PY_PYTHON3"}:
            del env[key]
    env.update(retained)
    env.update({"UV_DEFAULT_INDEX": "https://pypi.org/simple", "UV_NO_CONFIG": "1",
                "UV_PYTHON_PREFERENCE": "only-managed", "PYTHONNOUSERSITE": "1",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
    return env


def check_environment_isolation():
    supplied = {"PATH": "/fictional/bin", "UV_PYTHON_INSTALL_DIR": "/fictional/install",
                "UV_CACHE_DIR": "/fictional/cache", "UV_PROJECT_ENVIRONMENT": "/fictional/other-project",
                "UV_ACTIVE": "1", "UV_PYTHON": "/fictional/python", "UV_WORKING_DIRECTORY": "/fictional/project",
                "UV_ENV_FILE": "/fictional/environment", "VIRTUAL_ENV": "/fictional/venv",
                "PYTHONPATH": "/fictional/modules", "PYTHONHOME": "/fictional/home",
                "PYTEST_ADDOPTS": "--not-a-real-option", "PYTEST_PLUGINS": "not_a_real_plugin"}
    result = isolated_environment(supplied)
    for key in ("UV_PROJECT_ENVIRONMENT", "UV_ACTIVE", "UV_PYTHON", "UV_WORKING_DIRECTORY",
                "UV_ENV_FILE", "VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME", "PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        assert key not in result
    assert result["UV_PYTHON_INSTALL_DIR"] == supplied["UV_PYTHON_INSTALL_DIR"]
    assert result["UV_CACHE_DIR"] == supplied["UV_CACHE_DIR"]
    assert result["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert supplied["UV_ACTIVE"] == "1", "do not mutate parent mapping"


def execute(args, directory, env, expected=0, timeout=120):
    result = subprocess.run(args, cwd=directory, env=env, text=True,
                            capture_output=True, timeout=timeout)
    print(f"$ {' '.join(args)}\n{result.stdout}", end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", flush=True)
    assert result.returncode == expected, f"exit {result.returncode}, expected {expected}"
    return {"argv": args, "cwd": str(directory), "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = {"verified_date": "2026-09-28", "mode": "static-only" if args.static_only else "clean-copy-runtime",
              "rows": [], "commands": [], "total_tests": 0,
              "environment_status": "environment_pending",
              "did_not_run": ["Docker/other container engine", "systemd", "Caddy", "public DNS/CA", "actual browser integration", "TypeSafe", "ZIP or shared integration"]}
    uv = shutil.which("uv")
    check_environment_isolation()
    env = isolated_environment(os.environ)
    report["ambient_environment_isolation_checked"] = True
    if not args.static_only:
        assert uv, "uv required"
        assert os.name == "posix" and os.geteuid() != 0, "ordinary POSIX account required"
        version = execute([uv, "--version"], ROOT, env)
        assert version["stdout"].startswith("uv 0.12.13 ")
        report["commands"].append(version)
    with tempfile.TemporaryDirectory(prefix="langshift-o01-o03-clean-", dir="/tmp") as temp:
        for lab, loader, slug, standard, independent, solution, probes in ROWS:
            row, names = audit(lab, loader, slug)
            report["rows"].append(row)
            if args.static_only:
                continue
            target = Path(temp) / lab
            for name in names:
                dest = target / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / "examples/js2py" / lab / name, dest)
            clean_env = env | {"UV_PROJECT_ENVIRONMENT": str(target / ".venv")}
            commands = report["commands"]
            commands.append(execute([uv, "sync", "--locked", "--default-index", "https://pypi.org/simple"], target, clean_env))
            commands.append(execute([uv, "run", "--locked", "python", "--version"], target, clean_env))
            assert commands[-1]["stdout"].strip() == "Python 3.13.15"
            for tests, expected_cases in (("tests", standard), (solution, independent)):
                item = execute([uv, "run", "--locked", "python", "-m", "pytest", "-q", tests], target, clean_env)
                assert re.search(rf"\b{expected_cases} passed\b", item["stdout"]), "case count mismatch"
                commands.append(item)
                report["total_tests"] += expected_cases
            for probe in probes:
                commands.append(execute([uv, "run", "--locked", "python", probe], target, clean_env,
                                        expected=77 if probe == "container_probe.py" else 0))
            if lab == "o01-operating-system":
                commands.append(execute([uv, "run", "--locked", "python", "-m", "solutions.two_directories"], target, clean_env))
            # Runtime in clean copies must not edit canonical source or manifest inputs.
            for name, digest in row["source_sha256"].items():
                assert hashlib.sha256((ROOT / "examples/js2py" / lab / name).read_bytes()).hexdigest() == digest
    report["owned_clean_copies_removed"] = True
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"mode": report["mode"], "total_tests": report["total_tests"],
                      "environment_status": report["environment_status"]}))


if __name__ == "__main__":
    main()
