from sequences import tracked_minutes

events: list[str] = []
values = tracked_minutes([30, 0], events)
for value in values:
    print(value)
    break
print(events)
values.close()
print(events)
