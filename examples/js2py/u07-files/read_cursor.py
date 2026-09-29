from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures" / "notes.txt"
with path.open("r", encoding="utf-8") as stream:
    print("First:", repr(stream.read(6)))
    print("Rest:", repr(stream.read()))
    print("At end:", repr(stream.read()))
with path.open("r", encoding="utf-8") as stream:
    print("Reopened:", repr(stream.read(6)))
