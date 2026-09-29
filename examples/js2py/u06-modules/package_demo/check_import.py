import task_tools.app
from task_tools.report import buffered_total

print("App name:", task_tools.app.__name__)
print("Probe total:", buffered_total([0]))
