import asyncio
import tempfile


async def hold_file(events, entered, release, handles):
    handle = tempfile.TemporaryFile(mode="w+t", encoding="utf-8")
    handles.append(handle)  # Test can inspect the actual resource after exit.
    try:
        events.append("file:opened")
        entered.set()
        await release.wait()
        events.append("work:completed")
    finally:
        handle.close()
        events.append("file:closed")


async def cancelled():
    events, handles = [], []
    entered, release = asyncio.Event(), asyncio.Event()
    task = asyncio.create_task(hold_file(events, entered, release, handles))
    try:
        await entered.wait()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            events.append("owner:cancelled")
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert task.cancelled() and handles[0].closed
    return events


async def timed_out():
    events, handles = [], []
    try:
        # Zero deliberately expires at the next loop turn, after file acquisition.
        async with asyncio.timeout(0):
            await hold_file(events, asyncio.Event(), asyncio.Event(), handles)
    except TimeoutError:
        events.append("owner:timeout")
    assert handles[0].closed
    return events
