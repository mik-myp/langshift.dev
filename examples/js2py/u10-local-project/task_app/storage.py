import json

from .validation import validate_tasks


def load_tasks(path):
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    return validate_tasks(value)


def save_tasks(path, value):
    tasks = validate_tasks(value)
    text = json.dumps(tasks, ensure_ascii=False, indent=2, allow_nan=False)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text + "\n")
