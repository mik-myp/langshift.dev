from .rules import parse_minutes


def build_plan(rows, budget=20):
    if type(budget) is not int:
        raise TypeError("budget must be an integer")
    if budget < 0:
        raise ValueError("budget must be non-negative")
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
            if minutes <= budget:
                accepted.append({"title": title, "minutes": minutes})
                total_minutes = total_minutes + minutes
    return {
        "accepted": accepted,
        "rejected": rejected,
        "total_minutes": total_minutes,
    }
