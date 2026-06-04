from typing import Any

from crawl.config import MAX_CRAWL_PAGES
from crawl.crawler import (
    CrawledPage,
    crawl_site,
    crawl_site_with_outcomes,
    scrape_page,
)
from process.mappers import crawl_page_payload


async def crawl_single_page(url: str) -> dict[str, Any]:
    return crawl_page_payload(await scrape_page(url))


async def crawl_full_site(url: str) -> list[dict[str, Any]]:
    return [
        crawl_page_payload(page, site_seed_url=url)
        for page in await crawl_site(url)
    ]


async def crawl_site_partial(url: str) -> dict[str, Any]:
    crawled_pages, failures = await crawl_site_with_outcomes(url, limit=MAX_CRAWL_PAGES)
    pages = [crawl_page_payload(page, site_seed_url=url) for page in crawled_pages]
    return {
        "partial": bool(failures),
        "site_seed_url": url,
        "pages": pages,
        "failures": failures,
    }
