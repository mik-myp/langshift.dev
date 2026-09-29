from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures" / "notes.txt"
try:
    with path.open("r", encoding="ascii") as stream:
        stream.read()
except UnicodeDecodeError:
    print("After error closed:", stream.closed)
    raise
