values = [10, 20]
total = 0
for minutes in values:
    total = total + minutes
assert total == 30, "the known fixture must total 30"
print(total)
