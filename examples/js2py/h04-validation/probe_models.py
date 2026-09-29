from pydantic import BaseModel, ValidationError

from models import TaskCreate


class LooseMinutes(BaseModel):
    minutes: int


class RequiredNullable(BaseModel):
    note: str | None


def show_error(label: str, operation) -> None:
    try:
        operation()
    except ValidationError as error:
        # Do not print arbitrary raw input into production logs.
        print(label, error.errors()[0]["type"])


print("loose:", LooseMinutes(minutes="25").minutes)
for value in [True, "25", 25.0, -1]:
    show_error(repr(value), lambda: TaskCreate(title="Read", minutes=value))
record = TaskCreate(title="  Read HTTP  ", minutes=0)
print("strict:", record.model_dump())
show_error("nullable but missing:", lambda: RequiredNullable())
print("nullable and present:", RequiredNullable(note=None).model_dump())
