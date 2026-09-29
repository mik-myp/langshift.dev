"""Expand the reviewed D schema; existing users do NOT receive fake passwords."""
from alembic import op
import sqlalchemy as sa

revision = "004_identity"
down_revision = "003_contract"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("auth_version", sa.BigInteger(), nullable=False, server_default="1"))
    op.add_column("users", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                                    server_default=sa.text("CURRENT_TIMESTAMP")))
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(timezone=True)))
    op.create_check_constraint("users_auth_version_positive", "users", "auth_version >= 1")
    op.create_check_constraint("users_active_password", "users", "NOT is_active OR password_hash IS NOT NULL")
    op.create_table("auth_sessions",
        sa.Column("token_digest", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("auth_version", sa.BigInteger(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("auth_version >= 1", name="auth_sessions_version_positive"),
        sa.CheckConstraint("expires_at > issued_at", name="auth_sessions_expiry_order"),
        sa.CheckConstraint("token_digest ~ '^[0-9a-f]{64}$'", name="auth_sessions_digest_format"))
    op.create_index("auth_sessions_user_id_idx", "auth_sessions", ["user_id"])
    op.create_index("auth_sessions_expires_at_idx", "auth_sessions", ["expires_at"])


def downgrade():
    raise RuntimeError("Refusing to discard authentication state; use a reviewed recovery plan")
