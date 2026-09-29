"""Frozen D01-D03 schema. Never import the current application model here."""
from alembic import op
import sqlalchemy as sa

revision = "001_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("login", sa.String(80), nullable=False),
        sa.UniqueConstraint("login", name="users_login_key"),
        sa.CheckConstraint("length(btrim(login)) > 0", name="users_login_nonblank"))
    op.create_table("projects",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="projects_created_by_fkey", ondelete="RESTRICT"),
        sa.CheckConstraint("length(btrim(name)) > 0", name="projects_name_nonblank"))
    op.create_table("project_members",
        sa.Column("project_id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("role", sa.String(8), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="project_members_project_id_fkey", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="project_members_user_id_fkey", ondelete="RESTRICT"),
        sa.CheckConstraint("role IN ('owner', 'member')", name="project_members_role_valid"))
    op.create_table("tasks",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.String(2000)),
        sa.Column("status", sa.String(8), nullable=False, server_default=sa.text("'todo'")),
        sa.Column("minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="tasks_project_id_fkey", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="tasks_created_by_fkey", ondelete="RESTRICT"),
        sa.CheckConstraint("length(btrim(title)) > 0", name="tasks_title_nonblank"),
        sa.CheckConstraint("status IN ('todo', 'doing', 'done')", name="tasks_status_valid"),
        sa.CheckConstraint("minutes >= 0", name="tasks_minutes_nonnegative"))


def downgrade():
    connection = op.get_bind()
    for table in ("tasks", "project_members", "projects", "users"):
        if connection.execute(sa.text(f"SELECT EXISTS (SELECT 1 FROM {table})")).scalar_one():
            raise RuntimeError("Refusing base downgrade with existing data; use a reviewed recovery plan")
    for table in ("tasks", "project_members", "projects", "users"):
        op.drop_table(table)
