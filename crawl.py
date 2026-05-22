import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
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
