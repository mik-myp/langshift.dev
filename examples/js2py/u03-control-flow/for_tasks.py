tasks = [
    {"title": "Read branches", "minutes": 20, "done": True},
    {"title": "Practice loops", "minutes": 35, "done": False},
    {"title": "Check boundaries", "minutes": 0, "done": False},
]
total = 0
pending = 0
for task in tasks:
    total = total + task["minutes"]
    if not task["done"]:
        pending = pending + 1
print(f"Tasks: {len(tasks)}; total: {total} minutes")
print(f"Pending: {pending}")
