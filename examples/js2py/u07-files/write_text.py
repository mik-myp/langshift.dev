from pathlib import Path

output = Path(__file__).resolve().parent / "_output"
output.mkdir(exist_ok=True)
path = output / "note.txt"
with path.open("w", encoding="utf-8", newline="\n") as stream:
    count = stream.write("学习 Python\n")
print("Characters written:", count)
with path.open("r", encoding="utf-8") as stream:
    print("Read back:", repr(stream.read()))
