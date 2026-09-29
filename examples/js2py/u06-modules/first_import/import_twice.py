import task_rules as first
import task_rules as second

print("Same module:", first is second)
print("Buffered:", second.add_buffer(20))
