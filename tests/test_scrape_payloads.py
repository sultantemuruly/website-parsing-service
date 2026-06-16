import bootstrap  # noqa: F401, E402

from contextlib import asynccontextmanager
import json
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from crawl.crawler import CrawledPage, crawl_site_with_outcomes, scrape_page
from fastapi.testclient import TestClient
from main import app
from process.mappers import crawl_page_payload, social_scrape_payload
from process.schemas import ProcessPageRequest
from social.normalize.models import ScrapeContext

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
        with patch("crawl.service.scrape_page", new=AsyncMock(return_value=page)):
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
        with patch("social.scrape.service.scrape_linkedin_url", new=AsyncMock(return_value=ctx)):
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
            "crawl.service.crawl_site_with_outcomes",
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
            with patch("crawl.service.scrape_page", new=AsyncMock()) as scrape_mock:
                response = client.post("/crawl?url=https://example.com/page")
        finally:
            if had_existing:
                client.app.state.crawl_limiter = original
            else:
                delattr(client.app.state, "crawl_limiter")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], "Crawler is busy, retry later")
        scrape_mock.assert_not_called()
class BrowserRunAdapterTest(unittest.IsolatedAsyncioTestCase):
    async def test_scrape_page_uses_markdown_endpoint(self):
        with patch(
            "crawl.crawler._browser_run_request",
            new=AsyncMock(
                return_value="![hero](https://example.com/hero.png)\n\n[More](https://example.com)"
            ),
        ) as request_mock:
            page = await scrape_page("https://example.com/page")

        self.assertEqual(page.metadata["source_url"], "https://example.com/page")
        self.assertEqual(page.markdown, "\n\n[More](https://example.com)")
        request_mock.assert_awaited_once()
        args = request_mock.await_args.args
        kwargs = request_mock.await_args.kwargs
        self.assertEqual(args, ("POST", "/markdown"))
        self.assertEqual(kwargs["payload"]["url"], "https://example.com/page")

    async def test_crawl_site_collects_pages_and_failures_from_terminal_job(self):
        request_mock = AsyncMock(
            side_effect=[
                {"id": "job-123"},
                {"status": "running", "records": []},
                {"status": "completed", "records": []},
                {
                    "status": "completed",
                    "records": [
                        {
                            "status": "completed",
                            "url": "https://example.com/ok",
                            "markdown": "# OK",
                            "metadata": {"title": "OK"},
                        },
                        {
                            "status": "errored",
                            "url": "https://example.com/bad",
                            "error": "No markdown",
                        },
                    ],
                },
            ]
        )

        with patch("crawl.crawler._browser_run_request", new=request_mock):
            pages, failures = await crawl_site_with_outcomes("https://example.com")

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].metadata["source_url"], "https://example.com/ok")
        self.assertEqual(pages[0].metadata["title"], "OK")
        self.assertEqual(
            failures,
            [{"url": "https://example.com/bad", "error": "No markdown"}],
        )

    async def test_crawl_site_reports_terminal_job_failure_without_losing_pages(self):
        request_mock = AsyncMock(
            side_effect=[
                {"id": "job-123"},
                {"status": "running", "records": []},
                {"status": "cancelled_due_to_limits", "records": []},
                {
                    "status": "cancelled_due_to_limits",
                    "records": [
                        {
                            "status": "completed",
                            "url": "https://example.com/ok",
                            "markdown": "# OK",
                        }
                    ],
                },
            ]
        )

        with patch("crawl.crawler._browser_run_request", new=request_mock):
            pages, failures = await crawl_site_with_outcomes("https://example.com")

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].metadata["source_url"], "https://example.com/ok")
        self.assertEqual(
            failures,
            [
                {
                    "url": "https://example.com",
                    "error": "Crawl job ended with status: cancelled_due_to_limits",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
