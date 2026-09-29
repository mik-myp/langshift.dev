from alembic import context
from sqlalchemy import create_engine, pool
from models import Base
from safety import checked_url

config = context.config
target_metadata = Base.metadata
url = checked_url(config.attributes.get("database_url"))

if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"}, compare_type=True,
                      compare_server_default=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata,
                              compare_type=True, compare_server_default=True)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()
