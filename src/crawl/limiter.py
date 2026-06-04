import asyncio
from contextlib import asynccontextmanager

from fastapi import HTTPException


class CrawlRequestLimiter:
    def __init__(self, max_in_flight: int, queue_timeout_ms: int):
        self._semaphore = asyncio.Semaphore(max_in_flight)
        self._queue_timeout_seconds = queue_timeout_ms / 1000

    @asynccontextmanager
    async def slot(self):
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self._queue_timeout_seconds,
            )
        except TimeoutError as exc:
            raise HTTPException(
                status_code=429,
                detail="Crawler is busy, retry later",
            ) from exc

        try:
            yield
        finally:
            self._semaphore.release()
