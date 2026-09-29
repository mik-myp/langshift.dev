from pathlib import Path

output = Path(__file__).resolve().parent / "_output"
output.mkdir(exist_ok=True)
path = output / "modes.txt"
with path.open("w", encoding="utf-8", newline="\n") as stream:
    stream.write("First\n")
with path.open("a", encoding="utf-8", newline="\n") as stream:
    stream.write("Next\n")
with path.open("r", encoding="utf-8") as stream:
    print("Appended:", repr(stream.read()))
with path.open("w", encoding="utf-8", newline="\n") as stream:
    stream.write("Reset\n")
with path.open("r", encoding="utf-8") as stream:
    print("Replaced:", repr(stream.read()))
