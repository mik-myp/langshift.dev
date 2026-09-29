"""Independent variation: a small, bounded batch with an owner and a deadline."""
import asyncio
from scheduling import drain


def normalize(title):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be non-empty text")
    return title.strip()


async def transform_batch(titles, fetch, *, limit=2, deadline=1.0):
    if not 1 <= limit <= 4 or not 0 < deadline <= 30:
        raise ValueError("invalid batch budget")
    if len(titles) > 8:
        raise ValueError("at most eight titles")
    normalized = [normalize(title) for title in titles]  # Pure work stays sync.
    slots = asyncio.Semaphore(limit)

    async def one(title):
        async with slots:
            return await fetch(title)

    tasks = []
    try:
        async with asyncio.timeout(deadline):
            tasks = [asyncio.create_task(one(title)) for title in normalized]
            # Input-order observation, not a claim of fail-fast supervision.
            return [await task for task in tasks]
    finally:
        await drain(tasks)
