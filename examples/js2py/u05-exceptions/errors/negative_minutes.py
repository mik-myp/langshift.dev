def parse_minutes(raw):
    if type(raw) is not str:
        raise TypeError("minutes must be text")
    minutes = int(raw)
    if minutes < 0:
        raise ValueError("minutes must be non-negative")
    return minutes


print(parse_minutes("-5"))
