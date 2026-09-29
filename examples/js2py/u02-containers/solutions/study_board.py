template = {"title": "Untitled", "topics": ["python"], "minutes": 20, "owner": None}

first = template.copy()
first["topics"] = template["topics"].copy()
first["title"] = "Read lists"

second = template.copy()
second["topics"] = template["topics"].copy()
second["title"] = "Practice dictionaries"
second["topics"].append("copy")
second["minutes"] = 35
second.pop("owner")

plans = [first, second]
total_minutes = plans[0]["minutes"] + plans[1]["minutes"]
print(f"Plans: {len(plans)}; total: {total_minutes} minutes")
print(plans[0]["title"])
print(plans[1]["title"])
print(template["topics"])
print(plans[0]["topics"])
print(plans[1]["topics"])
print("owner" in plans[0])
print(plans[0]["owner"] is None)
print("owner" in plans[1])
print(plans[0]["topics"] is plans[1]["topics"])
