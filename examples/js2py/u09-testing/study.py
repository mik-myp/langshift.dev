def pending_minutes(tasks):
    if type(tasks) is not list:
        raise ValueError("tasks must be a list")
    total = 0
    for task in tasks:
        if type(task) is not dict or set(task) != {"minutes", "done"}:
            raise ValueError("each task needs exactly minutes and done")
        minutes = task["minutes"]
        if type(minutes) is not int or minutes < 0:
            raise ValueError("minutes must be a nonnegative int")
        if type(task["done"]) is not bool:
            raise ValueError("done must be bool")
        if not task["done"]:
            total = total + minutes
    return total
