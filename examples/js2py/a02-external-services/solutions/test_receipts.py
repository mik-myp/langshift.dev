import asyncio
import httpx
import pytest

from lifecycle import managed_client
from solutions.receipts import ReceiptProvider, create_receipt

ORIGIN = "http://127.0.0.1:8766"


def test_lost_reply_same_key_one_effect():
    async def scenario():
        provider = ReceiptProvider()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(provider)) as client:
            first = await create_receipt(client, "operation-001")
            assert first == await create_receipt(client, "operation-001") == {"receipt_id": 1}
            assert provider.effects == 1 and provider.calls == 3
    asyncio.run(scenario())


def test_same_key_different_payload_rejected():
    async def scenario():
        provider = ReceiptProvider()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(provider)) as client:
            await create_receipt(client, "operation-001")
            with pytest.raises(httpx.HTTPStatusError) as error:
                await create_receipt(client, "operation-001", label="different-synthetic")
            assert error.value.response.status_code == 409
            assert provider.effects == 1
    asyncio.run(scenario())


def test_new_key_and_restart_are_not_deduplicated():
    async def scenario():
        provider = ReceiptProvider()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(provider)) as client:
            await create_receipt(client, "operation-001")
            await create_receipt(client, "operation-002")
        assert provider.effects == 2
        restarted = ReceiptProvider()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(restarted)) as client:
            await create_receipt(client, "operation-001")
        assert restarted.effects == 1  # Fake has forgotten the old effect!
    asyncio.run(scenario())


def test_cancel_does_not_retry():
    async def scenario():
        entered = asyncio.Event()
        calls = 0
        async def wait(request):
            nonlocal calls
            calls += 1
            entered.set()
            await asyncio.Event().wait()
        async with managed_client(ORIGIN, transport=httpx.MockTransport(wait)) as client:
            task = asyncio.create_task(create_receipt(client, "operation-001"))
            try:
                await entered.wait()
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
                assert calls == 1
            finally:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())
