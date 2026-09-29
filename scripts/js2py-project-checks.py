"""Maintainer integration helpers for the L08–L10 foundation projects."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def environment(**changes):
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    for key in ["VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_ACTIVE", "UV_PYTHON"]:
        env.pop(key, None)
    env.update(PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1", UV_NO_CONFIG="1")
    env.update(changes)
    return env


def run(cwd, *args, expected=0, env=None):
    result = subprocess.run(
        list(args),
        cwd=cwd,
        env=env or environment(),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != expected:
        raise AssertionError(
            (args, result.returncode, expected, result.stdout, result.stderr)
        )
    return result


def uv(cwd, *args, **kwargs):
    return run(cwd, "uv", *args, **kwargs)


def python(cwd, source, **kwargs):
    return uv(cwd, "run", "--locked", "python", "-c", source, **kwargs)


def project(parent, lab, label=None):
    manifest = json.loads((ROOT / f"examples/js2py/{lab}-files.json").read_text())
    target = parent / (label or lab)
    target.mkdir()
    with zipfile.ZipFile(ROOT / f"public/learning-assets/js2py/{lab}.zip") as archive:
        assert sorted(archive.namelist()) == sorted(
            f"{lab}/{name}" for name in manifest
        )
        for name in manifest:
            payload = archive.read(f"{lab}/{name}")
            assert payload == (ROOT / "examples/js2py" / lab / name).read_bytes()
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    return target


def check_unchanged(lab, names):
    for name, payload in names.items():
        assert (lab / name).read_bytes() == payload, name


def metadata(lab):
    return {
        name: (lab / name).read_bytes()
        for name in ["pyproject.toml", "uv.lock", ".python-version"]
    }


def check_environments():
    with tempfile.TemporaryDirectory(prefix="js2py-environments-") as directory:
        parent = Path(directory).resolve()
        (parent / "pyproject.toml").write_text(
            '[project]\nname="outer"\nversion="0.0.0"\nrequires-python=">=99"\n'
        )
        parent_bytes = (parent / "pyproject.toml").read_bytes()
        lab = project(parent, "u08-environments")
        before = metadata(lab)
        uv(lab, "sync", "--locked")
        probe = uv(lab, "run", "--locked", "python", "probe.py").stdout
        assert "Python: 3.13.15\n" in probe and "Isolated: True\n" in probe
        assert "Distribution: 4.13.0\n" in probe and "Size: 1.5 KiB\n" in probe
        assert str(lab / ".venv") in probe
        expected = "Files: 3\nBytes: 1536\nReadable: 1.5 KiB\n"
        assert uv(lab, "run", "--locked", "python", "app.py").stdout == expected
        check_unchanged(lab, before)

        # Real extra distribution: demonstrate run's inexact default vs sync's exact default.
        interpreter = python(lab, "import sys; print(sys.executable)").stdout.strip()
        uv(
            lab,
            "pip",
            "install",
            "--python",
            interpreter,
            "packaging==25.0",
            "--default-index",
            "https://pypi.org/simple",
        )
        assert (
            python(lab, "import packaging; print(packaging.__version__)").stdout
            == "25.0\n"
        )
        uv(lab, "sync", "--locked")
        assert (
            python(
                lab,
                "import importlib.util; print(importlib.util.find_spec('packaging'))",
            ).stdout
            == "None\n"
        )
        check_unchanged(lab, before)

        shadow = uv(
            lab, "run", "--locked", "python", "errors/show_shadow.py", expected=1
        )
        assert (
            "AttributeError" in shadow.stderr
            and str(lab / "errors/humanize.py") in shadow.stdout
        )
        (lab / "errors/humanize.py").rename(lab / "errors/local_marker.py")
        assert uv(
            lab, "run", "--locked", "python", "errors/show_shadow.py"
        ).stdout.endswith("1.5 KiB\n")

        missing = lab / "exercises/missing-declaration"
        uv(missing, "sync", "--locked")
        failure = uv(missing, "run", "--locked", "python", "app.py", expected=1)
        assert "ModuleNotFoundError" in failure.stderr and "humanize" in failure.stderr
        original = metadata(missing)
        uv(
            missing,
            "add",
            "humanize==4.13.0",
            "--default-index",
            "https://pypi.org/simple",
        )
        assert (missing / "pyproject.toml").read_bytes() != original["pyproject.toml"]
        assert (missing / "uv.lock").read_bytes() != original["uv.lock"]
        assert uv(missing, "run", "--locked", "python", "app.py").stdout == "2.0 KiB\n"

        stale = project(parent, "u08-environments", "stale")
        p = stale / "pyproject.toml"
        p.write_text(p.read_text().replace("humanize==4.13.0", "humanize==4.12.0"))
        stale_before = metadata(stale)
        result = uv(stale, "run", "--locked", "python", "app.py", expected=2)
        assert "--locked" in result.stderr and "lockfile" in result.stderr.lower()
        assert result.stdout == ""
        check_unchanged(stale, stale_before)

        cold = project(parent, "u08-environments", "cold")
        result = uv(
            cold,
            "sync",
            "--offline",
            "--locked",
            expected=1,
            env=environment(UV_CACHE_DIR=str(parent / "empty-cache")),
        )
        assert "cache" in result.stderr.lower() or "offline" in result.stderr.lower()
        assert not (cold / "_output").exists()

        for name in ["independent-a", "independent-b"]:
            scratch = parent / name
            scratch.mkdir()
            assert not list(scratch.iterdir())
            answer = lab / "solutions/size-report"
            for filename in [
                ".python-version",
                "pyproject.toml",
                "uv.lock",
                "report.py",
            ]:
                (scratch / filename).write_bytes((answer / filename).read_bytes())
            uv(scratch, "sync", "--locked")
            assert (
                uv(scratch, "run", "--locked", "python", "report.py").stdout == expected
            )
            source = """from report import total_bytes
for values, expected in [([], 0), ([0], 0), ([1024, 1024], 2048), ([1, 2, 3], 6)]:
    original = values.copy()
    assert total_bytes(values) == expected and values == original
for values in [None, (1,), [True], [-1], [1.5], ["1"]]:
    try:
        total_bytes(values)
    except ValueError:
        continue
    raise AssertionError(values)
print("independent matrix passed")
"""
            assert python(scratch, source).stdout == "independent matrix passed\n"
            assert python(scratch, "import report").stdout == ""
        assert (parent / "pyproject.toml").read_bytes() == parent_bytes
        print(
            "L08 PASS: versions/origin, locked recovery, inexact/exact sync, missing declaration repair, shadow repair, stale lock, cold-cache failure, two independent environments"
        )


def check_testing():
    with tempfile.TemporaryDirectory(prefix="js2py-testing-") as directory:
        parent = Path(directory).resolve()
        lab = project(parent, "u09-testing")
        before = metadata(lab)
        uv(lab, "sync", "--locked")
        assert (
            uv(lab, "run", "--locked", "python", "first_check.py").stdout
            == "Observed: 20\nChecked\n"
        )
        assert (
            "AssertionError"
            in uv(lab, "run", "--locked", "python", "wrong_check.py", expected=1).stderr
        )
        for args, count in [
            ((), "6 passed"),
            (("tests/test_study.py::test_empty_input_is_zero",), "1 passed"),
        ]:
            assert (
                count
                in uv(
                    lab, "run", "--locked", "python", "-m", "pytest", "-q", *args
                ).stdout
            )
        collect = uv(
            lab, "run", "--locked", "python", "-m", "pytest", "--collect-only", "-q"
        ).stdout
        assert "6 tests collected" in collect
        for filename, exit_code, fragment in [
            ("errors/test_wrong_expectation.py", 1, "1 failed"),
            ("errors/test_false_green.py", 0, "1 passed"),
            ("errors/not_discovered", 5, "no tests ran"),
            ("errors/test_import_failure.py", 2, "ModuleNotFoundError"),
            ("exercises/test_broken_study.py", 1, "2 failed"),
        ]:
            assert (
                fragment
                in uv(
                    lab,
                    "run",
                    "--locked",
                    "python",
                    "-m",
                    "pytest",
                    "-q",
                    filename,
                    expected=exit_code,
                ).stdout
            )
        undetected = lab / "errors/not_discovered/check_totals.py"
        undetected.rename(undetected.with_name("test_totals.py"))
        assert (
            "1 passed"
            in uv(
                lab,
                "run",
                "--locked",
                "python",
                "-m",
                "pytest",
                "-q",
                "errors/not_discovered",
            ).stdout
        )
        broken = lab / "exercises/broken_study.py"
        broken.write_text(
            broken.read_text().replace('if task["done"]:', 'if not task["done"]:')
        )
        assert (
            "2 passed"
            in uv(
                lab,
                "run",
                "--locked",
                "python",
                "-m",
                "pytest",
                "-q",
                "exercises/test_broken_study.py",
            ).stdout
        )
        study = lab / "study.py"
        good = study.read_text()
        for mutant in [
            good.replace('if not task["done"]:', 'if task["done"]:'),
            good.replace(
                "if type(minutes) is not int or minutes < 0:", "if minutes < 0:"
            ),
        ]:
            study.write_text(mutant)
            assert (
                "failed"
                in uv(
                    lab, "run", "--locked", "python", "-m", "pytest", "-q", expected=1
                ).stdout
            )
        study.write_text(good)
        assert (
            "6 passed"
            in uv(lab, "run", "--locked", "python", "-m", "pytest", "-q").stdout
        )
        uv(lab, "sync", "--locked", "--no-dev")
        absent = uv(
            lab, "run", "--locked", "--no-dev", "python", "-m", "pytest", expected=1
        )
        assert "No module named pytest" in absent.stderr
        uv(lab, "sync", "--locked")
        check_unchanged(lab, before)
        answer = lab / "solutions/budget"
        uv(answer, "sync", "--locked")
        assert (
            "9 passed"
            in uv(answer, "run", "--locked", "python", "-m", "pytest", "-q").stdout
        )
        scratch = parent / "my-budget"
        scratch.mkdir()
        for name in [
            "pyproject.toml",
            ".python-version",
            "uv.lock",
            "budget.py",
            "tests/test_budget.py",
        ]:
            p = scratch / name
            p.parent.mkdir(exist_ok=True)
            p.write_bytes((answer / name).read_bytes())
        uv(scratch, "sync", "--locked")
        assert (
            "9 passed"
            in uv(scratch, "run", "--locked", "python", "-m", "pytest", "-q").stdout
        )
        original = (scratch / "budget.py").read_text()
        (scratch / "budget.py").write_text(
            "def remaining_budget(budget, spent):\n    return 0\n"
        )
        assert (
            "failed"
            in uv(
                scratch, "run", "--locked", "python", "-m", "pytest", "-q", expected=1
            ).stdout
        )
        (scratch / "budget.py").write_text(original)
        assert (
            "9 passed"
            in uv(scratch, "run", "--locked", "python", "-m", "pytest", "-q").stdout
        )
        print(
            "L09 PASS: 6+9 tests, discovery/selection, exact exits 1/2/5, false-green demonstration, repairs, three mutation detections, no-dev recovery and empty reconstruction"
        )


def check_local_project():
    with tempfile.TemporaryDirectory(prefix="js2py-local-project-") as directory:
        parent = Path(directory).resolve()
        lab = project(parent, "u10-local-project")
        before = metadata(lab)
        uv(lab, "sync", "--locked")
        assert (
            uv(lab, "run", "--locked", "python", "check_import.py").stdout
            == "Imported: task_app.app task_app.storage\n"
        )
        assert not (lab / "_output").exists()
        assert (
            uv(lab, "run", "--locked", "python", "demo_resource.py").stdout
            == "Inside: True\nAfter: False\n"
        )
        assert (
            "15 passed"
            in uv(lab, "run", "--locked", "python", "-m", "pytest", "-q").stdout
        )
        assert (
            "2 passed"
            in uv(
                lab,
                "run",
                "--locked",
                "python",
                "-m",
                "pytest",
                "-q",
                "solutions/test_new_requirement.py",
            ).stdout
        )
        assert not (lab / "_output").exists()
        first = "Source: new file\nChanged: 1\nTasks: 3\nPending minutes: 35\n"
        again = "Source: existing file\nChanged: 0\nTasks: 3\nPending minutes: 35\n"
        assert (
            uv(lab, "run", "--locked", "python", "-m", "task_app.app").stdout == first
        )
        path = lab / "_output/tasks.json"
        good = path.read_bytes()
        assert (
            uv(lab, "run", "--locked", "python", "-m", "task_app.app").stdout == again
        )
        assert path.read_bytes() == good
        assert (
            uv(
                parent,
                "run",
                "--project",
                "u10-local-project",
                "--locked",
                "python",
                "u10-local-project/run_tasks.py",
            ).stdout
            == again
        )
        assert not (parent / "_output").exists()
        path.write_bytes(good.replace(b'"minutes": 35', b'"minutes": 36'))
        assert (
            "Pending minutes: 36\n"
            in uv(lab, "run", "--locked", "python", "-m", "task_app.app").stdout
        )
        for bad, error in [
            (b"{broken\n", "JSONDecodeError"),
            (b"\xff", "UnicodeDecodeError"),
            (b'{"tasks": []}\n', "ValueError"),
        ]:
            path.write_bytes(bad)
            result = uv(
                lab, "run", "--locked", "python", "-m", "task_app.app", expected=1
            )
            assert result.stdout == "Invalid existing data; refusing to save\n"
            assert error in result.stderr and path.read_bytes() == bad
        path.write_bytes(b"[]\n")
        assert (
            uv(lab, "run", "--locked", "python", "-m", "task_app.app").stdout
            == "Source: existing file\nChanged: 0\nTasks: 0\nPending minutes: 0\n"
        )
        assert path.read_bytes() == b"[]\n"
        check_unchanged(lab, before)
        scratch = project(parent, "u10-local-project", "independent-copy")
        assert not (scratch / ".venv").exists() and not (scratch / "_output").exists()
        uv(scratch, "sync", "--locked")
        assert (
            "15 passed"
            in uv(scratch, "run", "--locked", "python", "-m", "pytest", "-q").stdout
        )
        assert (
            uv(scratch, "run", "--locked", "python", "-m", "task_app.app").stdout
            == first
        )
        rules = scratch / "task_app/rules.py"
        correct = rules.read_text()
        rules.write_text(correct.replace('if not task["done"]:', 'if task["done"]:'))
        assert (
            "failed"
            in uv(
                scratch, "run", "--locked", "python", "-m", "pytest", "-q", expected=1
            ).stdout
        )
        rules.write_text(correct)
        assert (
            "15 passed"
            in uv(scratch, "run", "--locked", "python", "-m", "pytest", "-q").stdout
        )
        print(
            "L10 PASS: 15+2 tests, import safety, temporary cleanup, actual first/repeated processes, external cwd, changed/empty/corrupt inputs, mutation detection and clean recovery"
        )


def main(kind):
    if not shutil.which("uv"):
        raise SystemExit(
            "Install uv and the chapter's Python baseline before integration checks."
        )
    {
        "environments": check_environments,
        "testing": check_testing,
        "local-project": check_local_project,
    }[kind]()


if __name__ == "__main__":
    main(sys.argv[1])
