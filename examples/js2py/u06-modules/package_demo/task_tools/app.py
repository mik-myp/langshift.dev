from .report import buffered_total


def main():
    minutes = [20, 35]
    print("Package total:", buffered_total(minutes))


if __name__ == "__main__":
    main()
