import os
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
import pytest

from app import create_app
from check_config import check
from config import data_directory
from secret_demo import observe
from volume_probe import count


def test_static_config_is_explicitly_not_runtime_acceptance():
    assert check()[-1] == "container_runtime=NOT_VERIFIED"


def test_secret_demo_never_prints_its_marker():
    assert observe() == ["file_mode=0o600", "fictional_value_loaded=True", "value_is_not_printed=True"]


@pytest.mark.parametrize("value", [None, "", ".", "relative", "/missing-js2py-container-dir"])
def test_startup_rejects_invalid_data_directory(value):
    with pytest.raises(ValueError):
        data_directory({} if value is None else {"OPS_DATA_DIR": value})


def test_health_is_not_a_task_api(monkeypatch):
    with TemporaryDirectory() as temp:
        monkeypatch.setenv("OPS_DATA_DIR", temp)
        with TestClient(create_app()) as client:
            assert client.get("/health/live").json() == {"status": "ok"}
            assert client.get("/health/ready").json() == {"status": "ready"}
            assert client.get("/tasks").status_code == 404


def test_liveness_survives_readiness_write_failure(monkeypatch):
    assert os.geteuid() != 0, "ordinary user required to test POSIX write denial"
    with TemporaryDirectory() as temp:
        directory = Path(temp)
        monkeypatch.setenv("OPS_DATA_DIR", temp)
        with TestClient(create_app()) as client:
            directory.chmod(0o500)
            try:
                assert client.get("/health/live").status_code == 200
                assert client.get("/health/ready").status_code == 503
            finally:
                directory.chmod(0o700)


def test_local_storage_preservation_is_not_a_container_volume_test():
    with TemporaryDirectory() as temp:
        first, second = Path(temp) / "first", Path(temp) / "second"
        first.mkdir(); second.mkdir()
        assert count(first) == 0
        assert count(first, True) == 1
        assert count(first) == 1
        assert count(second) == 0


def test_corrupt_counter_is_not_reset():
    with TemporaryDirectory() as temp:
        file = Path(temp) / "counter.json"
        file.write_text('{"count": true}')
        with pytest.raises(ValueError):
            count(Path(temp), True)
        assert file.read_text() == '{"count": true}'



def test_container_probe_without_opt_in_is_pending_not_success():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "container_probe.py"],
                            capture_output=True, text=True, timeout=3)
    assert result.returncode == 77
    assert "environment_pending" in result.stdout


def test_regular_file_is_not_an_engine_socket(tmp_path):
    from container_probe import local_socket
    import pytest
    path = tmp_path / "not-a-socket"
    path.write_text("fictional")
    with pytest.raises(ValueError):
        local_socket(str(path))


def test_real_loopback_http_is_not_container_acceptance():
    from local_probe import observe
    assert observe() == ["host_http_live=200", "host_http_ready=200", "unwritable_live=200",
            "unwritable_ready=503", "restored_ready=200", "tasks_not_implemented=404",
            "container_runtime=NOT_VERIFIED"]
