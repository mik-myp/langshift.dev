try:
    int("bad")
except Exception:
    print("Broad handler ran")
except ValueError:
    print("Specific handler ran")

try:
    int("bad")
except ValueError:
    print("Specific handler ran")
except Exception:
    print("Broad handler ran")
