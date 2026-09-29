import pytest
from db import make_engine
from safety import fresh_database


@pytest.fixture
def database_url():
    with fresh_database() as url:
        yield url


@pytest.fixture
def engine(database_url):
    engine = make_engine(database_url)
    try:
        yield engine
    finally:
        outstanding = engine.pool.checkedout()
        engine.dispose()
        assert outstanding == 0
