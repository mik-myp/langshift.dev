titles = ["Read", "Practice"]
for title in titles:
    print(title)
print(title)
for title in titles:
    title = "Changed"
print(titles)
tasks = [{"title": "Read", "done": False}]
for task in tasks:
    task["done"] = True
print(tasks[0]["done"])
