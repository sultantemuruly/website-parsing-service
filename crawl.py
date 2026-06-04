import os
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from crawl_cdp_patch import apply_cdp_auth_patch
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.models import CrawlResult

apply_cdp_auth_patch()


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(int(raw_value), minimum)
    except ValueError:
        return default


CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
if not CF_ACCOUNT_ID:
    raise ValueError("CF_ACCOUNT_ID is not set")
if not CF_API_TOKEN:
    raise ValueError("CF_API_TOKEN is not set")

CF_BROWSER_KEEP_ALIVE_MS = _env_int("CF_BROWSER_KEEP_ALIVE_MS", 600_000, minimum=1)
CF_CDP_URL = (
    f"wss://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/"
    f"browser-rendering/devtools/browser?keep_alive={CF_BROWSER_KEEP_ALIVE_MS}"
)

MAX_CRAWL_PAGES = _env_int("CRAWL_MAX_PAGES", 25, minimum=1)
MAX_DISCOVERY_DEPTH = _env_int("CRAWL_MAX_DEPTH", 2, minimum=1)
PAGE_TIMEOUT_MS = _env_int("CRAWL_PAGE_TIMEOUT_MS", 30_000, minimum=1)
SITE_CRAWL_SEMAPHORE_COUNT = _env_int("CRAWL_SITE_SEMAPHORE_COUNT", 1, minimum=1)

_BROWSER_CLOSED_MARKERS = (
    "target page, context or browser has been closed",
    "browser has been closed",
    "context has been closed",
    "page has been closed",
    "target closed",
)

T = TypeVar("T")


def browser_config() -> BrowserConfig:
    return BrowserConfig(
        browser_mode="custom",
        cdp_url=CF_CDP_URL,
        cdp_cleanup_on_close=True,
        cdp_close_delay=1.0,
        cache_cdp_connection=False,
        create_isolated_context=True,
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
        max_pages_before_recycle=0,
    )


def _base_crawler_config() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        page_timeout=PAGE_TIMEOUT_MS,
        excluded_tags=["nav", "footer", "aside"],
    )


def _site_crawl_config(limit: int) -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        page_timeout=PAGE_TIMEOUT_MS,
        excluded_tags=["nav", "footer", "aside"],
        semaphore_count=SITE_CRAWL_SEMAPHORE_COUNT,
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=MAX_DISCOVERY_DEPTH,
            max_pages=limit,
            include_external=False,
        ),
    )


@dataclass
class CrawledPage:
    markdown: str
    metadata: dict[str, Any]


@asynccontextmanager
async def _run_with_crawler():
    crawler = AsyncWebCrawler(config=browser_config(), thread_safe=True)
    await crawler.start()
    try:
        yield crawler
    finally:
        with suppress(Exception):
            await crawler.close()


def _markdown_text(result: CrawlResult) -> str:
    if result.markdown is None:
        return ""
    return str(result.markdown)


def result_to_page(result: CrawlResult) -> CrawledPage:
    raw_meta = result.metadata or {}
    metadata: dict[str, Any] = {"source_url": result.url}
    for key in ("title", "language", "description"):
        if value := raw_meta.get(key):
            metadata[key] = value
    return CrawledPage(markdown=_markdown_text(result), metadata=metadata)


def _browser_closed_message(error: object) -> str | None:
    text = str(error).strip()
    lowered = text.lower()
    for marker in _BROWSER_CLOSED_MARKERS:
        if marker in lowered:
            return text
    return None


def _normalize_results(result: CrawlResult | list[CrawlResult]) -> list[CrawlResult]:
    if isinstance(result, list):
        return result
    return [result]


def _all_results_browser_closed(result: CrawlResult | list[CrawlResult]) -> bool:
    results = _normalize_results(result)
    return bool(results) and all(
        (not item.success) and _browser_closed_message(item.error_message or "")
        for item in results
    )


def _contains_browser_closed_result(result: CrawlResult | list[CrawlResult]) -> bool:
    return any(
        (not item.success) and _browser_closed_message(item.error_message or "")
        for item in _normalize_results(result)
    )


async def _run_with_recovery(
    operation: Callable[[AsyncWebCrawler], Awaitable[CrawlResult | list[CrawlResult]]],
) -> CrawlResult | list[CrawlResult]:
    for attempt in range(2):
        async with _run_with_crawler() as crawler:
            try:
                result = await operation(crawler)
            except Exception as exc:
                if _browser_closed_message(exc) and attempt == 0:
                    continue
                if _browser_closed_message(exc):
                    raise ValueError(str(exc)) from exc
                raise

            if _all_results_browser_closed(result) and attempt == 0:
                continue

            return result

    raise RuntimeError("Crawler recovery failed")


async def scrape_page(url: str) -> CrawledPage:
    result = await _run_with_recovery(
        lambda crawler: crawler.arun(url, config=_base_crawler_config())
    )
    if isinstance(result, list):
        result = result[0]
    if not result.success:
        raise ValueError(result.error_message or "Crawl failed")
    page = result_to_page(result)
    if not page.markdown.strip():
        raise ValueError("No markdown")
    return page


def _result_url(result: CrawlResult, fallback: str) -> str:
    return result.url or fallback


def _classify_site_result(
    result: CrawlResult, seed_url: str
) -> tuple[CrawledPage | None, dict[str, str] | None]:
    page_url = _result_url(result, seed_url)
    if not result.success:
        return None, {"url": page_url, "error": result.error_message or "Crawl failed"}
    if not _markdown_text(result).strip():
        return None, {"url": page_url, "error": "No markdown"}
    return result_to_page(result), None


async def crawl_site_with_outcomes(
    url: str, *, limit: int = MAX_CRAWL_PAGES
) -> tuple[list[CrawledPage], list[dict[str, str]]]:
    """Return successful pages and per-URL failures from a site crawl."""
    capped_limit = min(max(limit, 1), MAX_CRAWL_PAGES)
    results = await _run_with_recovery(
        lambda crawler: crawler.arun(url, config=_site_crawl_config(capped_limit))
    )
    if not isinstance(results, list):
        results = [results]

    pages: list[CrawledPage] = []
    failures: list[dict[str, str]] = []
    for result in results:
        page, failure = _classify_site_result(result, url)
        if page is not None:
            pages.append(page)
        elif failure is not None:
            failures.append(failure)
    return pages, failures


async def crawl_site(url: str, *, limit: int = MAX_CRAWL_PAGES) -> list[CrawledPage]:
    pages, _ = await crawl_site_with_outcomes(url, limit=limit)
    return pages
