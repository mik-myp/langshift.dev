from fastapi.testclient import TestClient
import pytest
from solutions.origin_policy import create_app, ORIGINS


@pytest.mark.parametrize("origin", ORIGINS)
def test_two_exact_origins(origin):
    client = TestClient(create_app())
    result = client.options("/probe", headers={"Origin": origin,
        "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,idempotency-key"})
    assert result.status_code == 200
    assert result.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in result.headers


@pytest.mark.parametrize("origin", ["https://frontend.lab.test:8445", "http://frontend.lab.test:8444", "https://frontend.lab.test.evil.invalid:8444", "null"])
def test_near_misses_do_not_match(origin):
    result = TestClient(create_app()).options("/probe", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
    assert result.status_code == 400
    assert "access-control-allow-origin" not in result.headers


def test_curl_style_request_is_not_authorized_by_cors():
    result = TestClient(create_app()).post("/probe")
    assert result.status_code == 200 and result.json() == {"authenticated": False}
