from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class InputModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", validate_default=True)


class LoginInput(InputModel):
    login: str = Field(min_length=1, max_length=80)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("login")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("login must not be blank")
        return value


class NewPassword(InputModel):
    password: SecretStr = Field(min_length=15, max_length=128)


class PasswordChange(InputModel):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=15, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    login: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


from datetime import UTC, datetime
from typing import Literal


class ProjectInput(InputModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value


class MemberInput(InputModel):
    # Target invitee, never the authenticated actor or a self-selected role.
    user_id: int = Field(gt=0, le=9223372036854775807)


class TaskInput(InputModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: Literal["todo", "doing", "done"] = "todo"
    minutes: int = Field(default=0, ge=0, le=2147483647)
    priority: int = Field(default=0, ge=0, le=2)
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value

    @field_validator("due_at", mode="before")
    @classmethod
    def aware_utc(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("due_at must be an ISO timestamp") from None
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("due_at must include an offset")
        return value.astimezone(UTC)


class TaskPatch(TaskInput):
    title: str = Field(default="Untitled", min_length=1, max_length=120)


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_by: int
    created_at: datetime


class MemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    role: Literal["owner", "member"]


class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    created_by: int
    title: str
    description: str | None
    status: Literal["todo", "doing", "done"]
    minutes: int
    priority: int
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProjectPage(BaseModel):
    items: list[ProjectPublic]
    limit: int
    offset: int
    total: int


class TaskPage(BaseModel):
    items: list[TaskPublic]
    limit: int
    offset: int
    total: int
