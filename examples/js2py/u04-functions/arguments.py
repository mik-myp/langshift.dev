def estimate(minutes, repeats=1, extra=5):
    return minutes * repeats + extra


print(estimate(20))
print(estimate(20, 2))
print(estimate(20, extra=0))
print(estimate(repeats=2, minutes=20, extra=0))
