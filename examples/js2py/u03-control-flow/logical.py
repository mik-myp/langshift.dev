titles = []
print(bool(titles and titles[0] == "Read"))
print("" or "Untitled")
print("Read" and "Ready")
print(not titles)
minutes = 0
print(minutes or 25)
if minutes is None:
    effective_minutes = 25
else:
    effective_minutes = minutes
print(effective_minutes)
