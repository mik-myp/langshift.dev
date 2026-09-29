def status_label(task):
    if task["done"]:
        return "done"
    if task.get("minutes") is None:
        return "unknown"
    return "pending"


def announce(title):
    print(f"Ready: {title}")


def maybe_announce(title):
    if not title:
        return
    print(f"Ready: {title}")


print(status_label({"done": True, "minutes": None}))
print(status_label({"done": False, "minutes": None}))
print(status_label({"done": False, "minutes": 0}))
result = announce("Read")
print(result)
print(maybe_announce(""))
