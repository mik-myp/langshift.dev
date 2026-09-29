from study import pending_minutes

result = pending_minutes([{"minutes": 20, "done": False}])
print("Observed:", result)
assert result == 20
print("Checked")
