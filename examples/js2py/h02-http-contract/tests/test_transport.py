import json
from contract_examples import ROOT, read_case
from inspect_transport import inspect
from tools.owned_server import exchange, owned_server


def test_real_status_is_not_the_embedded_contract_status():
    with owned_server(ROOT / "public") as (_, port):
        status, headers, body = exchange(port, "/exchanges/create-ok.json")
        assert status == 200
        assert headers["Content-type"].startswith("application/json")
        assert json.loads(body) == read_case("create-ok")
        assert json.loads(body)["response"]["status"] == 201


def test_live_success_failure_head_origin_and_cleanup():
    assert inspect() == [
        "real GET example: HTTP 200; proposed POST: 201",
        "real GET tasks: HTTP 404",
        "real POST tasks: HTTP 501; no CRUD implemented",
        "real HEAD example: HTTP 200; body bytes=0",
        "real GET with Origin: HTTP 200; allow-origin=False",
        "service_alive=True", "owned_service_stopped=True",
    ]


def test_origin_header_does_not_authorize_or_block_this_nonbrowser_client():
    with owned_server(ROOT / "public") as (_, port):
        status, headers, _ = exchange(port, "/exchanges/blank-title.json",
                                      headers={"Origin": "https://untrusted.invalid"})
        assert status == 200
        assert not any(key.lower() == "access-control-allow-origin" for key in headers)


def test_unimplemented_preflight_is_not_a_successful_cors_configuration():
    with owned_server(ROOT / "public") as (_, port):
        status, _, _ = exchange(port, "/tasks", "OPTIONS", headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert status == 501
