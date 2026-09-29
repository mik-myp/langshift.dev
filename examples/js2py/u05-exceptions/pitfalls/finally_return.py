def convert(raw):
    try:
        return int(raw)
    finally:
        return 0


print("Overridden:", convert("25"))
print("Hidden:", convert("bad"))
