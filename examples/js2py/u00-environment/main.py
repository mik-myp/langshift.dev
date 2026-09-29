"""A local learning program, not a web server or an input-validation example."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("tasks.json")


def build_report(tasks):
    """Summarize the trusted task list shipped with this lesson."""
    completed = 0
    for task in tasks:
        if task["done"]:
            completed += 1

    total = len(tasks)
    pending = total - completed
    return f"Tasks: {total} | Done: {completed} | Pending: {pending}"


def main():
    tasks = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(build_report(tasks))


if __name__ == "__main__":
    main()
