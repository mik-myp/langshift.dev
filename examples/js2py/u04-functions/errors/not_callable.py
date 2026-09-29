def is_pending(task):
    return not task["done"]


task = {"title": "Read", "done": False}
rule = is_pending(task)
print(rule(task))
