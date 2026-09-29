def with_buffer(minutes, extra=5):
    result = minutes + extra
    return result


first = with_buffer(20)
second = with_buffer(0, extra=0)
print(first)
print(second)
