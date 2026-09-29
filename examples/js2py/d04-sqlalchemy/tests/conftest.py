import pytest
from db import make_engine
from models import Base
from safety import fresh_database


@pytest.fixture
def database_url():
    with fresh_database() as url:
        yield url


@pytest.fixture
def engine(database_url):
    engine = make_engine(database_url)
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        outstanding = engine.pool.checkedout()
        engine.dispose()
        assert outstanding == 0, "Session/Connection leaked out of the test"
