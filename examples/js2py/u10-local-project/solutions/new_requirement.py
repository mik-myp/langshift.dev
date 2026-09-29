from task_app.validation import validate_tasks


def plan_within_budget(tasks, budget):
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative int")
    checked = validate_tasks(tasks)
    selected = []
    used = 0
    for task in checked:
        if not task["done"] and used + task["minutes"] <= budget:
            selected.append(task)
            used = used + task["minutes"]
    return selected, used
