from pathlib import Path
from alembic import op
revision = "005_owner_guard"
down_revision = '004_identity'
branch_labels = None
depends_on = None

def upgrade():
    path = Path(__file__).resolve().parents[2] / "sql/005_owner_guard.sql"
    op.execute(path.read_text())

def downgrade():
    raise RuntimeError("No automatic destructive downgrade: application rollback keeps the expanded schema")
