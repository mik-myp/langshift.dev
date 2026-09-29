class WrongNotebook:
    entries: list[str] = []  # One class-level list, not one list per instance.


first = WrongNotebook()
second = WrongNotebook()
first.entries.append("Read")
print(second.entries)
