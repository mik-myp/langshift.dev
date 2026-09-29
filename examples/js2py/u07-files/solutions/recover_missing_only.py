import json
from pathlib import Path


def load_or_empty(path):
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except FileNotFoundError:
        return []
    if type(value) is not list:
        raise ValueError("tasks must be a list")
    return value


def main():
    output = Path(__file__).resolve().parent / "_output"
    output.mkdir(exist_ok=True)
    path = output / "repair.json"
    original = "{broken\n"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(original)
    try:
        tasks = load_or_empty(path)
    except json.JSONDecodeError:
        print("Refused damaged JSON")
        with path.open("r", encoding="utf-8") as stream:
            print("Unchanged:", stream.read() == original)
        return
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(tasks, stream)


if __name__ == "__main__":
    main()
