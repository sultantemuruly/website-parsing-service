import asyncio
import os
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.models import CrawlResult


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return max(int(raw_value), minimum)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


MAX_CRAWL_PAGES = _env_int("CRAWL_MAX_PAGES", 25, minimum=1)
MAX_DISCOVERY_DEPTH = _env_int("CRAWL_MAX_DEPTH", 2, minimum=1)
PAGE_TIMEOUT_MS = _env_int("CRAWL_PAGE_TIMEOUT_MS", 30_000, minimum=1)
SITE_CRAWL_SEMAPHORE_COUNT = _env_int("CRAWL_SITE_SEMAPHORE_COUNT", 1, minimum=1)
CRAWL_BROWSER_MEMORY_SAVING = _env_bool("CRAWL_BROWSER_MEMORY_SAVING", True)
CRAWL_TEXT_MODE = _env_bool("CRAWL_TEXT_MODE", False)
CRAWL_LIGHT_MODE = _env_bool("CRAWL_LIGHT_MODE", False)
CRAWL_MAX_PAGES_BEFORE_RECYCLE = _env_int(
    "CRAWL_MAX_PAGES_BEFORE_RECYCLE",
    200,
    minimum=0,
)

_crawler: AsyncWebCrawler | None = None
_crawler_lock = asyncio.Lock()

_BROWSER_CLOSED_MARKERS = (
    "target page, context or browser has been closed",
    "browser has been closed",
    "context has been closed",
    "page has been closed",
    "target closed",
)


def browser_config() -> BrowserConfig:
    return BrowserConfig(
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
        memory_saving_mode=CRAWL_BROWSER_MEMORY_SAVING,
        max_pages_before_recycle=CRAWL_MAX_PAGES_BEFORE_RECYCLE,
        text_mode=CRAWL_TEXT_MODE,
        light_mode=CRAWL_LIGHT_MODE,
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


async def _new_crawler() -> AsyncWebCrawler:
    crawler = AsyncWebCrawler(config=browser_config(), thread_safe=True)
    await crawler.start()
    return crawler


async def start_crawler() -> AsyncWebCrawler:
    global _crawler
    async with _crawler_lock:
        if _crawler is None:
            _crawler = await _new_crawler()
        return _crawler


async def close_crawler() -> None:
    global _crawler
    async with _crawler_lock:
        crawler = _crawler
        _crawler = None
        if crawler is None:
            return
        with suppress(Exception):
            await crawler.close()


async def replace_crawler(dead_crawler: AsyncWebCrawler | None = None) -> AsyncWebCrawler:
    global _crawler
    async with _crawler_lock:
        if dead_crawler is not None and _crawler is not dead_crawler and _crawler is not None:
            return _crawler

        crawler_to_close = _crawler
        _crawler = None
        if crawler_to_close is not None:
            with suppress(Exception):
                await crawler_to_close.close()

        _crawler = await _new_crawler()
        return _crawler


async def _require_crawler() -> AsyncWebCrawler:
    if _crawler is None:
        return await start_crawler()
    return _crawler


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
    operation,
) -> CrawlResult | list[CrawlResult]:
    for attempt in range(2):
        crawler = await _require_crawler()
        try:
            result = await operation(crawler)
        except Exception as exc:
            if _browser_closed_message(exc) and attempt == 0:
                await replace_crawler(crawler)
                continue
            if _browser_closed_message(exc):
                raise ValueError(str(exc)) from exc
            raise

        if _all_results_browser_closed(result) and attempt == 0:
            await replace_crawler(crawler)
            continue

        if _contains_browser_closed_result(result):
            await replace_crawler(crawler)

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
