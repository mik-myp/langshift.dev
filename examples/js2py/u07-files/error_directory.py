from pathlib import Path

path = Path(__file__).resolve().parent / "fixtures"
with path.open("r", encoding="utf-8") as stream:
    print(stream.read())
