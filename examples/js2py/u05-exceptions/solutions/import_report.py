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


def build_report(rows):
    accepted = []
    rejected = []
    total_minutes = 0
    for number, row in enumerate(rows, start=1):
        title = row["title"]
        raw = row["minutes"]
        try:
            minutes = parse_minutes(raw)
        except ValueError as error:
            rejected.append({"row": number, "title": title, "reason": str(error)})
        else:
            accepted.append({"title": title, "minutes": minutes})
            total_minutes = total_minutes + minutes
    return {
        "accepted": accepted,
        "rejected": rejected,
        "total_minutes": total_minutes,
    }


rows = [
    {"title": "Read", "minutes": " 20 "},
    {"title": "Typo", "minutes": "twenty"},
    {"title": "Zero", "minutes": "0"},
    {"title": "Negative", "minutes": "-5"},
    {"title": "Practice", "minutes": "35"},
]
report = build_report(rows)
print("Accepted:", report["accepted"])
print("Rejected:", report["rejected"])
print("Total:", report["total_minutes"])
print("Source first:", rows[0])
