from pathlib import Path
from alembic import op
revision = "003_contract"
down_revision = '002_expand'
branch_labels = None
depends_on = None

def upgrade():
    path = Path(__file__).resolve().parents[2] / "sql/003_contract.sql"
    op.execute(path.read_text())

def downgrade():
    raise RuntimeError("No automatic destructive downgrade: application rollback keeps the expanded schema")
