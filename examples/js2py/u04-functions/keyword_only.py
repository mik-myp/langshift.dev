def make_label(title, *, done=False):
    if done:
        return f"[done] {title}"
    return f"[todo] {title}"


print(make_label("Read"))
print(make_label("Read", done=True))
