import pytest
import labctl


@pytest.fixture(autouse=True)
def fresh_owned_database():
    # reset() refuses a missing/tampered ownership marker or a different server.
    labctl.reset()
