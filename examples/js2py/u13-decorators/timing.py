events = []


def record(label):
    events.append("evaluate " + label)

    def decorate(function):
        events.append("apply " + label)
        return function

    return decorate


@record("outer")
@record("inner")
def operation(value):
    events.append("call " + str(value))
    return value


print(events)
operation(4)
operation(5)
print(events)
