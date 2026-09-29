def display_minutes(minutes):
    raise ValueError("display rule is broken")


raw = "25"
try:
    minutes = int(raw)
    display_minutes(minutes)
except ValueError:
    print("Bad input")
