from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from fastapi import FastAPI, HTTPException, Request

from config import CRAWL_MAX_IN_FLIGHT, CRAWL_QUEUE_TIMEOUT_MS
from crawl.limiter import CrawlRequestLimiter

T = TypeVar("T")


def get_crawl_limiter(app: FastAPI) -> CrawlRequestLimiter:
    limiter = getattr(app.state, "crawl_limiter", None)
    if limiter is None:
        limiter = CrawlRequestLimiter(
            max_in_flight=CRAWL_MAX_IN_FLIGHT,
            queue_timeout_ms=CRAWL_QUEUE_TIMEOUT_MS,
        )
        app.state.crawl_limiter = limiter
    return limiter


async def run_limited_crawl(request: Request, operation: Callable[[], Awaitable[T]]) -> T:
    async with get_crawl_limiter(request.app).slot():
        return await operation()


async def run_crawl_endpoint(request: Request, operation: Callable[[], Awaitable[Any]]) -> Any:
    try:
        return await run_limited_crawl(request, operation)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
