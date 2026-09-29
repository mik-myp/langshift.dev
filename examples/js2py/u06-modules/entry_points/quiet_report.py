def build_total(minutes):
    return sum(minutes)


def main():
    minutes = [20, 35]
    print("Business total:", build_total(minutes))


if __name__ == "__main__":
    main()
