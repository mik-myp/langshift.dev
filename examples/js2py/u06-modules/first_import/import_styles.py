import task_rules as rules
from task_rules import DEFAULT_MINUTES
from task_rules import add_buffer as buffered

print("Alias:", rules.DEFAULT_MINUTES)
print("Direct names:", DEFAULT_MINUTES, buffered(20))
