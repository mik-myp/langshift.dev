from pathlib import Path

relative = Path("fixtures") / "notes.txt"
base = Path(__file__).resolve().parent
target = base / relative
print("Cwd:", Path.cwd())
print("Relative:", relative)
print("Absolute:", target.is_absolute())
print("Name:", target.name)
print("Parent name:", target.parent.name)
print("Target:", target)
