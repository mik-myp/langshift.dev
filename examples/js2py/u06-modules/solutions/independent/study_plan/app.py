from .summary import build_plan


def main():
    rows = [
        {"title": "Read", "minutes": " 20 "},
        {"title": "Typo", "minutes": "twenty"},
        {"title": "Zero", "minutes": "0"},
        {"title": "Negative", "minutes": "-5"},
        {"title": "Practice", "minutes": "35"},
    ]
    plan = build_plan(rows)
    print("Accepted:", plan["accepted"])
    print("Rejected:", plan["rejected"])
    print("Total:", plan["total_minutes"])
    print("Source first:", rows[0])


if __name__ == "__main__":
    main()
