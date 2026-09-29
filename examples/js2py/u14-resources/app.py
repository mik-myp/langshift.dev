from contextlib import closing
from pathlib import Path

from resources import TextFile, opened_text
from sequences import lines_from, tracked_minutes


def main() -> None:
    events: list[str] = []
    values = tracked_minutes([30, 0], events)
    print(events)
    print(next(values))
    print(events)
    values.close()
    print(events)

    path = Path(__file__).parent / "fixtures" / "lines.txt"
    events = []
    with TextFile(path, events) as handle:
        print(handle.readline().rstrip("\n"))
    print(handle.closed, events)

    events = []
    try:
        with opened_text(path, events) as handle:
            raise ValueError("deliberate body failure")
    except ValueError:
        print(handle.closed, events)

    with closing(lines_from(path)) as lines:
        for line in lines:
            print(line)
            break


if __name__ == "__main__":
    main()
