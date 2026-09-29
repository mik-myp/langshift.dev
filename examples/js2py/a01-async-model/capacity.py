import asyncio
from scheduling import drain


class Meter:
    def __init__(self):
        self.active = 0
        self.peak = 0


async def limited_job(index, slots, meter, entered, release):
    async with slots:
        meter.active += 1
        meter.peak = max(meter.peak, meter.active)
        try:
            entered[index].set()
            await release[index].wait()
            return index
        finally:
            meter.active -= 1


async def bounded(limit=2):
    if not 1 <= limit <= 4:
        raise ValueError("limit must be between 1 and 4")
    slots, meter = asyncio.Semaphore(limit), Meter()
    entered = [asyncio.Event() for _ in range(4)]
    release = [asyncio.Event() for _ in range(4)]
    tasks = [
        asyncio.create_task(limited_job(i, slots, meter, entered, release))
        for i in range(4)
    ]
    try:
        for index in range(limit):
            await entered[index].wait()
        assert sum(event.is_set() for event in entered) == limit
        # Release one admitted job, then witness a replacement being admitted.
        for index in range(4):
            release[index].set()
            await tasks[index]
            if index + limit < 4:
                await entered[index + limit].wait()
    finally:
        await drain(tasks)
    assert meter.active == 0
    return f"peak={meter.peak} active={meter.active}"
