def pending_minutes(tasks):
    total = 0
    for task in tasks:
        if task["done"]:
            total = total + task["minutes"]
    return total
