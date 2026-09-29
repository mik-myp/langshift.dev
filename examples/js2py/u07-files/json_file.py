import json
from pathlib import Path

output = Path(__file__).resolve().parent / "_output"
output.mkdir(exist_ok=True)
path = output / "profile.json"
value = {"title": "学习", "minutes": 20, "done": False, "note": None}
with path.open("w", encoding="utf-8", newline="\n") as stream:
    result = json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write("\n")
print("dump returned:", result)
with path.open("r", encoding="utf-8") as stream:
    restored = json.load(stream)
print("Title:", restored["title"])
print("Equal value:", restored == value)
