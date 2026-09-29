import humanize


def main():
    sizes = [512, 1024, 0]
    total = 0
    for size in sizes:
        total = total + size
    print("Files:", len(sizes))
    print("Bytes:", total)
    print("Readable:", humanize.naturalsize(total, binary=True))


if __name__ == "__main__":
    main()
