import asyncio
import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    UndetectedAdapter,
    VirtualScrollConfig,
    LLMConfig,
    LLMExtractionStrategy,
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(threshold=0.2, threshold_type="adaptive")
)

basic_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator,
)

deep_config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=2, include_external=False),
    scraping_strategy=LXMLWebScrapingStrategy(),
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator,
    verbose=True,
)

deep_streaming_config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=2, include_external=False),
    scraping_strategy=LXMLWebScrapingStrategy(),
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator,
    verbose=True,
    stream=True,
)

async def crawl_page(url: str):
    async with AsyncWebCrawler() as crawler:
        return await crawler.arun(url, config=basic_config)


async def crawl_page_deep(url: str):
    async with AsyncWebCrawler() as crawler:
        return await crawler.arun(url, config=deep_config)


async def crawl_page_deep_streaming(url: str):
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(url, config=deep_streaming_config):
            yield result


async def mock_external_fetch(url: str) -> str:
    """Mock last-resort fetch (stand-in for an external scraping API)."""
    print(f"[mock_external_fetch] fetching HTML for {url}", flush=True)
    return f"""<!DOCTYPE html>
<html>
  <body>
    <main>
      <h1>Mock external fetch</h1>
      <p>Source URL: {url}</p>
      <article>
        <p>This HTML was returned by mock_external_fetch after all browser
        attempts were blocked or failed.</p>
      </article>
    </main>
  </body>
</html>"""


anti_bot_browser_config = BrowserConfig(headless=True, enable_stealth=True)

anti_bot_run_config = CrawlerRunConfig(
    magic=True,
    wait_until="load",
    wait_for="css:main",
    max_retries=2,
    fallback_fetch_function=mock_external_fetch,
    virtual_scroll_config=VirtualScrollConfig(
        container_selector="main",
        scroll_count=100,
        scroll_by="page_height",
        wait_after_scroll=1.0,
    ),
    cache_mode=CacheMode.BYPASS,
)


def _undetected_crawler() -> AsyncWebCrawler:
    strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=anti_bot_browser_config,
        browser_adapter=UndetectedAdapter(),
    )
    return AsyncWebCrawler(crawler_strategy=strategy, config=anti_bot_browser_config)


def print_crawl_stats(result) -> None:
    stats = result.crawl_stats or {}
    print(f"Resolved by: {stats.get('resolved_by')}")
    print(f"Attempts: {stats.get('attempts')}, retries: {stats.get('retries')}")
    if stats.get("fallback_fetch_used"):
        print("Fallback fetch was used")
    for i, attempt in enumerate(stats.get("proxies_used") or [], start=1):
        blocked = attempt.get("blocked")
        reason = attempt.get("reason") or ""
        status = "blocked" if blocked else "ok"
        print(f"  Attempt {i}: {status}" + (f" ({reason})" if reason else ""))


async def scrape_social_profile(url: str):
    async with _undetected_crawler() as crawler:
        return await crawler.arun(url=url, config=anti_bot_run_config)


if __name__ == "__main__":
    result = asyncio.run(scrape_social_profile("https://www.instagram.com/nuedukz/"))
    print_crawl_stats(result)

    if result.success:
        md = result.markdown
        text = md.raw_markdown if hasattr(md, "raw_markdown") and md.raw_markdown else str(md or "")
        print(f"\nGot {len(text)} chars of markdown:\n")
        print(text or "(empty)")
        print(len(md.raw_markdown))
    else:
        print(f"\nAll attempts failed: {result.error_message}")
