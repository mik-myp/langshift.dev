saved = {"title": "Read", "tags": ["python"]}
draft = saved.copy()
draft["tags"] = saved["tags"].copy()
draft["tags"].append("review")
print(saved["tags"])
print(draft["tags"])
print(saved["tags"] is draft["tags"])
