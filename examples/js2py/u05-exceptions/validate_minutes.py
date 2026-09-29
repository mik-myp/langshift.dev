def parse_minutes(raw):
    if type(raw) is not str:
        raise TypeError("minutes must be text")
    minutes = int(raw)
    if minutes < 0:
        raise ValueError("minutes must be non-negative")
    return minutes


for raw in ["25", "0", "-5"]:
    try:
        minutes = parse_minutes(raw)
        print("Accepted:", minutes)
    except ValueError as error:
        print("Rejected:", error)
