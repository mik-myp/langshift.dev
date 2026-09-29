def parse_minutes(raw):
    if type(raw) is not str:
        raise TypeError("minutes must be text")
    try:
        minutes = int(raw)
    except ValueError as error:
        raise ValueError("minutes must be an integer") from error
    if minutes < 0:
        raise ValueError("minutes must be non-negative")
    return minutes
