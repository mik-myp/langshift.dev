try:
    int(None)
except ValueError:
    print("except")
finally:
    print("finally before propagation")
print("After")
