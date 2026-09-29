"""Independent variation: nullable archive timestamp with no invented old values."""
from alembic import op
import sqlalchemy as sa
revision = "004_archived_at"
down_revision = "003_contract"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("projects", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM projects WHERE archived_at IS NOT NULL)")).scalar_one():
        raise RuntimeError("Refusing to discard archive history")
    op.drop_column("projects", "archived_at")
