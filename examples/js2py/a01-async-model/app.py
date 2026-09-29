import asyncio
from capacity import bounded
from ownership import cancelled, timed_out
from scheduling import blocking, creation, offloaded, scheduled, sequential


async def main():
    for name, demo in [
        ("creation", creation), ("sequential", sequential),
        ("scheduled", scheduled), ("blocking", blocking),
        ("offloaded", offloaded), ("cancelled", cancelled), ("timeout", timed_out),
    ]:
        print(f"{name}: {' | '.join(await demo())}")
    print(f"bounded: {await bounded()}")


if __name__ == "__main__":
    asyncio.run(main())
