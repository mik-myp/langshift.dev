def classify_minutes(minutes):
    """Classify None or an integer; bool and other input types are excluded."""
    if minutes is None:
        return "unknown"
    if minutes < 0:
        return "invalid"
    return "known"


def build_report(tasks, budget=20):
    """Return a fresh report without changing the supplied task records."""
    report = {
        "pending": 0,
        "known_minutes": 0,
        "unknown": 0,
        "invalid": 0,
        "ready_titles": [],
    }
    for task in tasks:
        if task["done"]:
            continue
        report["pending"] = report["pending"] + 1
        minutes = task.get("minutes")
        category = classify_minutes(minutes)
        if category == "unknown":
            report["unknown"] = report["unknown"] + 1
        elif category == "invalid":
            report["invalid"] = report["invalid"] + 1
        else:
            report["known_minutes"] = report["known_minutes"] + minutes
            if minutes <= budget:
                report["ready_titles"].append(task["title"])
    return report


tasks = [
    {"title": "Read", "minutes": 20, "done": False},
    {"title": "Finished", "minutes": 30, "done": True},
    {"title": "Zero", "minutes": 0, "done": False},
    {"title": "Unknown", "done": False},
    {"title": "Repair", "minutes": -5, "done": False},
]
report = build_report(tasks)
print(f"Pending: {report['pending']}")
print(f"Known: {report['known_minutes']} minutes")
print(f"Unknown: {report['unknown']}; invalid: {report['invalid']}")
print(report["ready_titles"])
empty_report = build_report([])
print(empty_report["pending"])
print(empty_report["ready_titles"])
print(report["ready_titles"])
