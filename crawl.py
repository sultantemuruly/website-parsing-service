import os
from dotenv import load_dotenv
from firecrawl import AsyncFirecrawl

load_dotenv(override=True)

fc_api_key = os.getenv("FC_API_KEY")
if not fc_api_key:
    raise ValueError("FC_API_KEY is not set")

_client = AsyncFirecrawl(api_key=fc_api_key)

MAX_CRAWL_PAGES = 100


async def scrape_page(url: str):
    return await _client.scrape(url, formats=["markdown"])


async def crawl_site(url: str, *, limit: int = MAX_CRAWL_PAGES) -> list:
    capped_limit = min(max(limit, 1), MAX_CRAWL_PAGES)

    result = await _client.crawl(
        url=url,
        limit=capped_limit,
        max_discovery_depth=2,
        scrape_options={"formats": ["markdown"]},
    )

    return result.data
