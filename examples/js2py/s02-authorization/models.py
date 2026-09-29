"""Reviewed D schema plus explicitly migrated authentication state."""
from datetime import datetime
from sqlalchemy import (BigInteger, CheckConstraint, DateTime, ForeignKey, Identity,
                        Integer, String, UniqueConstraint, text, Boolean, Text, Index)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("login", name="users_login_key"),
        CheckConstraint("length(btrim(login)) > 0", name="users_login_nonblank"),
        CheckConstraint("auth_version >= 1", name="users_auth_version_positive"),
        CheckConstraint("NOT is_active OR password_hash IS NOT NULL", name="users_active_password"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    login: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    auth_version: Mapped[int] = mapped_column(BigInteger, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (CheckConstraint("length(btrim(name)) > 0", name="projects_name_nonblank"),)
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey(
        "users.id", ondelete="RESTRICT", name="projects_created_by_fkey"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        CheckConstraint("role IN ('owner', 'member')", name="project_members_role_valid"),
        Index("project_members_one_owner", "project_id", unique=True,
              postgresql_where=text("role = 'owner'")),
    )
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(
        "projects.id", ondelete="RESTRICT", name="project_members_project_id_fkey"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(
        "users.id", ondelete="RESTRICT", name="project_members_user_id_fkey"), primary_key=True)
    role: Mapped[str] = mapped_column(String(8))


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("length(btrim(title)) > 0", name="tasks_title_nonblank"),
        CheckConstraint("status IN ('todo', 'doing', 'done')", name="tasks_status_valid"),
        CheckConstraint("minutes >= 0", name="tasks_minutes_nonnegative"),
        CheckConstraint("priority BETWEEN 0 AND 2", name="tasks_priority_valid"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey(
        "projects.id", ondelete="RESTRICT", name="tasks_project_id_fkey"))
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey(
        "users.id", ondelete="RESTRICT", name="tasks_created_by_fkey"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(8), server_default=text("'todo'"))
    minutes: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    priority: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        CheckConstraint("auth_version >= 1", name="auth_sessions_version_positive"),
        CheckConstraint("expires_at > issued_at", name="auth_sessions_expiry_order"),
        CheckConstraint("token_digest ~ '^[0-9a-f]{64}$'", name="auth_sessions_digest_format"),
        Index("auth_sessions_user_id_idx", "user_id"),
        Index("auth_sessions_expires_at_idx", "expires_at"),
    )
    token_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"))
    auth_version: Mapped[int] = mapped_column(BigInteger)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
