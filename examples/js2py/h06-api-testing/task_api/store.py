from task_api.models import TaskCreate, TaskPatch, TaskStored


class MemoryStore:
    """Sequential exercises only: no durable data, locks or user permissions."""

    def __init__(self) -> None:
        self.tasks: dict[int, TaskStored] = {}
        self.next_id = 1

    def create(self, payload: TaskCreate) -> TaskStored:
        record = TaskStored(id=self.next_id, **payload.model_dump())
        self.tasks[record.id] = record
        self.next_id += 1
        return record

    def ordered(self) -> list[TaskStored]:
        return [self.tasks[key] for key in sorted(self.tasks)]

    def get(self, task_id: int) -> TaskStored | None:
        return self.tasks.get(task_id)

    def patch(self, current: TaskStored, payload: TaskPatch) -> TaskStored:
        candidate = current.model_dump()
        candidate.update(payload.model_dump(exclude_unset=True))
        updated = TaskStored.model_validate(candidate)
        self.tasks[current.id] = updated
        return updated

    def delete(self, task_id: int) -> None:
        del self.tasks[task_id]
