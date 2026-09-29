from pathlib import Path
from observe import observe

if __name__ == "__main__":
    directory = Path(__file__).resolve().parent / "public"
    print("\n".join(observe(directory, "/health.txt")))
