tasks = [
    {"title": "Read branches", "minutes": 20, "done": False},
    {"title": "Review loops", "minutes": 30, "done": True},
    {"title": "Try empty input", "minutes": 0, "done": False},
    {"title": "Estimate later", "minutes": None, "done": False},
    {"title": "Missing estimate", "done": False},
    {"title": "Repair estimate", "minutes": -5, "done": False},
]
budget = 20
pending_count = 0
known_minutes = 0
unknown_count = 0
invalid_count = 0
ready_titles = []
for task in tasks:
    if task["done"]:
        continue
    pending_count = pending_count + 1
    minutes = task.get("minutes")
    if minutes is None:
        unknown_count = unknown_count + 1
    elif minutes < 0:
        invalid_count = invalid_count + 1
    else:
        known_minutes = known_minutes + minutes
        if minutes <= budget:
            ready_titles.append(task["title"])
print(f"Tasks: {len(tasks)}; pending: {pending_count}")
print(f"Known pending time: {known_minutes} minutes")
print(f"Unknown: {unknown_count}; invalid: {invalid_count}")
print(f"Ready within {budget} minutes each: {len(ready_titles)}")
for number, title in enumerate(ready_titles, start=1):
    print(f"{number}. {title}")
