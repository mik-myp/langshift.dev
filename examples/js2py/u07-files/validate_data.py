import json


def total_minutes(value):
    if type(value) is not list:
        raise ValueError("root must be a list")
    total = 0
    for number, row in enumerate(value, start=1):
        if type(row) is not dict or "minutes" not in row:
            raise ValueError(f"row {number} must be an object with minutes")
        minutes = row["minutes"]
        if type(minutes) is not int or minutes < 0:
            raise ValueError(f"row {number} minutes must be a non-negative integer")
        total = total + minutes
    return total


def main():
    texts = [
        '[{"minutes": 20}, {"minutes": 0}]',
        '{"minutes": 20}',
        '[{"minutes": "20"}]',
        '[{"minutes": true}]',
    ]
    for text in texts:
        value = json.loads(text)
        try:
            total = total_minutes(value)
        except ValueError as error:
            print("Rejected:", error)
        else:
            print("Total:", total)


if __name__ == "__main__":
    main()
