task = {
    "title": "Read names",
    "minutes": 25,
    "owner": None,
}
print(task["title"])
task["minutes"] = 30
task["done"] = False
print(task)
removed_owner = task.pop("owner")
print(removed_owner)
print("owner" in task)
print(len(task))
