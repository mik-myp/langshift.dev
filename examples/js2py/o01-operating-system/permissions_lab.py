"""Change modes only on our own temporary file, restoring before cleanup."""
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory


def observe() -> list[str]:
    if os.geteuid() == 0:
        raise RuntimeError("run as an ordinary user; root bypasses this permission experiment")
    with TemporaryDirectory(prefix="js2py-permissions-") as temp:
        directory = Path(temp)
        file = directory / "fictional-config.txt"
        previous = os.umask(0o077)
        try:
            file.write_text("not-a-credential\n")
        finally:
            os.umask(previous)
        lines = [f"directory_mode={oct(stat.S_IMODE(directory.stat().st_mode))}",
                 f"file_mode={oct(stat.S_IMODE(file.stat().st_mode))}"]
        file.chmod(0o000)
        try:
            try:
                file.read_text()
            except PermissionError:
                lines.append("read_without_permission=denied")
            else:
                raise AssertionError("permission was bypassed; check user/ACL/platform before accepting")
        finally:
            file.chmod(0o600)
        lines.append(f"restored_read={file.read_text().strip() == 'not-a-credential'}")
        return lines


if __name__ == "__main__":
    print("\n".join(observe()))
