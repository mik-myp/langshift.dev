from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest

from client import fetch
from observe import observe
from tools.owned_server import exchange, owned_server

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


def test_success_failure_success_does_not_stop_the_process():
    assert observe(PUBLIC, "/hello.txt") == [
        "200 hello from the service", "404 missing", "200 hello from the service",
        "request_done_process_alive=True", "process_stopped=True",
    ]


def test_client_reads_the_response():
    with owned_server(PUBLIC) as (_, port):
        assert fetch(port, "/hello.txt") == (200, "hello from the service\n")


def test_query_is_not_a_literal_filename():
    with owned_server(PUBLIC) as (_, port):
        status, _, body = exchange(port, "/hello.txt?attempt=2")
        assert status == 200
        assert body == b"hello from the service\n"


def test_head_has_no_response_body():
    with owned_server(PUBLIC) as (_, port):
        status, headers, body = exchange(port, "/hello.txt", "HEAD")
        assert status == 200
        assert int(headers["Content-Length"]) == len(b"hello from the service\n")
        assert body == b""


def test_project_file_is_not_inside_the_served_directory():
    with owned_server(PUBLIC) as (_, port):
        assert exchange(port, "/pyproject.toml")[0] == 404


def test_address_collision_does_not_kill_the_first_server():
    with owned_server(PUBLIC) as (first, port):
        second = subprocess.run(
            [sys.executable, "-m", "http.server", str(port),
             "--bind", "127.0.0.1", "--directory", str(PUBLIC)],
            capture_output=True, text=True, timeout=5,
        )
        assert second.returncode != 0
        assert "Address already in use" in second.stderr
        assert first.poll() is None
        assert exchange(port, "/hello.txt")[0] == 200


def test_wrong_existing_directory_causes_404_not_startup_failure():
    with TemporaryDirectory() as empty:
        with owned_server(Path(empty)) as (process, port):
            assert exchange(port, "/hello.txt")[0] == 404
            assert process.poll() is None


def test_exception_still_stops_only_our_child():
    with pytest.raises(RuntimeError, match="intentional experiment failure"):
        with owned_server(PUBLIC) as (process, _):
            raise RuntimeError("intentional experiment failure")
    assert process.poll() is not None


def test_ctrl_c_signal_stops_our_foreground_equivalent():
    with owned_server(PUBLIC) as (process, _):
        process.send_signal(signal.SIGINT)
        assert process.wait(timeout=3) == 0


@pytest.mark.parametrize("port,path", [(0, "/hello.txt"), (65536, "/hello.txt"), (8765, "hello.txt")])
def test_client_rejects_invalid_local_arguments(port, path):
    with pytest.raises(ValueError):
        fetch(port, path)


def test_client_cli_http_failure_has_exit_2():
    with owned_server(PUBLIC) as (_, port):
        result = subprocess.run(
            [sys.executable, str(ROOT / "client.py"), str(port), "/not-here.txt"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 2
        assert result.stdout.startswith("status=404\n")
