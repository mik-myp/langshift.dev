def replace_local(task):
    task = {"title": "Local", "tags": []}
    return task


def add_topic(task, topic):
    task["tags"].append(topic)


original = {"title": "Read", "tags": ["python"]}
replacement = replace_local(original)
print(original["title"])
print(replacement["title"])
print(replacement is original)
result = add_topic(original, "functions")
print(result)
print(original["tags"])
