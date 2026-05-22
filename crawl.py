import asyncio

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, BrowserConfig, VirtualScrollConfig
from crawl4ai.async_configs import ProxyConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(threshold=0.2, threshold_type="adaptive")
)

basic_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator
)

deep_config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=2, 
        include_external=False
    ),
    scraping_strategy=LXMLWebScrapingStrategy(),
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator,
    verbose=True
)

deep_streaming_config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=2, 
        include_external=False
    ),
    scraping_strategy=LXMLWebScrapingStrategy(),
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator,
    verbose=True,
    stream=True
)

async def crawl_page(url: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=basic_config)
    return result

async def crawl_page_deep(url: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=deep_config)
    return result

async def crawl_page_deep_streaming(url: str):
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(url, config=deep_streaming_config):
            yield result

# Mock proxies — replace with real ProxyConfig values in production
MOCK_DATACENTER_PROXY = ProxyConfig(
    server="http://datacenter-proxy.example.com:8080",
    username="user",
    password="pass",
)
MOCK_RESIDENTIAL_PROXY = ProxyConfig(
    server="http://residential-proxy.example.com:9090",
    username="user",
    password="pass",
)


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


def _print_escalation_stats(result) -> None:
    stats = result.crawl_stats or {}
    print(f"Resolved by: {stats.get('resolved_by')}")
    print(f"Attempts: {stats.get('attempts')}, retries: {stats.get('retries')}")
    if stats.get("fallback_fetch_used"):
        print("Fallback fetch was used")

    for i, attempt in enumerate(stats.get("proxies_used") or [], start=1):
        proxy = attempt.get("proxy") or "direct"
        blocked = attempt.get("blocked")
        reason = attempt.get("reason") or ""
        status = "blocked" if blocked else "ok"
        print(f"  Attempt {i}: {proxy} — {status}" + (f" ({reason})" if reason else ""))


async def scrape_social_profile(url: str):
    browser_cfg = BrowserConfig(headless=True, enable_stealth=True)
    run_cfg = CrawlerRunConfig(
        magic=True,
        wait_until="load",
        wait_for="css:main",
        max_retries=2,
        proxy_config=[MOCK_DATACENTER_PROXY, MOCK_RESIDENTIAL_PROXY],
        fallback_fetch_function=mock_external_fetch,
        virtual_scroll_config=VirtualScrollConfig(
            container_selector="main",
            scroll_count=30,
            scroll_by="page_height",
            wait_after_scroll=1.0,
        ),
        cache_mode=CacheMode.BYPASS,
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        return await crawler.arun(url=url, config=run_cfg)

if __name__ == "__main__":
    result = asyncio.run(scrape_social_profile("https://x.com/AnthropicAI"))
    _print_escalation_stats(result)

    if result.success:
        md = result.markdown
        text = md.raw_markdown if hasattr(md, "raw_markdown") and md.raw_markdown else str(md or "")
        print(f"\nGot {len(text)} chars of markdown:\n")
        print(text or "(empty)")
    else:
        print(f"\nAll attempts failed: {result.error_message}")
