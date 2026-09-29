import asyncio


async def work():
    print("body:before-await")
    await asyncio.sleep(0)
    print("body:after-await")


async def main():
    pending = work()
    print("caller:after-call")
    await pending


if __name__ == "__main__":
    asyncio.run(main())
