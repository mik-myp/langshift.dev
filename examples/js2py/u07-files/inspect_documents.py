import json
from pathlib import Path

from validate_data import total_minutes

base = Path(__file__).resolve().parent / "fixtures"
names = [
    "tasks.json",
    "absent.json",
    "invalid-utf8.bin",
    "malformed.json",
    "wrong-root.json",
    "wrong-types.json",
]
for name in names:
    try:
        with (base / name).open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except FileNotFoundError:
        print(f"{name}: missing file")
    except UnicodeDecodeError:
        print(f"{name}: invalid UTF-8")
    except json.JSONDecodeError as error:
        print(f"{name}: invalid JSON at line {error.lineno}, column {error.colno}")
    else:
        try:
            total = total_minutes(value)
        except ValueError as error:
            print(f"{name}: invalid data: {error}")
        else:
            print(f"{name}: total={total}")
