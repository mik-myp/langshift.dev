from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from solutions.restore_copy import restore_counter
from volume_probe import count


def test_restore_to_a_new_directory_not_the_live_source():
    with TemporaryDirectory() as temp:
        source, restored = Path(temp) / "source", Path(temp) / "restored"
        source.mkdir(); restored.mkdir()
        count(source, True); count(source, True)
        assert restore_counter(source, restored) == 2
        assert count(source) == 2


def test_nonempty_restore_target_is_refused():
    with TemporaryDirectory() as temp:
        root = Path(temp)
        count(root, True)
        with pytest.raises(ValueError, match="empty"):
            restore_counter(root, root)


def test_corrupt_source_does_not_write_a_destination(tmp_path):
    source, destination = tmp_path / "source", tmp_path / "destination"
    source.mkdir(); destination.mkdir()
    file = source / "counter.json"
    file.write_text('{"count": true}')
    with pytest.raises(ValueError):
        restore_counter(source, destination)
    assert list(destination.iterdir()) == []
    assert file.read_text() == '{"count": true}'
