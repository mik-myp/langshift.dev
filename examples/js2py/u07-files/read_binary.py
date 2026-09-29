from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures" / "notes.txt"
with path.open("rb") as stream:
    raw = stream.read()
print("Is bytes:", type(raw) is bytes)
print("Decoded:", repr(raw.decode("utf-8")))
