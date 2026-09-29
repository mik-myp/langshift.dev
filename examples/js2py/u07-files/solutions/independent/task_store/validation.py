def validate_tasks(value):
    if type(value) is not list:
        raise ValueError("tasks must be a list")
    tasks = []
    for number, row in enumerate(value, start=1):
        if type(row) is not dict:
            raise ValueError(f"task {number} must be an object")
        if set(row) != {"title", "minutes", "done"}:
            raise ValueError(f"task {number} must contain exactly title, minutes, done")
        title = row["title"]
        minutes = row["minutes"]
        done = row["done"]
        if type(title) is not str or title.strip() == "":
            raise ValueError(f"task {number} title must be non-empty text")
        if type(minutes) is not int or minutes < 0:
            raise ValueError(f"task {number} minutes must be a non-negative integer")
        if type(done) is not bool:
            raise ValueError(f"task {number} done must be a boolean")
        tasks.append({"title": title, "minutes": minutes, "done": done})
    return tasks
