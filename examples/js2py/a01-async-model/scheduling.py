"""Order is evidence; elapsed time is not the assertion."""
import asyncio
import threading
import time


async def step(name, events):
    events.append(f"{name}:start")
    await asyncio.sleep(0)  # A deliberate scheduling checkpoint, not fake I/O.
    events.append(f"{name}:end")
    return name


async def creation():
    events = []
    pending = step("A", events)
    events.append("called:no-body-yet")
    await pending
    return events


async def sequential():
    events = []
    await step("A", events)
    await step("B", events)
    return events


async def drain(tasks):
    """Owner cancels unfinished children and observes every terminal result."""
    for task in tasks:
        if not task.done():
            task.cancel()
    return await asyncio.gather(*tasks, return_exceptions=True)


async def scheduled():
    events = []
    entered = [asyncio.Event(), asyncio.Event()]
    release = [asyncio.Event(), asyncio.Event()]

    async def child(index, name):
        events.append(f"{name}:start")
        entered[index].set()
        await release[index].wait()
        events.append(f"{name}:end")

    first = asyncio.create_task(child(0, "A"))
    second = asyncio.create_task(child(1, "B"))
    try:
        await entered[0].wait()
        await entered[1].wait()
        events.append("owner:both-entered")
        release[1].set()
        await second
        release[0].set()
        await first
    finally:
        await drain([first, second])
    return events


async def blocking():
    events = []
    asyncio.get_running_loop().call_soon(events.append, "callback:ran")
    events.append("sync:start")
    time.sleep(0.02)  # Deliberately wrong on the event-loop thread.
    events.append("sync:end")
    assert "callback:ran" not in events
    await asyncio.sleep(0)
    events.append("owner:resumed")
    return events


async def offloaded():
    events = []
    entered = asyncio.Event()
    release = threading.Event()
    loop = asyncio.get_running_loop()

    def blocking_library():
        loop.call_soon_threadsafe(entered.set)
        if not release.wait(5):  # Hang guard, not a speed assertion.
            raise RuntimeError("owner did not release worker")
        return "thread:returned"

    task = asyncio.create_task(asyncio.to_thread(blocking_library))
    try:
        await entered.wait()
        events.append("loop:responsive-while-thread-waits")
    finally:
        release.set()  # Cancelling an await cannot forcibly stop this thread.
        events.append(await task)  # Explicitly join the work we own.
    return events
