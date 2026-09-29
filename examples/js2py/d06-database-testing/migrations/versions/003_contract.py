"""Small lab backfill + contract. Large tables need a separate bounded backfill."""
from alembic import op
import sqlalchemy as sa

revision = "003_contract"
down_revision = "002_expand"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE tasks SET priority = 0 WHERE priority IS NULL")
    op.alter_column("tasks", "priority", existing_type=sa.Integer(),
                    server_default=sa.text("0"), nullable=False)
    op.create_check_constraint("tasks_priority_valid", "tasks", "priority BETWEEN 0 AND 2")


def downgrade():
    # Values survive this step, but the guarantees/default disappear.
    op.drop_constraint("tasks_priority_valid", "tasks", type_="check")
    op.alter_column("tasks", "priority", existing_type=sa.Integer(),
                    server_default=None, nullable=True)
