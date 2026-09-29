import os
import sys

print("Name:", __name__)
print("Cwd:", os.getcwd())
print("File:", __file__)
print("First search:", sys.path[0])
