from pathlib import Path


def observe(path, mode):
    stream = None
    try:
        with path.open("r", encoding="utf-8") as stream:
            print("Inside closed:", stream.closed)
            if mode == "return":
                return "early"
            if mode == "error":
                raise ValueError("inside block")
            stream.read()
        print("After block closed:", stream.closed)
        return "normal"
    finally:
        if stream is None:
            print("No stream acquired")
        else:
            print("Finally closed:", stream.closed)


base = Path(__file__).resolve().parent / "fixtures"
for mode in ["normal", "return", "error", "missing"]:
    print("Mode:", mode)
    if mode == "missing":
        name = "absent.txt"
    else:
        name = "notes.txt"
    try:
        result = observe(base / name, mode)
    except FileNotFoundError:
        print("Caught: FileNotFoundError")
    except ValueError:
        print("Caught: ValueError")
    else:
        print("Result:", result)
