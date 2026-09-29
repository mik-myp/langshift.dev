from study import pending_minutes

result = pending_minutes([{"minutes": 20, "done": False}])
assert result == 99
print("Not reached")
