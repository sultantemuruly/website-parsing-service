import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from brightdata import BrightDataClient
from brightdata.models import ScrapeResult

from social_normalize import ScrapeContext

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


async def _scrape_linkedin(client: BrightDataClient, url: str) -> tuple[str, ScrapeResult]:
    path = _path(url)
    lower = url.lower()
    scraper = client.scrape.linkedin

    if "/jobs/view" in path or ("/jobs/" in path and "search" not in path):
        return "jobs", await scraper.jobs(url=url)
    if "/company/" in path:
        return "companies", await scraper.companies(url=url)
    if "/in/" in path or "/pub/" in path:
        return "profiles", await scraper.profiles(url=url)
    if "/feed/update" in path or "/posts/" in path or "urn:li:activity" in lower:
        return "posts", await scraper.posts(url=url)

    raise ValueError(f"Unsupported LinkedIn URL: {url}")


async def _scrape_instagram(client: BrightDataClient, url: str) -> tuple[str, ScrapeResult]:
    path = _path(url)
    scraper = client.scrape.instagram

    if "/p/" in path:
        return "posts", await scraper.posts(url=url)
    if "/reel/" in path or "/reels/" in path:
        return "reels", await scraper.reels(url=url)

    segments = [s for s in path.split("/") if s]
    if len(segments) == 1 and segments[0] not in {
        "p",
        "reel",
        "reels",
        "stories",
        "explore",
        "tv",
    }:
        return "profiles", await scraper.profiles(url=url)

    raise ValueError(f"Unsupported Instagram URL: {url}")


async def _scrape_facebook(client: BrightDataClient, url: str) -> tuple[str, ScrapeResult]:
    path = _path(url)
    scraper = client.scrape.facebook

    if "/groups/" in path:
        return "posts_by_group", await scraper.posts_by_group(url=url)
    if "/reel" in path:
        return "reels", await scraper.reels(url=url)
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
        return "posts_by_url", await scraper.posts_by_url(url=url)

    return "posts_by_profile", await scraper.posts_by_profile(url=url)


async def _scrape_url(url: str, platform: str, scrape_fn) -> ScrapeContext:
    async with BrightDataClient(token=token) as client:
        scraper_type, result = await scrape_fn(client, url)
        return ScrapeContext(
            platform=platform,
            scraper_type=scraper_type,
            request_url=url,
            raw=_result_data(result),
        )


async def scrape_linkedin_url(url: str) -> ScrapeContext:
    return await _scrape_url(url, "linkedin", _scrape_linkedin)


async def scrape_instagram_url(url: str) -> ScrapeContext:
    return await _scrape_url(url, "instagram", _scrape_instagram)


async def scrape_facebook_url(url: str) -> ScrapeContext:
    return await _scrape_url(url, "facebook", _scrape_facebook)
