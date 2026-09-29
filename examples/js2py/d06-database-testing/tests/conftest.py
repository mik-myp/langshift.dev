import pytest
from safety import fresh_database
from testing import migrated_engine


@pytest.fixture
def database_url():
    # Each test can commit/rollback for real. No outer rollback masks COMMIT.
    with fresh_database() as url:
        yield url


@pytest.fixture
def engine(database_url):
    # Context cleanup already exists if upgrade fails before yield.
    with migrated_engine(database_url) as engine:
        yield engine
