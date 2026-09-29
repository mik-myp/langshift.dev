def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags


first = add_tag("python")
print(first)
second = add_tag("functions")
print(first)
print(second)
print(first is second)
