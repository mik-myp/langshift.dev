from pathlib import Path

output = Path(__file__).resolve().parent / "_output"
output.mkdir(exist_ok=True)
path = output / "once.txt"
with path.open("x", encoding="utf-8", newline="\n") as stream:
    stream.write("Created once\n")
print("Created once")
