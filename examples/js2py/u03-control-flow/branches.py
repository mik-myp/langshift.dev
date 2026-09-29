minutes = 25
if minutes < 0:
    print("Invalid estimate")
elif minutes == 0:
    print("No time required")
elif minutes <= 25:
    print("Short session")
else:
    print("Long session")
print("Checked")
