def make_label(title, *, done=False):
    print("Body ran")
    if done:
        return f"[done] {title}"
    return f"[todo] {title}"


print(make_label("Read", True))
