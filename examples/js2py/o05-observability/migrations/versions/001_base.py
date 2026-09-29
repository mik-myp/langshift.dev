from pathlib import Path
from alembic import op
revision = "001_base"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    path = Path(__file__).resolve().parents[2] / "sql/001_base.sql"
    op.execute(path.read_text())

def downgrade():
    raise RuntimeError("No automatic destructive downgrade: application rollback keeps the expanded schema")
