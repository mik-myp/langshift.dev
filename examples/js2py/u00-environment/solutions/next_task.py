"""Reference answer. Read only after attempting the exercise."""


def next_task_title(tasks):
    for task in tasks:
        if not task["done"]:
            return task["title"]
    return "No pending tasks"
