import json
from pathlib import Path
import stat

from fastapi.testclient import TestClient
import pytest

from app import create_app, LOCAL_ORIGIN
from check_config import check
from tls_lab import running, curl, decoded, direct, backend


@pytest.fixture(scope="module")
def lab():
    with running() as value:
        yield value


def test_real_tls_and_forwarded_authorization(lab):
    status, body = decoded(curl(lab, extra=("-H", "Authorization: Bearer demo-not-a-valid-session")))
    assert status == 200
    assert body == {"scheme": "https", "host": "lab.test", "client": "127.0.0.1", "authorization_present": True}


def test_unknown_ca_is_not_trusted(lab):
    assert curl(lab, trusted=False).returncode == 60


def test_wrong_hostname_still_fails_with_trusted_ca(lab):
    assert curl(lab, hostname="wrong.test").returncode == 60


def test_edge_discards_spoofed_headers(lab):
    _, body = decoded(curl(lab, extra=("-H", "X-Forwarded-For: 203.0.113.9",
        "-H", "X-Forwarded-Proto: http", "-H", "Forwarded: for=203.0.113.9;proto=http")))
    assert body["client"] == "127.0.0.1" and body["scheme"] == "https"


def test_local_process_can_spoof_when_loopback_is_trusted(lab):
    _, body = direct(lab["backend_port"], headers={"X-Forwarded-For": "203.0.113.9"})
    assert body["client"] == "203.0.113.9"


def test_no_proxy_trust_ignores_headers(tmp_path):
    with backend(tmp_path, trust_proxy=False) as port:
        _, body = direct(port, headers={"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.9"})
        assert body["scheme"] == "http" and body["client"] == "127.0.0.1"


def test_generic_500_and_private_log(lab):
    status, body = decoded(curl(lab, "/fail"))
    assert status == 500 and body == {"detail": "Internal server error"}
    log = (lab["directory"] / "backend.log").read_text()
    assert "unhandled_error request_id=" in log
    assert "FICTIONAL_INTERNAL" not in log and "demo-not-a-valid-session" not in log


def test_422_does_not_echo_input(lab):
    status, body = decoded(curl(lab, extra=("-H", "Content-Type: application/json", "--data", '{"minutes":"fictional-secret"}')))
    assert status == 422
    assert body == {"detail": [{"loc": ["body", "minutes"], "type": "int_type"}]}


def test_normal_json_input(lab):
    assert decoded(curl(lab, extra=("-H", "Content-Type: application/json", "--data", '{"minutes":0}'))) == (200, {"minutes": 0})


def test_local_edge_body_limit(lab):
    assert decoded(curl(lab, extra=("--data-binary", "x" * 4097)))[0] == 413


def test_private_temp_key_permissions(lab):
    assert stat.S_IMODE(lab["directory"].stat().st_mode) == 0o700
    assert all(stat.S_IMODE((lab["directory"] / file).stat().st_mode) == 0o600 for file in ("ca.key", "leaf.key"))


def test_cors_preflight_allows_exact_origin(lab):
    result = curl(lab, extra=("--include", "-X", "OPTIONS", "-H", f"Origin: {LOCAL_ORIGIN}",
        "-H", "Access-Control-Request-Method: POST", "-H", "Access-Control-Request-Headers: authorization,content-type,idempotency-key"))
    assert result.returncode == 0 and result.stdout.endswith("\n200")
    assert f"access-control-allow-origin: {LOCAL_ORIGIN}" in result.stdout.lower()
    assert "access-control-allow-credentials:" not in result.stdout.lower()


def test_cors_rejected_preflight_but_not_authentication():
    client = TestClient(create_app(), base_url="https://lab.test")
    preflight = client.options("/probe", headers={"Origin": "https://other.lab.test", "Access-Control-Request-Method": "POST"})
    assert preflight.status_code == 400 and "access-control-allow-origin" not in preflight.headers
    actual = client.get("/probe", headers={"Origin": "https://other.lab.test"})
    assert actual.status_code == 200 and "access-control-allow-origin" not in actual.headers
    assert actual.json()["authorization_present"] is False


def test_host_is_checked_separately():
    client = TestClient(create_app(), base_url="https://evil.invalid")
    assert client.get("/probe").status_code == 400


def test_cors_covers_sanitized_500():
    client = TestClient(create_app(), base_url="https://lab.test")
    response = client.get("/fail", headers={"Origin": LOCAL_ORIGIN})
    assert response.status_code == 500 and response.headers["access-control-allow-origin"] == LOCAL_ORIGIN
    assert len(response.headers["x-request-id"]) == 32


def test_config_checks_are_not_deployment_acceptance():
    assert "caddy_runtime=NOT_VERIFIED" in check()


def test_owned_tls_resources_are_removed():
    with running() as own:
        directory, port = own["directory"], own["backend_port"]
    assert not directory.exists()
    with pytest.raises(OSError):
        direct(port)
