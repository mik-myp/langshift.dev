import asyncio
import pytest
from solutions.batch import transform_batch


def test_order_and_pure_validation():
    async def scenario():
        called = []
        async def fetch(title):
            called.append(title)
            await asyncio.sleep(0)
            return title.upper()
        assert await transform_batch([" a ", "b"], fetch) == ["A", "B"]
        called.clear()
        with pytest.raises(ValueError):
            await transform_batch(["ok", " "], fetch)
        assert called == []
    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["failure", "timeout", "cancel"])
def test_no_children_survive_owner(mode):
    async def scenario():
        entered, never = asyncio.Event(), asyncio.Event()
        live = set()
        async def fetch(title):
            live.add(title)
            try:
                if title == "a":
                    entered.set()
                    if mode == "failure":
                        raise LookupError("simulated")
                await never.wait()
            finally:
                live.remove(title)
        owner = asyncio.create_task(transform_batch(
            ["a", "b", "c"], fetch, limit=2,
            deadline=0.01 if mode == "timeout" else 5,
        ))
        await entered.wait()
        if mode == "cancel":
            owner.cancel()
        error = {"failure": LookupError, "timeout": TimeoutError,
                 "cancel": asyncio.CancelledError}[mode]
        with pytest.raises(error):
            await owner
        assert live == set()
        assert not [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    asyncio.run(scenario())


def test_empty_and_capacity_policy():
    async def scenario():
        async def fetch(title):
            return title
        assert await transform_batch([], fetch) == []
        with pytest.raises(ValueError):
            await transform_batch(["x"] * 9, fetch)
        with pytest.raises(ValueError):
            await transform_batch(["x"], fetch, limit=0)
    asyncio.run(scenario())
