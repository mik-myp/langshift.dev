import math
import statistics

print("Rounded up:", math.ceil(2.1))
print("Average:", statistics.mean([20, 30]))
try:
    statistics.mean([])
except statistics.StatisticsError:
    print("Empty input has no average")
