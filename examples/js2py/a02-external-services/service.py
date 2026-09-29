import asyncio
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError


class Hint(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    priority: Literal["low", "normal", "high"]


class InvalidHint(Exception):
    """Rejected external data; never put its body into a public response."""


class TransientFailure(Exception):
    """A narrow set of failures for which this read-only GET may be retried."""


def unavailable():
    return {"state": "unavailable", "priority": None}


class HintService:
    def __init__(self, client, *, concurrency=2, deadline=0.7, backoff=0.02):
        if not 1 <= concurrency <= 8 or not 0 < deadline <= 30 or not 0 <= backoff <= 1:
            raise ValueError("invalid external-service budget")
        self.client = client
        self.slots = asyncio.Semaphore(concurrency)
        self.deadline = deadline
        self.backoff = backoff
        self.active = 0
        self.peak = 0
        self.attempts = 0  # Lab counters, not a production metrics system.

    async def _once(self):
        try:
            # Fixed URL, no incoming task text, user ID, or user-supplied URL.
            async with self.client.stream("GET", "/hint") as response:
                if response.status_code in {502, 503, 504}:
                    raise TransientFailure("retryable upstream status")
                if response.status_code != 200:
                    raise InvalidHint("unexpected upstream status")
                if response.headers.get("content-type", "").split(";")[0].strip() != "application/json":
                    raise InvalidHint("unexpected content type")
                if response.headers.get("content-encoding", "identity") != "identity":
                    raise InvalidHint("encoded bodies are not accepted by this lab")
                body = bytearray()
                async for chunk in response.aiter_raw():
                    if len(body) + len(chunk) > 1024:
                        raise InvalidHint("upstream body too large")
                    body.extend(chunk)
                try:
                    hint = Hint.model_validate_json(bytes(body))
                except ValidationError:
                    raise InvalidHint("invalid upstream schema") from None
                return {"state": "available", "priority": hint.priority}
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
            raise TransientFailure("retryable upstream transport failure") from None

    async def hint(self):
        try:
            # Includes waiting for our semaphore, pool, both attempts and backoff.
            async with asyncio.timeout(self.deadline):
                async with self.slots:
                    self.active += 1
                    self.peak = max(self.peak, self.active)
                    try:
                        for attempt in range(2):
                            self.attempts += 1
                            try:
                                return await self._once()
                            except TransientFailure:
                                if attempt == 1:
                                    return unavailable()
                                await asyncio.sleep(self.backoff)
                    finally:
                        self.active -= 1
        except (TimeoutError, httpx.RequestError, InvalidHint):
            return unavailable()
        # CancelledError is deliberately not swallowed or converted to a fallback.
