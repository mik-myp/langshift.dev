def convert(raw):
    try:
        minutes = int(raw)
    except ValueError:
        print("except")
        return None
    else:
        print("else")
        return minutes
    finally:
        print("finally")


print("Result:", convert("0"))
print("Result:", convert("bad"))
