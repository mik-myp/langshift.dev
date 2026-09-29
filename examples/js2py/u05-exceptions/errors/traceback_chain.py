def parse_minutes(raw):
    return int(raw)


def task_minutes(task):
    return parse_minutes(task["minutes"])


def build_total(tasks):
    total = 0
    for task in tasks:
        total = total + task_minutes(task)
    return total


print("Starting report")
print(build_total([{"title": "Read", "minutes": "25m"}]))
print("Done")
