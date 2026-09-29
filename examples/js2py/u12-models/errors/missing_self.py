class WrongTask:
    def label():  # Intentional: no parameter to receive the bound instance.
        return "Read"


print(WrongTask().label())
