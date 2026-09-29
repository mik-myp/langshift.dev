import json
from pathlib import Path

output = Path(__file__).resolve().parent / "_output"
output.mkdir(exist_ok=True)
path = output / "two-documents.json"
with path.open("w", encoding="utf-8", newline="\n") as stream:
    json.dump({"part": 1}, stream)
    json.dump({"part": 2}, stream)
with path.open("r", encoding="utf-8") as stream:
    print("Written:", stream.read())
with path.open("r", encoding="utf-8") as stream:
    json.load(stream)
