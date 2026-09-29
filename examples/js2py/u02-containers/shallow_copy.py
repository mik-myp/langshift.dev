original = {"title": "Read", "tags": ["python"]}
draft = original.copy()
print(draft is original)
print(draft["tags"] is original["tags"])
draft["title"] = "Practice"
draft["tags"].append("basics")
print(original["title"])
print(original["tags"])
print(draft["title"])
