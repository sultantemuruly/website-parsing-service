from typing import Any, Awaitable, Callable

from process.mappers import social_scrape_payload
from social.normalize.models import ScrapeContext
from social.scrape.brightdata_adapter import (
    scrape_facebook_url,
    scrape_instagram_url,
    scrape_linkedin_url,
)


async def scrape_social_url(
    url: str,
    scrape: Callable[[str], Awaitable[ScrapeContext]],
) -> dict[str, Any]:
    return social_scrape_payload(await scrape(url))


async def scrape_linkedin(url: str) -> dict[str, Any]:
    return await scrape_social_url(url, scrape_linkedin_url)


async def scrape_instagram(url: str) -> dict[str, Any]:
    return await scrape_social_url(url, scrape_instagram_url)


async def scrape_facebook(url: str) -> dict[str, Any]:
    return await scrape_social_url(url, scrape_facebook_url)
