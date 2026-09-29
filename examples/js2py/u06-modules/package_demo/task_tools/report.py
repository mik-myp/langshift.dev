from .rules import add_buffer


def buffered_total(minutes):
    total = 0
    for value in minutes:
        total = total + add_buffer(value)
    return total
