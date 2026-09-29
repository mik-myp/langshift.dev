from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory(prefix="js2py-example-") as directory:
    path = Path(directory) / "note.txt"
    path.write_text("owned temporary data\n", encoding="utf-8")
    print("Inside:", path.exists())
print("After:", path.exists())
