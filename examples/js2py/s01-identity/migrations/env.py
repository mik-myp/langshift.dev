import os
from alembic import context
from sqlalchemy import create_engine, pool
from models import Base
from isolation import clear_libpq_environment

clear_libpq_environment()

url = os.environ.get("DATABASE_URL")
if not url or not url.startswith("postgresql+psycopg://"):
    raise RuntimeError("Set DATABASE_URL to the owned PostgreSQL lab URL")

# A real database is intentional; no offline create_all or implicit stamping.
engine = create_engine(url, poolclass=pool.NullPool, hide_parameters=True)
try:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
finally:
    engine.dispose()
