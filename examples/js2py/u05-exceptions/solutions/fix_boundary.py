def read_minutes(task):
    raw = task["minutes"]
    if type(raw) is not str:
        raise TypeError("minutes must be text")
    try:
        return int(raw)
    except ValueError:
        return None


print(read_minutes({"minutes": "20"}))
print(read_minutes({"minutes": "bad"}))
print(read_minutes({"minutes": "0"}))
