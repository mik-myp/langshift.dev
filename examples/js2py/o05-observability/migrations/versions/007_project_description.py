from pathlib import Path
from alembic import op
revision = "007_project_description"
down_revision = '006_task_operations'
branch_labels = None
depends_on = None

def upgrade():
    path = Path(__file__).resolve().parents[2] / "sql/007_project_description.sql"
    op.execute(path.read_text())

def downgrade():
    raise RuntimeError("No automatic destructive downgrade: application rollback keeps the expanded schema")
