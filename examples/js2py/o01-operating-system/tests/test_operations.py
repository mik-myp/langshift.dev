from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import pytest

from environment_lab import observe as environment_observe
from permissions_lab import observe as permissions_observe
from port_lab import observe as port_observe
from process_lab import ROOT, observe, signal_case
from worker import data_directory


def test_process_config_signals_and_restart():
    assert observe() == ["missing_config_exit=78",
        "SIGTERM: subprocess_returncode=0 cleanup=True",
        "SIGINT: subprocess_returncode=0 cleanup=True",
        "SIGKILL: subprocess_returncode=-9 cleanup=False",
        "same_directory_across_processes=2"]


@pytest.mark.parametrize("value", [None, "", ".", "relative/path", "/missing-js2py-ops-directory"])
def test_bad_directory_is_rejected(value):
    with pytest.raises(ValueError):
        data_directory({} if value is None else {"OPS_DATA_DIR": value})


def test_environment_and_cwd_are_explicit():
    assert environment_observe() == ["parent-choice", "from the working directory",
        "parent_mapping_unchanged=True", "wrong_cwd_exit=1", "wrong_cwd_is_FileNotFoundError=True"]


def test_permissions_are_not_fixed_by_making_everything_writable():
    assert permissions_observe() == ["directory_mode=0o700", "file_mode=0o600",
        "read_without_permission=denied", "restored_read=True"]


def test_port_collision_and_owned_cleanup():
    assert port_observe() == ["listening_on_loopback=True", "second_bind_rejected=True", "owned_socket_closed=True"]


def test_invalid_configuration_does_not_echo_the_value():
    result = subprocess.run([sys.executable, str(ROOT / "worker.py"), "--once"],
        env={"OPS_DATA_DIR": "fictional-sensitive-marker"}, capture_output=True, text=True, timeout=3)
    assert result.returncode == 78
    assert "fictional-sensitive-marker" not in result.stderr


def test_corrupt_state_is_not_silently_reset():
    with TemporaryDirectory() as temp:
        state = Path(temp) / "state.json"
        state.write_text('{"starts": "bad"}')
        result = subprocess.run([sys.executable, str(ROOT / "worker.py"), "--once"],
            env={"OPS_DATA_DIR": temp}, capture_output=True, text=True, timeout=3)
        assert result.returncode == 65
        assert state.read_text() == '{"starts": "bad"}'


def test_unit_is_a_template_with_explicit_identity_and_stop_boundary():
    unit = (ROOT / "systemd/ops-worker.service").read_text()
    for setting in ("User=langshift-ops", "WorkingDirectory=/opt/", "Restart=on-failure", "TimeoutStopSec=5", "KillSignal=SIGTERM", "UMask=0077"):
        assert setting in unit
    assert "User=root" not in unit


@pytest.mark.parametrize("content", ["[]", "null", '{"starts": true}', '{"starts": -1}'])
def test_invalid_state_shape_has_controlled_exit(tmp_path, content):
    (tmp_path / "state.json").write_text(content)
    result = subprocess.run([sys.executable, str(ROOT / "worker.py"), "--once"],
        env={"OPS_DATA_DIR": str(tmp_path)}, text=True, capture_output=True, timeout=3)
    assert result.returncode == 65
    assert "Traceback" not in result.stderr
