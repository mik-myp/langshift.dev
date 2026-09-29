def display_minutes(minutes):
    raise ValueError("display rule is broken")


raw = "25"
try:
    minutes = int(raw)
except ValueError:
    print("Bad input")
else:
    display_minutes(minutes)
print("After display")
