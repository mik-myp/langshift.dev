import json
from pathlib import Path

from .storage import load_tasks, save_tasks


def main():
    output = Path(__file__).resolve().parent.parent / "_output"
    output.mkdir(exist_ok=True)
    path = output / "tasks.json"
    try:
        tasks = load_tasks(path)
    except FileNotFoundError:
        print("Source: new file")
        tasks = [
            {"title": "Read", "minutes": 20, "done": False},
            {"title": "练习", "minutes": 35, "done": False},
        ]
    except json.JSONDecodeError:
        print("Invalid JSON; file unchanged")
        raise
    except UnicodeDecodeError:
        print("Invalid UTF-8; file unchanged")
        raise
    except ValueError:
        print("Invalid task data; file unchanged")
        raise
    else:
        print("Source: existing file")
    for task in tasks:
        if task["title"] == "Read":
            task["done"] = True
    save_tasks(path, tasks)
    pending = 0
    for task in tasks:
        if not task["done"]:
            pending = pending + task["minutes"]
    print("Saved:", len(tasks))
    print("Pending minutes:", pending)
    print("Tasks:", tasks)


if __name__ == "__main__":
    main()
