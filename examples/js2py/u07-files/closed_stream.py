from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures" / "notes.txt"
with path.open("r", encoding="utf-8") as stream:
    text = stream.read()
print("Saved text:", repr(text))
print(stream.read())
