import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from crawl import (
    MAX_CRAWL_PAGES,
    close_crawler,
    crawl_site,
    crawl_site_with_outcomes,
    scrape_page,
    start_crawler,
)
from process import (
    ProcessPageRequest,
    ProcessSocialRequest,
    crawl_page_payload,
    crawled_page_from_request,
    process_page_data,
    process_social_data,
    scrape_context_from_request,
    social_scrape_payload,
)
from social_platforms import (
    scrape_facebook_url,
    scrape_instagram_url,
    scrape_linkedin_url,
)

from summary_agent import (
    BusinessProfileRequest,
    SummaryModel,
    summarize_business_profile,
)

def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(int(raw_value), minimum)
    except ValueError:
        return default


CRAWL_MAX_IN_FLIGHT = _env_int("CRAWL_MAX_IN_FLIGHT", 1, minimum=1)
CRAWL_QUEUE_TIMEOUT_MS = _env_int("CRAWL_QUEUE_TIMEOUT_MS", 1_000, minimum=1)


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


def _get_crawl_limiter(app: FastAPI) -> CrawlRequestLimiter:
    limiter = getattr(app.state, "crawl_limiter", None)
    if limiter is None:
        limiter = CrawlRequestLimiter(
            max_in_flight=CRAWL_MAX_IN_FLIGHT,
            queue_timeout_ms=CRAWL_QUEUE_TIMEOUT_MS,
        )
        app.state.crawl_limiter = limiter
    return limiter


async def _run_limited_crawl(request: Request, operation):
    async with _get_crawl_limiter(request.app).slot():
        return await operation()


async def _run_crawl_endpoint(request: Request, operation):
    try:
        return await _run_limited_crawl(request, operation)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _get_crawl_limiter(_app)
    await start_crawler()
    try:
        yield
    finally:
        await close_crawler()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"status": "ok"}


async def _crawl_payload(url: str) -> dict[str, Any]:
    return crawl_page_payload(await scrape_page(url))


async def _crawl_site_payload(url: str) -> list[dict[str, Any]]:
    return [
        crawl_page_payload(page, site_seed_url=url)
        for page in await crawl_site(url)
    ]


async def _crawl_site_partial_payload(url: str) -> dict[str, Any]:
    crawled_pages, failures = await crawl_site_with_outcomes(url, limit=MAX_CRAWL_PAGES)
    pages = [crawl_page_payload(page, site_seed_url=url) for page in crawled_pages]
    return {
        "partial": bool(failures),
        "site_seed_url": url,
        "pages": pages,
        "failures": failures,
    }


@app.post("/crawl")
async def crawl(request: Request, url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    return await _run_crawl_endpoint(request, lambda: _crawl_payload(url))


@app.post("/crawl/site")
async def crawl_site_endpoint(request: Request, url: str) -> list[dict[str, Any]]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    return await _run_crawl_endpoint(request, lambda: _crawl_site_payload(url))


@app.post("/crawl/site/partial")
async def crawl_site_partial(request: Request, url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    return await _run_crawl_endpoint(request, lambda: _crawl_site_partial_payload(url))


@app.post("/process/page")
async def process_page(body: ProcessPageRequest) -> dict[str, Any]:
    if not body.markdown.strip():
        raise HTTPException(status_code=400, detail="markdown is required")
    try:
        return process_page_data(
            crawled_page_from_request(body),
            site_seed_url=body.site_seed_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/social")
async def process_social(body: ProcessSocialRequest) -> dict[str, Any]:
    try:
        return process_social_data(scrape_context_from_request(body))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _social_endpoint(url: str, scrape) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return social_scrape_payload(await scrape(url))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin")
async def linkedin(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_linkedin_url)


@app.post("/instagram")
async def instagram(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_instagram_url)


@app.post("/facebook")
async def facebook(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_facebook_url)

@app.post("/business_profile")
async def business_profile(body: BusinessProfileRequest) -> SummaryModel:
    if not body.context.strip():
        raise HTTPException(status_code=400, detail="context is required")
    try:
        return await summarize_business_profile(body.context)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
