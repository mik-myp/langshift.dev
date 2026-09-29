default_minutes = 20


def make_task(title, minutes=default_minutes):
    return {"title": title, "minutes": minutes}


default_minutes = 35
print(make_task("Read")["minutes"])
print(make_task("Practice", 0)["minutes"])
print(make_task("Unknown", None)["minutes"])
print(make_task("Explicit", default_minutes)["minutes"])
