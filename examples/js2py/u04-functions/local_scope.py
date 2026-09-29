label = "module"
limit = 20


def format_label(label):
    prefix = "local"
    return f"{prefix}: {label}"


def current_limit():
    return limit


print(format_label("Read"))
print(label)
print(current_limit())
limit = 35
print(current_limit())
