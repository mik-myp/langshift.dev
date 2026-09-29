from pathlib import Path

path = Path(__file__).resolve().parent / "_output" / "absent-folder" / "note.txt"
with path.open("w", encoding="utf-8") as stream:
    stream.write("This cannot create parent directories")
