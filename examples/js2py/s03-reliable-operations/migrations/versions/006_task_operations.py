"""A transactionally committed receipt, scoped to actor/project/operation/key."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_task_operations"
down_revision = "005_owner_guard"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("task_operations",
        sa.Column("actor_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("project_id", sa.BigInteger(), sa.ForeignKey("projects.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("operation", sa.String(32), primary_key=True),
        sa.Column("key", sa.Uuid(), primary_key=True),
        sa.Column("request_digest", sa.String(64), nullable=False),
        sa.Column("response_body", postgresql.JSONB(), nullable=False),
        sa.Column("response_status", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expires_at > created_at", name="task_operations_expiry_order"),
        sa.CheckConstraint("response_status = 201", name="task_operations_status"),
        sa.CheckConstraint("request_digest ~ '^[0-9a-f]{64}$'", name="task_operations_digest_format"))
    op.create_index("task_operations_expires_at_idx", "task_operations", ["expires_at"])


def downgrade():
    raise RuntimeError("Refusing to erase replay history without a reviewed retention plan")
