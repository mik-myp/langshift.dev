def total_minutes(values):
    total = 0
    for minutes in values:
        total = total + minutes
        return total
    return total


print(total_minutes([10, 20]))
print(total_minutes([]))
