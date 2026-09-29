tasks = [
    {"title": "Finished", "minutes": 10, "done": True},
    {"title": "Long practice", "minutes": 35, "done": False},
    {"title": "Zero estimate", "minutes": 0, "done": False},
    {"title": "Read", "minutes": 20, "done": False},
]
budget = 20
found = None
for task in tasks:
    print(f"Check: {task['title']}")
    if task["done"]:
        continue
    if task["minutes"] <= budget:
        found = task
        break
if found is None:
    print("No match")
else:
    print(f"First match: {found['title']}")
