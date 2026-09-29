from estimates import parse_minutes, select_minutes, summarize


def main() -> None:
    values = parse_minutes("[30, 0, 90, 15]")
    selected = select_minutes(values, budget=45)
    print(selected)
    print(summarize(selected))
    print(select_minutes(values))


if __name__ == "__main__":
    main()
