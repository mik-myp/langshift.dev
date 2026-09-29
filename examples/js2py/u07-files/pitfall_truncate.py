from pathlib import Path

output = Path(__file__).resolve().parent / "_output"
output.mkdir(exist_ok=True)
path = output / "truncation.txt"
with path.open("w", encoding="utf-8", newline="\n") as stream:
    stream.write("Original notes\n")
try:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        raise ValueError("formatting failed before write")
except ValueError:
    print("Closed:", stream.closed)
with path.open("r", encoding="utf-8") as stream:
    print("Remaining:", repr(stream.read()))
