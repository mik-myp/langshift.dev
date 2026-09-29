def is_pending(task):
    return not task["done"]


def select_tasks(tasks, rule):
    selected = []
    for task in tasks:
        if rule(task):
            selected.append(task)
    return selected


tasks = [
    {"title": "Read", "done": True},
    {"title": "Practice", "done": False},
]
rule = is_pending
print(rule is is_pending)
print(rule({"done": False}))
selected = select_tasks(tasks, rule)
print([task["title"] for task in selected])
print(selected is tasks)
