"""Expected failure. Run explicitly, not as part of the passing suite.
The second test checks the *same* app retained from the first test.
This ordered diagnostic is not a pattern for ordinary independent tests.
"""
import pytest

from task_api.dependencies import get_store
from task_api.store import MemoryStore

seen = []


def test_01_deliberate_failure(app, overrides):
    seen.append(app)
    overrides[get_store] = lambda: MemoryStore()
    assert False, "deliberate failure after override"


def test_02_previous_app_was_restored():
    assert len(seen) == 1
    assert seen[0].dependency_overrides == {}
