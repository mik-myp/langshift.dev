"""A lost reply is not proof that an external write did not happen."""
import asyncio
import json

import httpx


class ReceiptProvider:
    """Mock-only idempotency contract; a restart discards this ledger."""
    def __init__(self):
        self.ledger = {}
        self.effects = 0
        self.calls = 0

    async def __call__(self, request):
        self.calls += 1
        key = request.headers.get("Idempotency-Key")
        if not key:
            return httpx.Response(400, json={"error": "key required"})
        payload = json.loads(request.content)
        if key in self.ledger:
            previous, receipt = self.ledger[key]
            if payload != previous:
                return httpx.Response(409, json={"error": "key reused for different data"})
            return httpx.Response(200, json=receipt)
        self.effects += 1
        receipt = {"receipt_id": self.effects}
        # No await between effect and ledger write in this ONE-process fake.
        self.ledger[key] = (payload, receipt)
        raise httpx.ReadTimeout("synthetic: effect committed, reply lost", request=request)


async def create_receipt(client, key, *, label="synthetic"):
    if not key or len(key) > 80:
        raise ValueError("a stable operation key is required")
    async with asyncio.timeout(1):
        for attempt in range(2):
            try:
                response = await client.post("/receipts", headers={"Idempotency-Key": key},
                                             json={"label": label})
                response.raise_for_status()
                data = response.json()
                if set(data) != {"receipt_id"} or type(data["receipt_id"]) is not int or data["receipt_id"] < 1:
                    raise ValueError("invalid receipt")
                return data
            except httpx.ReadTimeout:
                if attempt == 1:
                    raise
                await asyncio.sleep(0)  # No real retry delay needed for this mock.
