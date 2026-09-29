tasks = [
    {"title": "Read", "done": True},
    {"title": "Practice", "done": False},
    {"title": "Review", "done": False},
]
titles = []
for task in tasks:
    if not task["done"]:
        titles.append(task["title"])
compact_titles = [task["title"] for task in tasks if not task["done"]]
print(titles)
print(compact_titles)
print(titles == compact_titles)
print(titles is compact_titles)
