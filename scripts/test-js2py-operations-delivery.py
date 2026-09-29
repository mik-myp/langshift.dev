#!/usr/bin/env python3
"""Only O04-O06: clean allowlist copies, real owned PG18.6 and loopback processes.
Does not register shared builds, run GitHub Actions, Docker, systemd or deploy.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
LABS=ROOT/"examples/js2py"
def clean_environment(source=None):
    """Build child settings without inheriting a different project/venv or libpq target."""
    parent = dict(os.environ if source is None else source)
    env = {
        key: value for key, value in parent.items()
        if not key.startswith(("UV_", "PG", "PYTHON", "PYTEST_", "OPS_", "UVICORN_", "CONDA_"))
        and key not in {"VIRTUAL_ENV", "DATABASE_URL", "WEB_CONCURRENCY", "__PYVENV_LAUNCHER__"}
    }
    # This one PG-prefixed variable selects binaries, never connection defaults.
    if "PG_BIN" in parent:
        env["PG_BIN"] = parent["PG_BIN"]
    env.update(
        PATH=str(Path.home()/".local/bin")+os.pathsep+parent.get("PATH", ""),
        UV_PYTHON_INSTALL_DIR="/tmp/langshift-js2py-python-20260928",
        UV_CACHE_DIR="/tmp/langshift-js2py-uv-cache-20260928",
        UV_DEFAULT_INDEX="https://pypi.org/simple",
        UV_NO_CONFIG="1",
        PYTHONIOENCODING="utf-8",
        PYTHONNOUSERSITE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
    )
    return env


ENV=clean_environment()

def run(args,cwd,env=None):
    print("RUN", " ".join(map(str,args)),"IN",cwd,flush=True)
    result=subprocess.run(args,cwd=cwd,env=ENV if env is None else env,text=True,capture_output=True,timeout=240)
    print(result.stdout,end="")
    if result.stderr:print(result.stderr,end="")
    assert result.returncode==0,(args,result.returncode)
    return result.stdout


def stage(lab,target):
    names=json.loads((LABS/f"{lab}-files.json").read_text())
    assert len(names)==len(set(names))
    target.mkdir()
    hashes={}
    for name in names:
        path=Path(name)
        assert not path.is_absolute() and ".." not in path.parts
        assert not any(x in {".venv","__pycache__",".pytest_cache",".env",".runtime"} or x.startswith(".env.") for x in path.parts)
        assert path.suffix not in {".dump",".backup",".log"}
        source=LABS/lab/path
        assert source.is_file() and not source.is_symlink()
        data=source.read_bytes();hashes[name]=hashlib.sha256(data).hexdigest()
        destination=target/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
        if path.suffix==".py":ast.parse(data.decode(),filename=name)
    config=tomllib.loads((target/"pyproject.toml").read_text())
    assert config["project"]["requires-python"]==">=3.13,<3.14"
    assert config["tool"]["uv"]["package"] is False
    lock=tomllib.loads((target/"uv.lock").read_text())
    for package in lock["package"]:
        if "registry" in package["source"]:assert package["source"]["registry"]=="https://pypi.org/simple"
        for artifact in [package.get("sdist"),*package.get("wheels",[])]:
            if artifact:assert urlparse(artifact["url"]).hostname=="files.pythonhosted.org" and artifact["hash"].startswith("sha256:")
    return hashes


def tree_snapshot(root):
    """Check only our synthetic decoy; never follow an interpreter symlink."""
    result = {}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            result[relative] = ["symlink", os.readlink(path)]
        elif path.is_file():
            result[relative] = ["file", hashlib.sha256(path.read_bytes()).hexdigest()]
        elif path.is_dir():
            result[relative] = ["directory"]
    return result


def verify_uv_environment(path, proof):
    proof.mkdir()
    decoy = proof/"external-venv-decoy"
    run(["uv", "venv", "--python", "3.13.15", str(decoy)], proof)
    (decoy/"do-not-change.txt").write_text("synthetic environment boundary marker\n")
    config_home = proof/"config-home"
    (config_home/"uv").mkdir(parents=True)
    config = config_home/"uv/uv.toml"
    config.write_text("deliberately invalid TOML [ synthetic-config-canary\n")
    poison = dict(os.environ)
    poison.update(
        VIRTUAL_ENV=str(decoy), UV_PROJECT_ENVIRONMENT=str(decoy), UV_ACTIVE="1",
        UV_PYTHON=str(proof/"missing-interpreter"), UV_NO_CONFIG="0",
        UV_CONFIG_FILE=str(config), UV_PROJECT=str(proof/"wrong-project"),
        UV_ENV_FILE=str(proof/"missing-env-file"), XDG_CONFIG_HOME=str(config_home),
        PGHOSTADDR="synthetic-not-an-IP", PGSERVICE="synthetic-not-a-service",
        PGSERVICEFILE=str(proof/"not-a-service-file"),
    )
    original = dict(poison)
    env = clean_environment(poison)
    assert poison == original, "Do not mutate the caller environment"
    for key in ["VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_ACTIVE", "UV_PYTHON",
                "UV_CONFIG_FILE", "UV_PROJECT", "UV_ENV_FILE", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"]:
        assert key not in env
    assert env["UV_NO_CONFIG"] == "1"
    assert env.get("PG_BIN") == poison.get("PG_BIN")
    before = tree_snapshot(proof)
    run(["uv", "sync", "--locked"], path, env=env)
    assert tree_snapshot(proof) == before, "A synthetic external venv/config was changed"
    assert (path/".venv/bin/python").is_file()
    code = "import sys; from pathlib import Path; assert Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(); print('OWNED VENV PREFIX PASS')"
    run([str(path/".venv/bin/python"), "-c", code, str(path/".venv")], path, env=env)
    print("ENV GUARD PASS: inherited uv/venv overrides removed; invalid user config ignored; synthetic external venv unchanged", flush=True)


def verify_direct_entry_rejection(path, python):
    before = set(Path("/tmp").glob("ls-ops-*"))
    # Invalid synthetic values only. These are never a real host, DSN or service file.
    poison = dict(ENV, PGHOSTADDR="synthetic-not-an-IP",
                  PGSERVICE="synthetic-not-a-service",
                  PGSERVICEFILE="/synthetic/not-a-service-file",
                  PGPASSWORD="synthetic-private-environment-value")
    for entry in ["demo.py", "ci.py"]:
        result = subprocess.run([python, entry], cwd=path, env=poison,
                                text=True, capture_output=True, timeout=30)
        text = result.stdout+result.stderr
        assert result.returncode != 0
        assert "Refusing inherited PostgreSQL environment" in text
        assert "synthetic-private-environment-value" not in text
        assert "synthetic-not-an-IP" not in text and "synthetic-not-a-service" not in text
        assert "synthetic/not-a-service-file" not in text
        assert set(Path("/tmp").glob("ls-ops-*")) == before
        print("DIRECT ENTRY GUARD PASS", path.name, entry, "refused before cluster creation; values not logged", flush=True)


def main():
    assert "uv 0.12.13" in run(["uv","--version"],ROOT)
    counts={"o04-release":(7,2),"o05-observability":(8,1),"o06-recovery":(6,1)}
    results={}
    before=set(Path("/tmp").glob("ls-ops-*"))
    with tempfile.TemporaryDirectory(prefix="ls-ops-delivery-") as temp:
        for lab,(ordinary,independent) in counts.items():
            path=Path(temp)/lab;hashes=stage(lab,path)
            if lab == "o04-release":
                verify_uv_environment(path, Path(temp)/"environment-proof")
            else:
                run(["uv","sync","--locked"],path)
            python=str(path/".venv/bin/python")
            assert "Python 3.13.15" in run([python,"--version"],path)
            verify_direct_entry_rejection(path, python)
            output=run([python,"ci.py"],path)
            assert re.search(rf"\b{ordinary} passed\b",output)
            assert "CLEANUP PASS:" in output and "LOCAL CI PASS:" in output
            independent_output=run([python,"-m","pytest","-q","solutions"],path)
            assert re.search(rf"\b{independent} passed\b",independent_output)
            for name,digest in hashes.items():
                assert hashlib.sha256((path/name).read_bytes()).hexdigest()==digest,(lab,name,"staged artifact changed")
                assert hashlib.sha256((LABS/lab/name).read_bytes()).hexdigest()==digest,(lab,name,"canonical artifact changed")
            results[lab]={"ordinary_tests":ordinary,"independent_tests":independent,"allowlisted_files":len(hashes),"real_drill":True,"source_and_lock_unchanged":True,"direct_entry_env_rejection":True,"two_real_port0_servers":True}
    leftovers=set(Path("/tmp").glob("ls-ops-*"))-before
    assert not leftovers,"New owned cluster paths remain; inspect, do not broadly delete"
    print("OPERATIONS DELIVERY PASS",json.dumps(results,sort_keys=True))
    print("PENDING: hosted CI, Linux/systemd, Docker, public ingress/deployment, notification delivery, offsite backup, cross-host restore, production capacity, invited users")


if __name__=="__main__":main()
