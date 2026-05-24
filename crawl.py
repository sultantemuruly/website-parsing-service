import os
from dotenv import load_dotenv
from firecrawl import AsyncFirecrawl

load_dotenv(override=True)

fc_api_key = os.getenv("FC_API_KEY")
if not fc_api_key:
    raise ValueError("FC_API_KEY is not set")

_client = AsyncFirecrawl(api_key=fc_api_key)

MAX_CRAWL_PAGES = 100

_CRAWL_PARAMS = {
    "maxDepth": 2,
    "scrapeOptions": {"formats": ["markdown"]},
}


async def scrape_page(url: str):
    return await _client.scrape(url, formats=["markdown"])


async def crawl_site(url: str, *, limit: int = MAX_CRAWL_PAGES) -> list:
    params = {**_CRAWL_PARAMS, "limit": min(limit, MAX_CRAWL_PAGES)}
    result = await _client.crawl_url(url, params=params)
    return result.data if hasattr(result, "data") else result
