"""Only a fictional marker in an owned temporary directory; never real credentials."""
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory


def observe() -> list[str]:
    with TemporaryDirectory(prefix="js2py-secret-boundary-") as temp:
        file = Path(temp) / "fictional-secret.txt"
        descriptor = os.open(file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w") as output:
            output.write("not-a-real-credential\n")
        value = file.read_text().strip()
        return [f"file_mode={oct(stat.S_IMODE(file.stat().st_mode))}",
                f"fictional_value_loaded={bool(value)}", "value_is_not_printed=True"]


if __name__ == "__main__":
    print("\n".join(observe()))
