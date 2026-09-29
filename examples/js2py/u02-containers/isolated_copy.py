original = {"title": "Read", "tags": ["python"]}
draft = original.copy()
draft["tags"] = original["tags"].copy()
draft["title"] = "Practice"
draft["tags"].append("basics")
print(original["title"])
print(original["tags"])
print(draft["title"])
print(draft["tags"])
print(draft["tags"] is original["tags"])
