import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(threshold=0.2, threshold_type="adaptive")
)

config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator
)

async def crawl_page(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=config)
    return result.markdown.fit_markdown
