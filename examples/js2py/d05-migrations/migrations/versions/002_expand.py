"""Expand: nullable priority; both old and transitional writers still work."""
from alembic import op
import sqlalchemy as sa

revision = "002_expand"
down_revision = "001_base"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("priority", sa.Integer(), nullable=True))


def downgrade():
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM tasks)")).scalar_one():
        raise RuntimeError("Refusing to discard priority while tasks exist")
    op.drop_column("tasks", "priority")
