"""At most one owner; at least one still requires the atomic service protocol."""
from alembic import op
import sqlalchemy as sa

revision = "005_owner_guard"
down_revision = "004_identity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("project_members_one_owner", "project_members", ["project_id"],
                    unique=True, postgresql_where=sa.text("role = 'owner'"))


def downgrade():
    raise RuntimeError("Refusing to remove the owner guard without a reviewed plan")
