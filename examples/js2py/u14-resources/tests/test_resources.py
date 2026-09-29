from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from resources import TextFile, opened_text
from sequences import lines_from, tracked_minutes

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "lines.txt"


def test_laziness_and_normal_exhaustion():
    events = []
    values = tracked_minutes([30, 0], events)
    assert events == []
    assert next(values) == 30
    assert events == ["started", "yield 30"]
    assert list(values) == [0]
    assert events == ["started", "yield 30", "yield 0", "finished"]
    assert list(values) == []
    with pytest.raises(StopIteration):
        next(values)


def test_partial_validation_happens_when_resumed():
    events = []
    values = tracked_minutes([30, -1], events)
    assert next(values) == 30
    with pytest.raises(ValueError):
        next(values)
    assert events[-1] == "finished"


def test_break_needs_an_owner_to_close():
    events = []
    values = tracked_minutes([30, 0], events)
    for value in values:
        assert value == 30
        break
    assert "finished" not in events
    values.close()
    values.close()
    assert events.count("finished") == 1


def test_unstarted_close_does_not_enter_body():
    events = []
    values = tracked_minutes([30], events)
    values.close()
    assert events == []


@pytest.mark.parametrize("factory", [TextFile, opened_text])
def test_real_handle_normal_cleanup(factory):
    events = []
    with factory(FIXTURE, events) as handle:
        assert handle.readline() == "alpha\n"
        assert not handle.closed
    assert handle.closed
    assert events == ["acquire-attempt", "acquired", "released"]


@pytest.mark.parametrize("factory", [TextFile, opened_text])
def test_body_failure_is_not_suppressed(factory):
    events = []
    with pytest.raises(ValueError, match="body failed"):
        with factory(FIXTURE, events) as handle:
            raise ValueError("body failed")
    assert handle.closed
    assert events[-1] == "released"


@pytest.mark.parametrize("factory", [TextFile, opened_text])
def test_acquisition_failure_has_no_body_or_exit(factory):
    with TemporaryDirectory() as directory:
        events = []
        with pytest.raises(FileNotFoundError):
            with factory(Path(directory) / "missing.txt", events):
                raise AssertionError("body must not execute")
        assert events == ["acquire-attempt"]


def test_line_iteration_preserves_blank_lines_and_handles_early_exit():
    assert list(lines_from(FIXTURE)) == ["alpha", "", "beta"]
    with closing(lines_from(FIXTURE)) as lines:
        assert next(lines) == "alpha"
    assert list(lines) == []


def test_nested_release_order():
    events = []
    with opened_text(FIXTURE, events) as outer:
        with opened_text(FIXTURE, events) as inner:
            assert not outer.closed and not inner.closed
        assert inner.closed and not outer.closed
    assert outer.closed
    assert events == [
        "acquire-attempt",
        "acquired",
        "acquire-attempt",
        "acquired",
        "released",
        "released",
    ]
