task = {"title": "Read", "minutes": 20, "changes": []}
try:
    task["changes"].append("estimate changed")
    task["minutes"] = int("bad")
except ValueError:
    print("Rejected")
print(task)
