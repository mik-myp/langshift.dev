def parse_minutes(raw):
    minutes = int(raw)
    assert minutes >= 0, "minutes must be non-negative"
    return minutes


print(parse_minutes("-5"))
