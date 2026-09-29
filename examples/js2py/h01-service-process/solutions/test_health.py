from pathlib import Path
from tools.owned_server import exchange, owned_server

PUBLIC = Path(__file__).resolve().parent / "public"


def test_independent_directory_and_a_second_request():
    with owned_server(PUBLIC) as (process, port):
        assert exchange(port, "/health.txt")[2] == b"ready\n"
        assert exchange(port, "/note.txt")[2] == b"a separate serving directory\n"
        assert process.poll() is None
    assert process.poll() is not None


def test_original_directory_is_not_implicitly_shared():
    with owned_server(PUBLIC) as (_, port):
        assert exchange(port, "/hello.txt")[0] == 404
