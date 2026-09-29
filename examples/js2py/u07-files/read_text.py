from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures" / "notes.txt"
with path.open("r", encoding="utf-8") as stream:
    print("Inside closed:", stream.closed)
    text = stream.read()
print("Text:", repr(text))
print("After closed:", stream.closed)
