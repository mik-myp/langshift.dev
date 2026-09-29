def add_buffer(minutes):
    return minutes + 5


def prepare_demo():
    print("Preparing demo")
    return [20, 35]


def main():
    prepared = prepare_demo()
    print("Demo total:", sum(prepared))


if __name__ == "__main__":
    main()
