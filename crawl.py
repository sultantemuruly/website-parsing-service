from dataclasses import dataclass
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.models import CrawlResult

MAX_CRAWL_PAGES = 100
MAX_DISCOVERY_DEPTH = 2

_crawler: AsyncWebCrawler | None = None


def browser_config() -> BrowserConfig:
    return BrowserConfig(
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
    )


def _base_crawler_config() -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        page_timeout=30_000,
        excluded_tags=["nav", "footer", "aside"],
    )


def _site_crawl_config(limit: int) -> CrawlerRunConfig:
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        page_timeout=30_000,
        excluded_tags=["nav", "footer", "aside"],
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


def init_crawler(crawler: AsyncWebCrawler) -> None:
    global _crawler
    _crawler = crawler


def clear_crawler() -> None:
    global _crawler
    _crawler = None


def _require_crawler() -> AsyncWebCrawler:
    if _crawler is None:
        raise RuntimeError("Crawler not initialized")
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


async def scrape_page(url: str) -> CrawledPage:
    result = await _require_crawler().arun(url, config=_base_crawler_config())
    if isinstance(result, list):
        result = result[0]
    if not result.success:
        raise ValueError(result.error_message or "Crawl failed")
    page = result_to_page(result)
    if not page.markdown.strip():
        raise ValueError("No markdown")
    return page


async def crawl_site(url: str, *, limit: int = MAX_CRAWL_PAGES) -> list[CrawledPage]:
    capped_limit = min(max(limit, 1), MAX_CRAWL_PAGES)
    results = await _require_crawler().arun(url, config=_site_crawl_config(capped_limit))
    if not isinstance(results, list):
        results = [results]

    pages: list[CrawledPage] = []
    for result in results:
        if result.success and _markdown_text(result).strip():
            pages.append(result_to_page(result))
    return pages
