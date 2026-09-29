def parse_minutes(raw):
    if type(raw) is not str:
        raise TypeError("minutes must be text")
    minutes = int(raw)
    if minutes < 0:
        raise ValueError("minutes must be non-negative")
    return minutes


def replace_estimate(task, raw):
    minutes = parse_minutes(raw)
    task["minutes"] = minutes
    task["changes"].append("estimate changed")


task = {"title": "Read", "minutes": 20, "changes": []}
try:
    replace_estimate(task, "-5")
except ValueError as error:
    print("Rejected:", error)
print(task)
replace_estimate(task, "0")
print(task)
