# Intentionally unannotated; default mypy checking does not inspect this body.
def broken():
    value = 1 + "2"
    return value


broken()
