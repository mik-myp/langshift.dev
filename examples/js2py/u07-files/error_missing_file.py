from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures" / "absent.txt"
with path.open("r", encoding="utf-8") as stream:
    print("Entered block")
    print(stream.read())
