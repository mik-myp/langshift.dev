#!/usr/bin/env python3
"""Build/check a deterministic download from an explicit, secret-free allowlist."""

import argparse
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "examples/js2py/u00-environment"
MANIFEST = ROOT / "examples/js2py/u00-files.json"
OUTPUT = ROOT / "public/learning-assets/js2py/u00-environment.zip"


LABS = {
    "u11-typing": (
        ROOT / "examples/js2py/u11-typing",
        ROOT / "examples/js2py/u11-typing-files.json",
        ROOT / "public/learning-assets/js2py/u11-typing.zip",
    ),
    "u12-models": (
        ROOT / "examples/js2py/u12-models",
        ROOT / "examples/js2py/u12-models-files.json",
        ROOT / "public/learning-assets/js2py/u12-models.zip",
    ),
    "u13-decorators": (
        ROOT / "examples/js2py/u13-decorators",
        ROOT / "examples/js2py/u13-decorators-files.json",
        ROOT / "public/learning-assets/js2py/u13-decorators.zip",
    ),
    "u14-resources": (
        ROOT / "examples/js2py/u14-resources",
        ROOT / "examples/js2py/u14-resources-files.json",
        ROOT / "public/learning-assets/js2py/u14-resources.zip",
    ),
    "u08-environments": (
        ROOT / "examples/js2py/u08-environments",
        ROOT / "examples/js2py/u08-environments-files.json",
        ROOT / "public/learning-assets/js2py/u08-environments.zip",
    ),
    "u09-testing": (
        ROOT / "examples/js2py/u09-testing",
        ROOT / "examples/js2py/u09-testing-files.json",
        ROOT / "public/learning-assets/js2py/u09-testing.zip",
    ),
    "u10-local-project": (
        ROOT / "examples/js2py/u10-local-project",
        ROOT / "examples/js2py/u10-local-project-files.json",
        ROOT / "public/learning-assets/js2py/u10-local-project.zip",
    ),
    "u07-files": (
        ROOT / "examples/js2py/u07-files",
        ROOT / "examples/js2py/u07-files-files.json",
        ROOT / "public/learning-assets/js2py/u07-files.zip",
    ),
    "u06-modules": (
        ROOT / "examples/js2py/u06-modules",
        ROOT / "examples/js2py/u06-modules-files.json",
        ROOT / "public/learning-assets/js2py/u06-modules.zip",
    ),
    "u05-exceptions": (
        ROOT / "examples/js2py/u05-exceptions",
        ROOT / "examples/js2py/u05-exceptions-files.json",
        ROOT / "public/learning-assets/js2py/u05-exceptions.zip",
    ),
    "u00-environment": (LAB, MANIFEST, OUTPUT),
    "u00-first-script": (
        ROOT / "examples/js2py/u00-first-script",
        ROOT / "examples/js2py/u00-first-script-files.json",
        ROOT / "public/learning-assets/js2py/u00-first-script.zip",
    ),
    "u01-scalars": (
        ROOT / "examples/js2py/u01-scalars",
        ROOT / "examples/js2py/u01-scalars-files.json",
        ROOT / "public/learning-assets/js2py/u01-scalars.zip",
    ),
    "u04-functions": (
        ROOT / "examples/js2py/u04-functions",
        ROOT / "examples/js2py/u04-functions-files.json",
        ROOT / "public/learning-assets/js2py/u04-functions.zip",
    ),
    "u03-control-flow": (
        ROOT / "examples/js2py/u03-control-flow",
        ROOT / "examples/js2py/u03-control-flow-files.json",
        ROOT / "public/learning-assets/js2py/u03-control-flow.zip",
    ),
    "u02-containers": (
        ROOT / "examples/js2py/u02-containers",
        ROOT / "examples/js2py/u02-containers-files.json",
        ROOT / "public/learning-assets/js2py/u02-containers.zip",
    ),
}


for row in json.loads(
    (ROOT / "scripts/tests/fixtures/js2py-backend-chapters.json").read_text()
):
    LABS[row["lab"]] = (
        ROOT / "examples/js2py" / row["lab"],
        ROOT / "examples/js2py" / (row["lab"] + "-files.json"),
        ROOT / "public/learning-assets/js2py" / (row["lab"] + ".zip"),
    )


def build_archive(lab=LAB, manifest=MANIFEST, prefix="u00-environment"):
    if not prefix or prefix in (".", "..") or "/" in prefix or "\\" in prefix:
        raise ValueError("Archive prefix must be a single directory name")
    names = json.loads(manifest.read_text(encoding="utf-8"))
    if len(names) != len(set(names)):
        raise ValueError("Duplicate lab file in allowlist")
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(names):
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Invalid lab path: {name}")
            source = lab / relative
            if not source.is_file() or source.is_symlink():
                raise ValueError(f"Missing or non-regular lab file: {name}")
            info = zipfile.ZipInfo(f"{prefix}/{name}", (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
    return data.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--lab", choices=sorted(LABS))
    args = parser.parse_args()
    names = [args.lab] if args.lab else list(LABS)
    for name in names:
        lab, manifest, output = LABS[name]
        expected = build_archive(lab, manifest, name)
        if args.check:
            if not output.exists() or output.read_bytes() != expected:
                parser.exit(
                    1,
                    f"{name} download is stale. Run python3 scripts/build-js2py-lab.py\n",
                )
            print(f"{name} download matches its allowlisted source files")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(expected)
            print(f"Built {output.relative_to(ROOT)} ({len(expected)} bytes)")


if __name__ == "__main__":
    main()
