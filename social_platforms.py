import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from brightdata import BrightDataClient
from brightdata.models import ScrapeResult

load_dotenv(override=True)

token = os.getenv("BRIGHTDATA_API_TOKEN")
if not token:
    raise ValueError("BRIGHTDATA_API_TOKEN is not set")


def _path(url: str) -> str:
    return urlparse(url).path.lower().rstrip("/")


def _result_data(result: ScrapeResult):
    if not result.success:
        raise RuntimeError(result.error or "Bright Data scrape failed")
    return result.data


async def _scrape_linkedin(client: BrightDataClient, url: str) -> ScrapeResult:
    path = _path(url)
    lower = url.lower()
    scraper = client.scrape.linkedin

    if "/jobs/view" in path or ("/jobs/" in path and "search" not in path):
        return await scraper.jobs(url=url)
    if "/company/" in path:
        return await scraper.companies(url=url)
    if "/in/" in path or "/pub/" in path:
        return await scraper.profiles(url=url)
    if "/feed/update" in path or "/posts/" in path or "urn:li:activity" in lower:
        return await scraper.posts(url=url)

    raise ValueError(f"Unsupported LinkedIn URL: {url}")


async def _scrape_instagram(client: BrightDataClient, url: str) -> ScrapeResult:
    path = _path(url)
    scraper = client.scrape.instagram

    if "/p/" in path:
        return await scraper.posts(url=url)
    if "/reel/" in path or "/reels/" in path:
        return await scraper.reels(url=url)

    segments = [s for s in path.split("/") if s]
    if len(segments) == 1 and segments[0] not in {
        "p",
        "reel",
        "reels",
        "stories",
        "explore",
        "tv",
    }:
        return await scraper.profiles(url=url)

    raise ValueError(f"Unsupported Instagram URL: {url}")


async def _scrape_facebook(client: BrightDataClient, url: str) -> ScrapeResult:
    path = _path(url)
    scraper = client.scrape.facebook

    if "/groups/" in path:
        return await scraper.posts_by_group(url=url)
    if "/reel" in path:
        return await scraper.reels(url=url)
    if any(
        marker in path
        for marker in (
            "/posts/",
            "/permalink/",
            "/story.php",
            "/photo.php",
            "/videos/",
            "/watch/",
        )
    ):
        return await scraper.posts_by_url(url=url)

    return await scraper.posts_by_profile(url=url)


async def scrape_linkedin_url(url: str):
    async with BrightDataClient(token=token) as client:
        return _result_data(await _scrape_linkedin(client, url))


async def scrape_instagram_url(url: str):
    async with BrightDataClient(token=token) as client:
        return _result_data(await _scrape_instagram(client, url))


async def scrape_facebook_url(url: str):
    async with BrightDataClient(token=token) as client:
        return _result_data(await _scrape_facebook(client, url))
