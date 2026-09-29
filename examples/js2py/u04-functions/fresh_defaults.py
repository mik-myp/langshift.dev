def make_task(title, tags=None):
    if tags is None:
        tags = []
    else:
        tags = tags.copy()
    return {"title": title, "tags": tags}


first = make_task("Read")
second = make_task("Practice")
first["tags"].append("python")
print(first["tags"])
print(second["tags"])
print(first["tags"] is second["tags"])
source_tags = ["python"]
third = make_task("Review", source_tags)
third["tags"].append("copy")
print(source_tags)
print(third["tags"])
print(third["tags"] is source_tags)
