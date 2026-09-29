print("Before definition")


def add_buffer(minutes):
    print("Inside call")
    return minutes + 5


print("After definition")
result = add_buffer(20)
print(result)
