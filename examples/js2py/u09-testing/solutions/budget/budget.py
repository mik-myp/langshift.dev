def remaining_budget(budget, spent):
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative int")
    if type(spent) is not list:
        raise ValueError("spent must be a list")
    total = 0
    for minutes in spent:
        if type(minutes) is not int or minutes < 0:
            raise ValueError("spent items must be nonnegative ints")
        total = total + minutes
    remaining = budget - total
    if remaining < 0:
        return 0
    return remaining
