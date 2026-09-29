import sys
from importlib.metadata import version

import humanize

print("Python:", sys.version.split()[0])
print("Executable:", sys.executable)
print("Isolated:", sys.prefix != sys.base_prefix)
print("Distribution:", version("humanize"))
print("Imported from:", humanize.__file__)
print("Size:", humanize.naturalsize(1536, binary=True))
