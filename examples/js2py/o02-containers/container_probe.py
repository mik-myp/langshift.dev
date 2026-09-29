"""Opt-in ONLY. Never uses the user's Docker context or removes their resources.
A passing local static check is not a passing container experiment.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
from tempfile import TemporaryDirectory
import time
import uuid

ROOT = Path(__file__).resolve().parent


def local_socket(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not stat.S_ISSOCK(path.stat().st_mode):
        raise ValueError("explicit existing local UNIX socket required")
    return path


def run_probe(socket_path: Path) -> list[str]:
    docker = shutil.which("docker")
    if docker is None:
        raise RuntimeError("Docker CLI is unavailable")
    name = "js2py-o02-" + uuid.uuid4().hex[:12]
    image, volume = name + ":lab", name + "-data"
    containers = []
    built = created_volume = False
    results = []
    # Empty config: do not read credential helpers or contact a saved remote context.
    with TemporaryDirectory(prefix="js2py-docker-config-") as config:
        base = [docker, "--config", config, "--host", f"unix://{socket_path}"]
        env = {key: value for key, value in os.environ.items()
               if not key.startswith("DOCKER_") and key not in {"BUILDX_BUILDER"}}
        def call(*args, check=True, timeout=180):
            p = subprocess.run(base + list(args), env=env, cwd=ROOT, text=True,
                               capture_output=True, timeout=timeout)
            if check and p.returncode:
                # Build errors can be inspected locally; no environment dump.
                raise RuntimeError(f"owned Docker command failed: {args[0]}\n{p.stderr[-3000:]}")
            return p.stdout.strip()
        version = json.loads(call("version", "--format", "{{json .Server}}"))
        if int(version["Version"].split(".")[0]) < 28 or version.get("Os") != "linux":
            raise RuntimeError("controlled Linux Docker Engine >=28 required")
        try:
            call("build", "--tag", image, ".", timeout=600)
            built = True
            call("volume", "create", "--label", f"langshift.owner={name}", volume)
            created_volume = True
            def start(suffix, persistent):
                target = name + suffix
                args = ["run", "-d", "--name", target, "--label", f"langshift.owner={name}",
                        "--init", "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
                        "--publish", "127.0.0.1::8000"]
                if persistent:
                    args += ["--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16777216",
                             "--mount", f"type=volume,source={volume},target=/data"]
                # Nonpersistent branch intentionally tests the writable layer.
                call(*args, image)
                containers.append(target)
                deadline = time.monotonic() + 40
                while time.monotonic() < deadline:
                    health = call("inspect", "--format", "{{.State.Health.Status}}", target)
                    if health == "healthy":
                        return target
                    time.sleep(.5)
                raise RuntimeError("owned container did not become healthy")
            def count(target, increment=False):
                args = ["exec", target, "python", "volume_probe.py"]
                if increment:
                    args.append("--increment")
                return int(call(*args))
            first = start("-volume-a", True)
            assert call("exec", first, "id", "-u") == "10001"
            assert json.loads(call("inspect", "--format", "{{json .HostConfig}}", first))["ReadonlyRootfs"]
            bindings = json.loads(call("inspect", "--format", "{{json .NetworkSettings.Ports}}", first))
            assert all(v["HostIp"] == "127.0.0.1" for values in bindings.values() if values for v in values)
            assert count(first, True) == 1
            call("stop", "--time", "10", first)
            call("start", first)
            assert count(first) == 1
            call("rm", "--force", first); containers.remove(first)
            second = start("-volume-b", True)
            assert count(second) == 1
            results += ["nonroot=10001", "root_filesystem=read_only", "host_publish=loopback_only", "named_volume_after_recreate=1"]
            layer = start("-layer-a", False)
            assert count(layer, True) == 1
            call("stop", "--time", "10", layer); call("start", layer)
            assert count(layer) == 1
            call("rm", "--force", layer); containers.remove(layer)
            fresh = start("-layer-b", False)
            assert count(fresh) == 0
            results += ["writable_layer_after_stop_start=1", "writable_layer_after_recreate=0"]
            return results
        finally:
            # No prune, global stop, wildcard names or removal of pre-existing resources.
            for target in reversed(containers):
                call("rm", "--force", target, check=False)
            if created_volume:
                call("volume", "rm", volume, check=False)
            if built:
                call("image", "rm", image, check=False)
            print("owned_resources_cleanup_requested=True")
            # Base image/build cache may remain. Never prune a shared engine.


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", help="explicit local UNIX socket, no remote contexts")
    parser.add_argument("--confirm-controlled-engine", action="store_true")
    args = parser.parse_args()
    if not args.socket or not args.confirm_controlled_engine:
        print("environment_pending: provide a controlled local Linux Docker Engine >=28 and explicit consent")
        return 77
    try:
        socket_path = local_socket(args.socket)
    except (OSError, ValueError):
        print("environment_pending: explicit local UNIX socket is unavailable")
        return 77
    try:
        print("\n".join(run_probe(socket_path)))
    except (RuntimeError, AssertionError, subprocess.TimeoutExpired) as exc:
        print(f"container experiment failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
