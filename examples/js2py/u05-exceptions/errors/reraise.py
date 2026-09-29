def read_minutes(raw):
    try:
        return int(raw)
    except ValueError:
        print("Context: parsing Read")
        raise


print(read_minutes("bad"))
