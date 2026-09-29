"""Expected failure: a coroutine object is single-use, unlike a completed Task."""
import asyncio


async def value():
    return 42


async def main():
    pending = value()
    print(await pending, flush=True)
    print(await pending)


if __name__ == "__main__":
    asyncio.run(main())
