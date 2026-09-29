"""Runs successfully but violates the owner's cancellation contract."""
import asyncio


async def wrong(entered):
    entered.set()
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        return "pretend-success"


async def main():
    entered = asyncio.Event()
    task = asyncio.create_task(wrong(entered))
    await entered.wait()
    task.cancel()
    print(f"result={await task} cancelled={task.cancelled()}")


if __name__ == "__main__":
    asyncio.run(main())
