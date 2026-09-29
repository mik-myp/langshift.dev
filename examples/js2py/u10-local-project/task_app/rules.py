from .validation import validate_tasks


def complete_title(tasks, title):
    if type(title) is not str or not title.strip():
        raise ValueError("title must be nonempty text")
    result = validate_tasks(tasks)
    changed = 0
    for task in result:
        if task["title"] == title and not task["done"]:
            task["done"] = True
            changed = changed + 1
    return result, changed


def summarize(tasks):
    checked = validate_tasks(tasks)
    pending = 0
    for task in checked:
        if not task["done"]:
            pending = pending + task["minutes"]
    return {"count": len(checked), "pending_minutes": pending}
