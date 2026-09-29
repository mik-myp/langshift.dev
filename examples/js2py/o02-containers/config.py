from pathlib import Path


def data_directory(environ) -> Path:
    value = environ.get("OPS_DATA_DIR", "")
    directory = Path(value)
    if not value or not directory.is_absolute() or not directory.is_dir():
        raise ValueError("OPS_DATA_DIR must name an existing absolute directory")
    return directory
