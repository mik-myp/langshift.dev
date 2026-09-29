from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", validate_default=True)

    title: str = Field(min_length=1, max_length=120)
    minutes: int = Field(ge=0)
    done: bool = False
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def reject_blank_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value  # Check a stripped copy, but preserve the original spelling.


class TaskPatch(TaskCreate):
    # Valid placeholders for omitted fields, NOT replacement values for storage.
    # Only model_dump(exclude_unset=True) may be merged into an existing task.
    title: str = Field(default="Untitled", min_length=1, max_length=120)
    minutes: int = Field(default=0, ge=0)


class TaskStored(TaskCreate):
    id: int = Field(gt=0)
    internal_tag: str = "h04-memory-only"


class TaskPublic(BaseModel):
    # A deliberately separate output allowlist; never use this as an input model.
    model_config = ConfigDict(strict=True, extra="ignore", validate_default=True)

    id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=120)
    minutes: int = Field(ge=0)
    done: bool
    note: str | None


class TaskPage(BaseModel):
    items: list[TaskPublic]
    limit: int
    offset: int
    total: int
