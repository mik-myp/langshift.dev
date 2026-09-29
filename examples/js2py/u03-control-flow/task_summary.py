tasks = [
    {"title": "Read branches", "minutes": 20, "done": True},
    {"title": "Practice loops", "minutes": 35, "done": False},
    {"title": "Check boundaries", "minutes": 0, "done": False},
]
done_count = 0
pending_titles = []
remaining = 0
for task in tasks:
    if task["done"]:
        done_count = done_count + 1
    else:
        pending_titles.append(task["title"])
        remaining = remaining + task["minutes"]
pending_count = len(pending_titles)
print(f"Tasks: {len(tasks)}")
print(f"Done: {done_count}; pending: {pending_count}")
print(f"Remaining: {remaining} minutes")
if pending_count > 0:
    average = remaining / pending_count
    print(f"Pending average: {average:.1f} minutes")
else:
    print("Pending average: n/a")
for number, title in enumerate(pending_titles, start=1):
    print(f"{number}. {title}")
