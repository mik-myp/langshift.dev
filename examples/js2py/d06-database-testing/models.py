"""D01-D03 schema, mapped explicitly. Relationships/auth arrive in later chapters."""
from datetime import datetime
from sqlalchemy import (BigInteger, CheckConstraint, DateTime, ForeignKey, Identity,
                        Integer, String, UniqueConstraint, text)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("login", name="users_login_key"),
        CheckConstraint("length(btrim(login)) > 0", name="users_login_nonblank"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    login: Mapped[str] = mapped_column(String(80))


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
    __table_args__ = (CheckConstraint("role IN ('owner', 'member')", name="project_members_role_valid"),)
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
