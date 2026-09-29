from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from safety import checked_url


def make_engine(url=None):
    return create_engine(checked_url(url), pool_size=2, max_overflow=0,
                         pool_timeout=2, pool_pre_ping=True)


def session_factory(engine):
    # DTOs are copied inside the transaction; don't depend on detached ORM objects.
    return sessionmaker(bind=engine, expire_on_commit=True)
