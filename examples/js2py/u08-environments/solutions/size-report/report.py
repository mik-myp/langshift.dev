import humanize


def total_bytes(sizes):
    if type(sizes) is not list:
        raise ValueError("sizes must be a list")
    total = 0
    for size in sizes:
        if type(size) is not int or size < 0:
            raise ValueError("each size must be a nonnegative int")
        total = total + size
    return total


def main():
    sizes = [1024, 512, 0]
    total = total_bytes(sizes)
    print("Files:", len(sizes))
    print("Bytes:", total)
    print("Readable:", humanize.naturalsize(total, binary=True))


if __name__ == "__main__":
    main()
