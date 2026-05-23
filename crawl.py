import os
from dotenv import load_dotenv
from firecrawl import AsyncFirecrawl

load_dotenv(override=True)

fc_api_key = os.getenv("FC_API_KEY")
if not fc_api_key:
    raise ValueError("FC_API_KEY is not set")

_client = AsyncFirecrawl(api_key=fc_api_key)

_CRAWL_PARAMS = {
    "maxDepth": 2,
    "limit": 100,
    "scrapeOptions": {"formats": ["markdown"]},
}


async def scrape_page(url: str):
    return await _client.scrape(url, formats=["markdown"])


async def crawl_site(url: str) -> list:
    result = await _client.crawl_url(url, params=_CRAWL_PARAMS)
    return result.data if hasattr(result, "data") else result
