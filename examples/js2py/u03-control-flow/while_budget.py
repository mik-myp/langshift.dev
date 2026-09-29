remaining = 50
blocks = 0
while remaining > 0:
    if remaining >= 20:
        used = 20
    else:
        used = remaining
    print(f"Block: {used} minutes")
    remaining = remaining - used
    blocks = blocks + 1
print(f"Blocks: {blocks}; remaining: {remaining}")
