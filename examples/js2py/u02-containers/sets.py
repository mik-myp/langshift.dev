tags = {"python", "basics", "python"}
print(len(tags))
print("python" in tags)
tags.add("practice")
tags.discard("missing")
print(sorted(tags))
required = {"python", "sql"}
print(sorted(required - tags))
print(sorted(required & tags))
print(sorted(required | tags))
print(len(set()))
