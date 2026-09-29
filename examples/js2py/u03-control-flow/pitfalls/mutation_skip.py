tasks = [
    {"title": "First", "done": True},
    {"title": "Second", "done": True},
    {"title": "Third", "done": False},
]
for index, task in enumerate(tasks):
    if task["done"]:
        tasks.pop(index)
print(tasks)
