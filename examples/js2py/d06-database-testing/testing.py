"""Cleanup must be installed before migration/setup, not only after yield."""
from contextlib import contextmanager
from db import make_engine
from migrate import upgrade


@contextmanager
def migrated_engine(url, prepare=None):
    engine = make_engine(url)
    try:
        if prepare is None:
            upgrade(url)
        else:
            prepare(engine)
        yield engine
    finally:
        outstanding = engine.pool.checkedout()
        engine.dispose()
        assert outstanding == 0, "Unreturned connection: do not hide it with DROP ... FORCE"
