tasks = [
    {"title": "First", "done": True},
    {"title": "Second", "done": True},
    {"title": "Third", "done": False},
]
pending_tasks = []
for task in tasks:
    if not task["done"]:
        pending_tasks.append(task)
print(pending_tasks)
print(len(tasks))
print(pending_tasks is tasks)
