import json
from pathlib import Path

from .rules import complete_title, summarize
from .storage import load_tasks, save_tasks


def initial_tasks():
    return [
        {"title": "Read", "minutes": 20, "done": False},
        {"title": "Practice", "minutes": 35, "done": False},
        {"title": "Review", "minutes": 0, "done": True},
    ]


def main(path=None):
    if path is None:
        path = Path(__file__).resolve().parent.parent / "_output" / "tasks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        tasks = load_tasks(path)
    except FileNotFoundError:
        print("Source: new file")
        tasks = initial_tasks()
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        print("Invalid existing data; refusing to save")
        raise
    else:
        print("Source: existing file")
    result, changed = complete_title(tasks, "Read")
    summary = summarize(result)
    save_tasks(path, result)
    print("Changed:", changed)
    print("Tasks:", summary["count"])
    print("Pending minutes:", summary["pending_minutes"])


if __name__ == "__main__":
    main()
