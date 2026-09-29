def add_buffer(minutes):
    return minutes + 5


def prepare_demo():
    print("Preparing demo")
    return [20, 35]


def main():
    print("Demo total:", sum(prepared))


prepared = prepare_demo()
if __name__ == "__main__":
    main()
