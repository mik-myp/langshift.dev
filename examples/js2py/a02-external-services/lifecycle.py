"""Only synthetic traffic to an explicitly loopback-only service is allowed."""
import re
from contextlib import asynccontextmanager

import anyio
import httpx


DEFAULT_UPSTREAM = "http://127.0.0.1:8766"


def validate_origin(origin):
    match = re.fullmatch(r"http://127\.0\.0\.1:([0-9]{1,5})", origin)
    if not match or not 1 <= int(match[1]) <= 65535:
        # Never include a supplied URL: it might contain credentials or query data.
        raise ValueError("upstream must be http://127.0.0.1:<port>; value omitted")
    return origin


@asynccontextmanager
async def managed_client(origin, *, transport=None):
    origin = validate_origin(origin)
    client = httpx.AsyncClient(
        base_url=origin,
        transport=transport,
        timeout=httpx.Timeout(connect=0.2, read=0.2, write=0.2, pool=0.1),
        limits=httpx.Limits(max_connections=2, max_keepalive_connections=2),
        trust_env=False,
        follow_redirects=False,
        headers={"Accept": "application/json", "Accept-Encoding": "identity"},
    )
    try:
        yield client
    finally:
        # AnyIO cancellation scopes cancel at each checkpoint. Shield just cleanup,
        # not the request. A broken close is bounded, surfaced, and not called success.
        with anyio.move_on_after(2, shield=True) as cleanup:
            await client.aclose()
        if cleanup.cancel_called:
            raise RuntimeError("outbound client cleanup exceeded budget")
