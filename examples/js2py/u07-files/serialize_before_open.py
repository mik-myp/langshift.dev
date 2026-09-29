import json
from pathlib import Path


def save_json(path, value):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text + "\n")


def main():
    output = Path(__file__).resolve().parent / "_output"
    output.mkdir(exist_ok=True)
    path = output / "serialization.json"
    save_json(path, {"saved": True})
    with path.open("r", encoding="utf-8") as stream:
        before = stream.read()
    try:
        save_json(path, {"tags": {"python"}})
    except TypeError:
        print("Serialization refused")
    with path.open("r", encoding="utf-8") as stream:
        print("Unchanged:", stream.read() == before)


if __name__ == "__main__":
    main()
