from dataclasses import dataclass, field


def checked_title(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("title must be non-blank text")
    return value


def checked_minutes(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("minutes must be a non-negative integer")
    return value


class Task:
    def __init__(self, title: str, minutes: int, done: bool = False) -> None:
        self.title = checked_title(title)
        self.minutes = checked_minutes(minutes)
        if type(done) is not bool:
            raise ValueError("done must be a bool")
        self.done = done

    def mark_done(self) -> bool:
        if self.done:
            return False
        self.done = True
        return True

    def remaining_minutes(self) -> int:
        return 0 if self.done else self.minutes

    def label(self) -> str:
        return self.title


class Plan:
    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = list(tasks)  # Own the list, share the contained Task instances.

    def remaining_minutes(self) -> int:
        total = 0
        for task in self.tasks:
            total += task.remaining_minutes()
        return total


class UrgentTask(Task):
    def label(self) -> str:
        return "! " + super().label()


@dataclass
class RawEstimate:
    title: str
    minutes: int


@dataclass
class Estimate:
    title: str
    minutes: int
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.title = checked_title(self.title)
        self.minutes = checked_minutes(self.minutes)
        if not isinstance(self.tags, list):
            raise ValueError("tags must be a list of text")
        for tag in self.tags:
            if not isinstance(tag, str):
                raise ValueError("tags must be a list of text")
        self.tags = list(self.tags)
