from collections.abc import Iterator
from dataclasses import dataclass
from tempfile import TemporaryFile
from typing import TextIO

from fastapi import Depends, HTTPException, Query, Request

from task_api.config import Settings
from task_api.store import MemoryStore


@dataclass
class RequestTrace:
    label: str
    stream: TextIO

    def mark(self, action: str) -> None:
        self.stream.write(action + "\n")
        print(f"TRACE use {self.label} {action}", flush=True)


def request_trace(request: Request) -> Iterator[RequestTrace]:
    # This is a real, temporary file handle, NOT a database session or audit log.
    stream = TemporaryFile(mode="w+t", encoding="utf-8")
    label = f"{request.method} {request.url.path}"
    try:
        print(f"TRACE acquire {label}", flush=True)
        yield RequestTrace(label, stream)
    finally:
        stream.close()
        print(f"TRACE release {label} closed={stream.closed}", flush=True)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_store(
    request: Request,
    trace: RequestTrace = Depends(request_trace, scope="function"),
) -> MemoryStore:
    trace.mark("get_store")
    return request.app.state.store


@dataclass(frozen=True)
class Page:
    limit: int
    offset: int


def get_page(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
) -> Page:
    if limit > settings.max_page_size:
        raise HTTPException(status_code=422, detail="limit exceeds TASKS_MAX_PAGE_SIZE")
    return Page(limit, offset)
