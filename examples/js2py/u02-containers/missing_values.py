task = {"title": "", "owner": None}
print("owner" in task)
print(task.get("owner"))
print("deadline" in task)
print(task.get("deadline"))
print(task.get("owner", "unassigned"))
print(task.get("deadline", "unassigned"))
print("[" + task.get("title", "Untitled") + "]")
print("deadline" in task)
