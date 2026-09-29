#!/usr/bin/env python3
"""A01/A02 only: source, safe clean ZIP extraction, runtime, mutations and MDX syntax.

No shared build/loader/navigation/TypeSafe changes. Uses existing Node dependencies;
never installs frontend packages or publishes ZIPs. Run with Python >=3.11.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import tempfile
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LABS = [
    ("a01-async-model", "getAsyncModelExample", "module-30-async-model", 14, 19, 5),
    ("a02-external-services", "getExternalServiceExample", "module-31-external-services", 16, 32, 4),
]
IGNORED = {".venv", "__pycache__", ".pytest_cache"}
WEB_PINS = {
    "fastapi": "0.135.1", "uvicorn": "0.42.0", "pydantic": "2.12.5",
    "httpx": "0.28.1", "anyio": "4.12.1", "starlette": "0.52.1",
}
FENCES = re.compile(r"^```([^\n]*)\n(.*?)^```", re.M | re.S)


def environment():
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("PYTHON") or key in {
            "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_ACTIVE", "UV_PYTHON",
            "UV_INDEX", "UV_INDEX_URL", "UV_EXTRA_INDEX_URL", "UV_DEFAULT_INDEX",
        }:
            env.pop(key)
    env.update(
        PATH=str(Path.home() / ".local/bin") + os.pathsep + env.get("PATH", ""),
        UV_PYTHON_INSTALL_DIR="/tmp/langshift-js2py-python-20260928",
        UV_CACHE_DIR="/tmp/langshift-js2py-uv-cache-20260928",
        UV_DEFAULT_INDEX="https://pypi.org/simple", UV_NO_CONFIG="1",
        PYTHONIOENCODING="utf-8", PYTHONNOUSERSITE="1",
    )
    return env


def run(directory, *args, expected=0, timeout=180):
    # A timeout must stop the child uv spawned as well, but no unrelated process.
    process = subprocess.Popen(args, cwd=directory, env=environment(), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)  # Only the group created above.
        except ProcessLookupError:
            pass
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate(timeout=5)
        raise
    if process.returncode != expected:
        raise AssertionError((str(directory), args, expected, process.returncode, stdout, stderr))
    return stdout, stderr


def py(directory, *args, **kwargs):
    return run(directory, "uv", "run", "--locked", "python", *args, **kwargs)


def curated_files(lab):
    names = json.loads((ROOT / "examples/js2py" / f"{lab}-files.json").read_text())
    directory = ROOT / "examples/js2py" / lab
    assert names == sorted(set(names)), "allowlist must be sorted and unique"
    for name in names:
        path = PurePosixPath(name)
        assert not path.is_absolute() and ".." not in path.parts and "\\" not in name
        assert not set(path.parts) & (IGNORED | {".git", ".env", "node_modules"})
        assert not name.endswith((".pyc", ".pem", ".key", ".zip", ".DS_Store"))
        assert not any(part.startswith(".env") for part in path.parts)
        target = directory / name
        assert target.is_file() and not target.is_symlink()
        assert target.resolve().is_relative_to(directory.resolve())
    actual = sorted(p.relative_to(directory).as_posix() for p in directory.rglob("*")
                    if p.is_file() and not set(p.relative_to(directory).parts) & IGNORED)
    assert names == actual, (lab, "unlisted or missing files", set(names) ^ set(actual))
    assert json.loads((directory / "DOWNLOAD-ALLOWLIST.json").read_text()) == names
    for required in ("pyproject.toml", "uv.lock", ".python-version", "README.md",
                     "README.zh-cn.md", "README.zh-tw.md", "sources.json", "commands.sh"):
        assert required in names
    config = tomllib.loads((directory / "pyproject.toml").read_text())
    assert config["project"]["requires-python"] == ">=3.13,<3.14"
    assert config["tool"]["uv"]["package"] is False
    assert config["dependency-groups"]["dev"] == ["pytest==8.4.2"]
    assert (directory / ".python-version").read_text().strip() == "3.13.15"
    locked = tomllib.loads((directory / "uv.lock").read_text())
    for package in locked["package"]:
        source = package["source"]
        if "registry" in source:
            assert source["registry"] == "https://pypi.org/simple"
        else:
            assert source == {"virtual": "."}
        artifacts = package.get("wheels", []) + ([package["sdist"]] if "sdist" in package else [])
        for artifact in artifacts:
            assert artifact["url"].startswith("https://files.pythonhosted.org/")
            assert re.fullmatch(r"sha256:[a-f0-9]{64}", artifact["hash"])
    if lab.startswith("a02"):
        versions = {p["name"]: p["version"] for p in locked["package"]}
        assert all(versions[k] == v for k, v in WEB_PINS.items())
    commands = (directory / "commands.sh").read_text().strip()
    for suffix in (".md", ".zh-cn.md", ".zh-tw.md"):
        readme = (directory / ("README" + suffix)).read_text()
        assert commands in readme and "2026-09-28" in readme
    return names


def content_row(lab, loader, slug, sections, names):
    reference_sets, fence_sets = [], []
    for suffix in (".mdx", ".zh-cn.mdx", ".zh-tw.mdx"):
        text = (ROOT / "content/docs/js2py" / (slug + suffix)).read_text()
        assert f"import {{ {loader} }} from '@/lib/js2py-examples'" in text
        refs = re.findall(rf"{loader}\('([^']+)'\)", text)
        assert refs and set(refs) <= set(names)
        reference_sets.append(refs)
        fence_sets.append(FENCES.findall(text))
        assert len(re.findall(r"^## \d+\.", text, re.M)) == sections
        assert text.count("<details>") >= 3
        assert text.count("<details>") == text.count("</details>")
        assert not re.search(r"<details\s+[^>]*\bopen\b", text)
        assert f"/learning-assets/js2py/{lab}.zip" in text
        assert "2026-09-28" in text
        assert len(text) > 8000, "substantive chapter, not a translated placeholder"
        if lab.startswith("a01"):
            assert 'compare={true} canRun={false}' in text
    assert reference_sets[0] == reference_sets[1] == reference_sets[2]
    assert fence_sets[0] == fence_sets[1] == fence_sets[2], "translated executable fence drift"
    return {"lab": lab, "loader": loader, "slug": slug, "sections": sections, "refs": reference_sets[0]}


def archive_bytes(directory, names):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            info = zipfile.ZipInfo(f"{directory.name}/{name}", (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (directory / name).read_bytes())
    return buffer.getvalue()


def verify_run(directory, main_count, answer_count):
    uv, _ = run(directory, "uv", "--version")
    assert uv.startswith("uv 0.12.13 ")
    # Executes the very command file embedded in all three chapter/README editions.
    stdout, stderr = run(directory, "bash", "commands.sh")
    assert "Python 3.13.15" in stdout
    counts = [int(x) for x in re.findall(r"(\d+) passed", stdout)]
    assert counts == [main_count, answer_count], (directory, counts, stdout)
    expected = "expected-output.txt" if directory.name.startswith("a01") else "expected-socket-output.txt"
    assert (directory / expected).read_text() in stdout
    if directory.name.startswith("a01"):
        assert py(directory, "comparison.py")[0] == (directory / "expected-python.txt").read_text()
        assert run(directory, "node", "comparison.js")[0] == (directory / "expected-javascript.txt").read_text()
        versions = {"python": "3.13.15", "pytest": "8.4.2"}
    else:
        output, _ = py(directory, "-c", "import json, importlib.metadata as m; "
                       f"print(json.dumps({{p:m.version(p) for p in {list(WEB_PINS) + ['pytest']!r}}}))")
        versions = json.loads(output)
        assert versions == {**WEB_PINS, "pytest": "8.4.2"}
        versions["python"] = "3.13.15"
    print(f"PASS {directory.name}: main={main_count}, solutions={answer_count}", flush=True)
    return {"main_passed": main_count, "solutions_passed": answer_count,
            "command": "bash commands.sh", "demo_exact_match": True, "versions": versions}


def mutation(directory, filename, before, after, selector):
    target = directory / filename
    original = target.read_text()
    assert before in original
    try:
        target.write_text(original.replace(before, after, 1))
        clear_bytecode(directory)
        stdout, _ = py(directory, "-m", "pytest", "-q", *selector, expected=1, timeout=45)
        assert "failed" in stdout
    finally:
        target.write_text(original)
        clear_bytecode(directory)
    print(f"CAUGHT mutant {directory.name}/{filename}", flush=True)
    return {"lab": directory.name, "file": filename, "selector": selector, "caught": True}


def clear_bytecode(directory):
    for path in directory.rglob("__pycache__"):
        if ".venv" not in path.relative_to(directory).parts:
            shutil.rmtree(path)


def mdx_check():
    # Existing site dependencies only. Compilation is a separate syntax check,
    # not a claim that missing integration loaders resolve or a service works.
    code = r'''
import fs from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(process.cwd() + '/package.json');
const local = createRequire(require.resolve('fumadocs-mdx'));
const { compile } = await import(local.resolve('@mdx-js/mdx'));
const { remarkCodeHike, recmaCodeHike } = await import('codehike/mdx');
const config = { components: { code: 'Code' } };
let count = 0;
for (const slug of ['module-30-async-model', 'module-31-external-services']) {
  for (const suffix of ['.mdx', '.zh-cn.mdx', '.zh-tw.mdx']) {
    const text = fs.readFileSync('content/docs/js2py/' + slug + suffix, 'utf8');
    const output = String(await compile(text, {
      remarkPlugins: [[remarkCodeHike, config]], recmaPlugins: [[recmaCodeHike, config]],
    }));
    if (slug.includes('30') && !output.includes("getAsyncModelExample('comparison.py')"))
      throw new Error('Comparison lost its source expression');
    count++;
  }
}
console.log(JSON.stringify({ compiled: count, pipeline: 'MDX + Code Hike', integration: false }));
'''
    stdout, _ = run(ROOT, "node", "--input-type=module", "-e", code)
    return json.loads(stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-out", type=Path, default=Path("/tmp/langshift-a01-a02-handoff.json"))
    args = parser.parse_args()
    rows, evidence, mutations = [], {}, []
    for lab, loader, slug, sections, main_count, answer_count in LABS:
        names = curated_files(lab)
        rows.append(content_row(lab, loader, slug, sections, names))
        directory = ROOT / "examples/js2py" / lab
        source_evidence = verify_run(directory, main_count, answer_count)
        data = archive_bytes(directory, names)
        assert data == archive_bytes(directory, names), "non-deterministic ZIP"
        with tempfile.TemporaryDirectory(prefix="langshift-async-extract-") as temporary:
            destination = Path(temporary)
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                assert sorted(archive.namelist()) == [f"{lab}/{name}" for name in names]
                archive.extractall(destination)  # Names already validated before archive creation.
            extracted = destination / lab
            assert not (extracted / ".venv").exists()
            for name in names:
                assert (extracted / name).read_bytes() == (directory / name).read_bytes()
            clean_evidence = verify_run(extracted, main_count, answer_count)
            if lab.startswith("a01"):
                mutations.append(mutation(extracted, "ownership.py", "        handle.close()",
                                          '        events.append("mutant:leaked")',
                                          ["tests/test_model.py", "-k", "real_file"]))
                mutations.append(mutation(extracted, "capacity.py", "async with slots:",
                                          "async with asyncio.Semaphore(99):",
                                          ["tests/test_model.py", "-k", "test_capacity"]))
            else:
                mutations.append(mutation(extracted, "service.py", "Hint.model_validate_json(bytes(body))",
                                          'Hint(priority="normal")',
                                          ["tests/test_service.py", "-k", "contract_and_bounded_retry"]))
                mutations.append(mutation(extracted, "lifecycle.py", "await client.aclose()",
                                          "await anyio.sleep(0)",
                                          ["tests/test_socket.py", "-k", "real_connection_released and normal"]))
            # Mutants are restored and never touch the repository source.
            for name in names:
                assert (extracted / name).read_bytes() == (directory / name).read_bytes()
        evidence[lab] = {"source": source_evidence, "clean_allowlisted_zip": clean_evidence,
                         "zip_sha256": hashlib.sha256(data).hexdigest(), "allowlisted_files": len(names)}
    mdx = mdx_check()
    assert mdx["compiled"] == 6
    payload = {
        "rows": rows,
        "verification": {
            "verified_on": "2026-09-28", "uv": "0.12.13", "labs": evidence,
            "unique_tests": 60, "source_and_clean_archive_each_passed": 60,
            "real_tcp_tests_in_a02_main": 5, "mutations": mutations,
            "mdx_syntax": mdx, "shared_integration_changed": False,
            "official_sources": [f"examples/js2py/{row['lab']}/sources.json" for row in rows],
            "not_verified": ["full-site loader/navigation/TypeSafe integration and ZIP publication",
                             "production database/auth/capstone integration", "load/multi-worker/TLS/HTTP2",
                             "all real connect/write/pool timeout phases", "forced process termination",
                             "AnyIO backends other than asyncio"],
        },
    }
    args.metadata_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"PASS: 60 unique tests in source and again in clean extraction; 4 mutants caught; 6 MDX files")
    print(f"Handoff: {args.metadata_out}")


if __name__ == "__main__":
    main()
