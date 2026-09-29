import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from task_app.app import initial_tasks, main
from task_app.storage import load_tasks, save_tasks


def test_round_trip_and_independent_results():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "tasks.json"
        source = [{"title": "学习", "minutes": 0, "done": False}]
        save_tasks(path, source)
        loaded = load_tasks(path)
        assert loaded == source
        loaded[0]["title"] = "changed"
        assert load_tasks(path) == source
        assert "学习" in path.read_text(encoding="utf-8")
        assert path.read_bytes().endswith(b"\n")


def test_missing_file_propagates():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "absent.json"
        with pytest.raises(FileNotFoundError):
            load_tasks(path)
        assert not path.exists()


def test_rejected_save_does_not_truncate_existing_file():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "tasks.json"
        save_tasks(path, initial_tasks())
        before = path.read_bytes()
        with pytest.raises(ValueError):
            save_tasks(path, {"tasks": []})
        assert path.read_bytes() == before


def test_rejected_save_does_not_create_missing_file():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "tasks.json"
        with pytest.raises(ValueError):
            save_tasks(path, [None])
        assert not path.exists()


def test_repeated_save_is_one_document_not_append():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "tasks.json"
        save_tasks(path, initial_tasks())
        save_tasks(path, [])
        assert path.read_bytes() == b"[]\n"
        assert load_tasks(path) == []


def test_main_first_and_second_and_empty_runs():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "nested" / "tasks.json"
        main(path)
        first = path.read_bytes()
        assert load_tasks(path)[0]["done"] is True
        main(path)
        assert path.read_bytes() == first
        save_tasks(path, [])
        main(path)
        assert path.read_bytes() == b"[]\n"


def test_main_does_not_overwrite_malformed_json():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "tasks.json"
        path.write_bytes(b"{broken\n")
        with pytest.raises(json.JSONDecodeError):
            main(path)
        assert path.read_bytes() == b"{broken\n"


def test_main_does_not_overwrite_invalid_encoding():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "tasks.json"
        path.write_bytes(b"\xff")
        with pytest.raises(UnicodeDecodeError):
            main(path)
        assert path.read_bytes() == b"\xff"


def test_main_does_not_overwrite_invalid_business_data():
    with TemporaryDirectory(prefix="js2py-test-") as directory:
        path = Path(directory) / "tasks.json"
        path.write_text('{"tasks": []}\n', encoding="utf-8")
        before = path.read_bytes()
        with pytest.raises(ValueError):
            main(path)
        assert path.read_bytes() == before
