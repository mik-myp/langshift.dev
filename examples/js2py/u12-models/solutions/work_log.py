from models import checked_minutes, checked_title


class WorkLog:
    def __init__(self, title: str, entries: list[int] | None = None) -> None:
        self.title = checked_title(title)
        self.entries: list[int] = []
        if entries is not None:
            for minutes in entries:
                self.add(minutes)

    def add(self, minutes: int) -> None:
        self.entries.append(checked_minutes(minutes))

    def total_minutes(self) -> int:
        return sum(self.entries)
