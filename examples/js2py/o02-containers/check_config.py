"""Selected security invariants, NOT Docker parsing/build/runtime validation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_FILES = {"Dockerfile", ".dockerignore", ".python-version", "pyproject.toml", "uv.lock", "app.py", "config.py", "volume_probe.py", "healthcheck.py"}


def check() -> list[str]:
    ignored = (ROOT / ".dockerignore").read_text().splitlines()
    assert ignored[0] == "**"
    assert {line[1:] for line in ignored[1:]} == BUILD_FILES
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "USER 10001:10001" in dockerfile
    assert "COPY . ." not in dockerfile
    assert "--locked --no-dev" in dockerfile
    assert 'CMD ["python", "-m", "uvicorn"' in dockerfile
    assert "--no-proxy-headers" in dockerfile
    service = json.loads((ROOT / "compose.json").read_text())["services"]["smoke"]
    assert all(port.startswith("127.0.0.1:") for port in service["ports"])
    assert service["read_only"] is True and service["user"] == "10001:10001"
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]
    assert "privileged" not in service and "network_mode" not in service
    assert not any("docker.sock" in mount for mount in service["volumes"])
    return ["build_context=explicit_allowlist", "host_publish=loopback_only", "runtime_user=10001", "root_filesystem=read_only", "container_runtime=NOT_VERIFIED"]


if __name__ == "__main__":
    print("\n".join(check()))
