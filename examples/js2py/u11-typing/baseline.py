# The understood, unannotated function to annotate before reading estimates.py.
def select_minutes(values, budget=None):
    selected = []
    used = 0
    for value in values:
        if budget is None or used + value <= budget:
            selected.append(value)
            used += value
    return selected
