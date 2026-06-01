from contextlib import asynccontextmanager
import json
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from crawl import CrawledPage, crawl_site_with_outcomes, scrape_page
from process import (
    ProcessPageRequest,
    crawl_page_payload,
    social_scrape_payload,
)
from social_normalize import ScrapeContext

os.environ.setdefault("BRIGHTDATA_API_TOKEN", "test-token")
from fastapi.testclient import TestClient

from main import app

FIXTURES = Path(__file__).parent / "fixtures"
client = TestClient(app)


class CrawlPagePayloadTest(unittest.TestCase):
    def test_maps_crawled_page_fields(self):
        page = CrawledPage(
            markdown="# Hello\n\nWorld",
            metadata={
                "source_url": "https://example.com/page",
                "title": "Example Page",
                "language": "en",
                "description": "A test page",
            },
        )
        payload = crawl_page_payload(page)

        self.assertEqual(payload["markdown"], "# Hello\n\nWorld")
        self.assertEqual(payload["url"], "https://example.com/page")
        self.assertEqual(payload["title"], "Example Page")
        self.assertEqual(payload["language"], "en")
        self.assertEqual(payload["description"], "A test page")
        self.assertNotIn("site_seed_url", payload)

    def test_includes_site_seed_url_when_provided(self):
        page = CrawledPage(
            markdown="# Hello",
            metadata={"source_url": "https://example.com/page"},
        )
        payload = crawl_page_payload(page, site_seed_url="https://example.com")

        self.assertEqual(payload["site_seed_url"], "https://example.com")

    def test_omits_absent_optional_fields(self):
        page = CrawledPage(
            markdown="# Hello",
            metadata={"source_url": "https://example.com/page"},
        )
        payload = crawl_page_payload(page)

        self.assertEqual(set(payload.keys()), {"markdown", "url"})
        ProcessPageRequest.model_validate(payload)


class SocialScrapePayloadTest(unittest.TestCase):
    def test_matches_scrape_context(self):
        ctx = ScrapeContext(
            platform="linkedin",
            scraper_type="profiles",
            request_url="https://www.linkedin.com/in/jane-doe",
            raw={"name": "Jane Doe"},
        )
        payload = social_scrape_payload(ctx)

        self.assertEqual(payload["platform"], "linkedin")
        self.assertEqual(payload["scraper_type"], "profiles")
        self.assertEqual(payload["request_url"], "https://www.linkedin.com/in/jane-doe")
        self.assertEqual(payload["raw"], {"name": "Jane Doe"})
        self.assertNotIn("chunks", payload)


class RoundTripTest(unittest.TestCase):
    def test_crawl_payload_round_trips_through_process_page(self):
        page = CrawledPage(
            markdown="# Hello\n\nWorld " * 50,
            metadata={
                "source_url": "https://example.com/page",
                "title": "Hello",
                "language": "en",
            },
        )
        payload = crawl_page_payload(page, site_seed_url="https://example.com")

        response = client.post("/process/page", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["chunks"])
        self.assertEqual(data["url"], "https://example.com/page")
        self.assertEqual(data["metadata"]["title"], "Hello")
        self.assertEqual(
            data["chunks"][0]["metadata"]["site_seed_url"],
            "https://example.com",
        )

    def test_social_payload_round_trips_through_process_social(self):
        raw = json.loads((FIXTURES / "linkedin_profile.json").read_text())
        ctx = ScrapeContext(
            platform="linkedin",
            scraper_type="profiles",
            request_url="https://www.linkedin.com/in/jane-doe",
            raw=raw,
        )
        payload = social_scrape_payload(ctx)

        response = client.post("/process/social", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["chunks"])
        self.assertEqual(data["scraper_type"], "profiles")
        self.assertEqual(data["record_type"], "profile")


class ScrapeEndpointTest(unittest.TestCase):
    def test_crawl_returns_payload_without_chunks(self):
        page = CrawledPage(
            markdown="# Hello\n\nWorld",
            metadata={
                "source_url": "https://example.com/page",
                "title": "Hello",
            },
        )
        with patch("main.scrape_page", new=AsyncMock(return_value=page)):
            response = client.post("/crawl?url=https://example.com/page")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["markdown"], "# Hello\n\nWorld")
        self.assertEqual(data["url"], "https://example.com/page")
        self.assertEqual(data["title"], "Hello")
        self.assertNotIn("chunks", data)
        self.assertNotIn("metadata", data)

    def test_linkedin_returns_payload_without_chunks(self):
        ctx = ScrapeContext(
            platform="linkedin",
            scraper_type="profiles",
            request_url="https://www.linkedin.com/in/jane-doe",
            raw={"name": "Jane Doe"},
        )
        with patch("main.scrape_linkedin_url", new=AsyncMock(return_value=ctx)):
            response = client.post("/linkedin?url=https://www.linkedin.com/in/jane-doe")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["platform"], "linkedin")
        self.assertEqual(data["scraper_type"], "profiles")
        self.assertEqual(data["request_url"], "https://www.linkedin.com/in/jane-doe")
        self.assertEqual(data["raw"], {"name": "Jane Doe"})
        self.assertNotIn("chunks", data)
        self.assertNotIn("record_type", data)


class PartialCrawlEndpointTest(unittest.TestCase):
    def test_returns_pages_and_failures(self):
        page = CrawledPage(
            markdown="# OK",
            metadata={"source_url": "https://example.com/ok"},
        )
        with patch(
            "main.crawl_site_with_outcomes",
            new=AsyncMock(
                return_value=(
                    [page],
                    [{"url": "https://example.com/bad", "error": "No markdown"}],
                ),
            ),
        ):
            response = client.post("/crawl/site/partial?url=https://example.com")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["partial"])
        self.assertEqual(data["site_seed_url"], "https://example.com")
        self.assertEqual(len(data["pages"]), 1)
        self.assertEqual(data["pages"][0]["url"], "https://example.com/ok")
        self.assertEqual(data["pages"][0]["site_seed_url"], "https://example.com")
        self.assertEqual(len(data["failures"]), 1)
        self.assertEqual(data["failures"][0]["error"], "No markdown")


class EndpointLimiterTest(unittest.TestCase):
    def test_returns_429_when_crawl_queue_is_full(self):
        class BusyLimiter:
            @asynccontextmanager
            async def slot(self):
                raise RuntimeError("Limiter should be patched by endpoint wrapper")
                yield

        @asynccontextmanager
        async def saturated_slot():
            from fastapi import HTTPException

            raise HTTPException(status_code=429, detail="Crawler is busy, retry later")
            yield

        limiter = BusyLimiter()
        limiter.slot = saturated_slot

        had_existing = hasattr(client.app.state, "crawl_limiter")
        original = getattr(client.app.state, "crawl_limiter", None)
        client.app.state.crawl_limiter = limiter
        try:
            with patch("main.scrape_page", new=AsyncMock()) as scrape_mock:
                response = client.post("/crawl?url=https://example.com/page")
        finally:
            if had_existing:
                client.app.state.crawl_limiter = original
            else:
                delattr(client.app.state, "crawl_limiter")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], "Crawler is busy, retry later")
        scrape_mock.assert_not_called()


class CrawlerRecoveryTest(unittest.IsolatedAsyncioTestCase):
    def _crawl_result(
        self,
        *,
        success: bool,
        url: str,
        markdown: str = "",
        error_message: str | None = None,
    ):
        return SimpleNamespace(
            success=success,
            url=url,
            markdown=markdown,
            metadata={"title": "Example"} if success else {},
            error_message=error_message,
        )

    async def test_scrape_page_retries_once_after_browser_closed_exception(self):
        closed_error = RuntimeError("Target page, context or browser has been closed")
        crawler_one = SimpleNamespace(arun=AsyncMock(side_effect=closed_error))
        crawler_two = SimpleNamespace(
            arun=AsyncMock(
                return_value=self._crawl_result(
                    success=True,
                    url="https://example.com/page",
                    markdown="# Hello",
                )
            )
        )

        with patch(
            "crawl._require_crawler",
            new=AsyncMock(side_effect=[crawler_one, crawler_two]),
        ), patch(
            "crawl.replace_crawler",
            new=AsyncMock(return_value=crawler_two),
        ) as replace_mock:
            page = await scrape_page("https://example.com/page")

        self.assertEqual(page.markdown, "# Hello")
        replace_mock.assert_awaited_once_with(crawler_one)
        self.assertEqual(crawler_one.arun.await_count, 1)
        self.assertEqual(crawler_two.arun.await_count, 1)

    async def test_scrape_page_does_not_retry_forever(self):
        closed_error = RuntimeError("Target page, context or browser has been closed")
        crawler_one = SimpleNamespace(arun=AsyncMock(side_effect=closed_error))
        crawler_two = SimpleNamespace(arun=AsyncMock(side_effect=closed_error))

        with patch(
            "crawl._require_crawler",
            new=AsyncMock(side_effect=[crawler_one, crawler_two]),
        ), patch(
            "crawl.replace_crawler",
            new=AsyncMock(return_value=crawler_two),
        ) as replace_mock:
            with self.assertRaisesRegex(
                ValueError,
                "Target page, context or browser has been closed",
            ):
                await scrape_page("https://example.com/page")

        replace_mock.assert_awaited_once_with(crawler_one)
        self.assertEqual(crawler_one.arun.await_count, 1)
        self.assertEqual(crawler_two.arun.await_count, 1)

    async def test_site_partial_results_trigger_recycle_without_dropping_successes(self):
        crawler = SimpleNamespace(
            arun=AsyncMock(
                return_value=[
                    self._crawl_result(
                        success=True,
                        url="https://example.com/ok",
                        markdown="# OK",
                    ),
                    self._crawl_result(
                        success=False,
                        url="https://example.com/bad",
                        error_message="Target page, context or browser has been closed",
                    ),
                ]
            )
        )

        with patch(
            "crawl._require_crawler",
            new=AsyncMock(return_value=crawler),
        ), patch(
            "crawl.replace_crawler",
            new=AsyncMock(return_value=SimpleNamespace()),
        ) as replace_mock:
            pages, failures = await crawl_site_with_outcomes("https://example.com")

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].metadata["source_url"], "https://example.com/ok")
        self.assertEqual(
            failures,
            [
                {
                    "url": "https://example.com/bad",
                    "error": "Target page, context or browser has been closed",
                }
            ],
        )
        replace_mock.assert_awaited_once_with(crawler)


if __name__ == "__main__":
    unittest.main()
