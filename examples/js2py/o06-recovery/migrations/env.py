from alembic import context

# Only our controller supplies a connection. Never read an ambient DATABASE_URL.
connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Use the owned-cluster migration controller, not an external URL")
context.configure(connection=connection, target_metadata=None)
with context.begin_transaction():
    context.run_migrations()
