"""Capture a real unawaited-coroutine warning without address-dependent output."""
import asyncio
import gc
import warnings


async def main():
    events = []

    async def work():
        events.append("ran")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", RuntimeWarning)
        pending = work()
        del pending
        gc.collect()  # Diagnostic demonstration, NOT resource management.
    assert any("was never awaited" in str(w.message) for w in caught)
    print(f"events={events}; RuntimeWarning: coroutine was never awaited")


if __name__ == "__main__":
    asyncio.run(main())
