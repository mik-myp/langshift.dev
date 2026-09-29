def create_task(title, minutes=None, tags=None):
    if tags is None:
        tags = []
    else:
        tags = tags.copy()
    return {"title": title, "minutes": minutes, "tags": tags, "done": False}


def is_ready(task, budget=20):
    if task["done"]:
        return False
    minutes = task.get("minutes")
    if minutes is None:
        return False
    if minutes < 0:
        return False
    return minutes <= budget


def select_tasks(tasks, rule):
    selected = []
    for task in tasks:
        if rule(task):
            selected.append(task)
    return selected


def make_budget_rule(budget):
    def matches(task):
        return is_ready(task, budget=budget)

    return matches


source_tags = ["python"]
first = create_task("Read", 20, source_tags)
second = create_task("Practice", 35, source_tags)
zero = create_task("Zero", 0)
unknown = create_task("Unknown")
finished = create_task("Finished", 10)
finished["done"] = True
invalid = create_task("Invalid", -5)
tasks = [first, second, zero, unknown, finished, invalid]
first["tags"].append("review")
small_budget = 20
large_budget = 40
small_rule = make_budget_rule(small_budget)
large_rule = make_budget_rule(large_budget)
small = select_tasks(tasks, small_rule)
large = select_tasks(tasks, large_rule)
small_titles = [task["title"] for task in small]
large_titles = [task["title"] for task in large]
print(source_tags)
print(first["tags"])
print(second["tags"])
print(zero["tags"] is unknown["tags"])
print(f"Within {small_budget}: {small_titles}")
print(f"Within {large_budget}: {large_titles}")
print(small is tasks)
print(f"Source tasks: {len(tasks)}")
