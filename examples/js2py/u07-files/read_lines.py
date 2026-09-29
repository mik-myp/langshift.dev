from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures" / "notes.txt"
with path.open("r", encoding="utf-8") as stream:
    for number, line in enumerate(stream, start=1):
        print(number, repr(line))
