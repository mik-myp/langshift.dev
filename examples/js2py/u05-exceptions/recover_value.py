for raw in ["25", "bad", "0"]:
    print("Input:", repr(raw))
    try:
        minutes = int(raw)
        print("Converted:", minutes)
    except ValueError as error:
        print("Rejected:", error)
    print("Next item")
