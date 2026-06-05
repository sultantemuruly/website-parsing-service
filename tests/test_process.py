import bootstrap  # noqa: F401, E402

import json
import unittest
from pathlib import Path

from crawl.crawler import CrawledPage
from fastapi.testclient import TestClient
from main import app
from process.mappers import crawled_page_from_request, scrape_context_from_request
from process.page.service import process_page_data
from process.schemas import ProcessPageRequest, ProcessSocialRequest
from process.social.service import process_social_data
from social.normalize.models import ScrapeContext

FIXTURES = Path(__file__).parent / "fixtures"
client = TestClient(app)


class ProcessPageDataTest(unittest.TestCase):
    def test_builds_chunks_with_metadata(self):
        page = CrawledPage(
            markdown="# Hello\n\nWorld " * 50,
            metadata={
                "source_url": "https://example.com/page",
                "title": "Example Page",
                "language": "en",
            },
        )
        result = process_page_data(page, site_seed_url="https://example.com")

        self.assertEqual(result["url"], "https://example.com/page")
        self.assertEqual(result["metadata"], {"title": "Example Page", "language": "en"})
        self.assertTrue(result["chunks"])
        chunk = result["chunks"][0]
        self.assertEqual(chunk["metadata"]["content_type"], "web_page")
        self.assertEqual(chunk["metadata"]["source_url"], "https://example.com/page")
        self.assertEqual(chunk["metadata"]["chunk_index"], 0)
        self.assertEqual(chunk["metadata"]["site_seed_url"], "https://example.com")

    def test_raises_when_markdown_empty(self):
        page = CrawledPage(markdown="", metadata={"source_url": "https://example.com"})
        with self.assertRaises(ValueError):
            process_page_data(page)


class ProcessSocialDataTest(unittest.TestCase):
    def setUp(self):
        raw = json.loads((FIXTURES / "linkedin_profile.json").read_text())
        self.ctx = ScrapeContext(
            platform="linkedin",
            scraper_type="profiles",
            request_url="https://www.linkedin.com/in/jane-doe",
            raw=raw,
        )

    def test_response_includes_scraper_type(self):
        response = process_social_data(self.ctx)
        self.assertEqual(response["scraper_type"], "profiles")
        self.assertEqual(response["record_type"], "profile")
        self.assertTrue(response["chunks"])

    def test_raises_when_no_content(self):
        ctx = ScrapeContext(
            platform="facebook",
            scraper_type="posts_by_profile",
            request_url="https://www.facebook.com/example",
            raw=[{"url": "https://www.facebook.com/post/1"}],
        )
        with self.assertRaises(ValueError):
            process_social_data(ctx)


class ProcessRequestHelpersTest(unittest.TestCase):
    def test_crawled_page_from_request(self):
        body = ProcessPageRequest(
            markdown="# Title",
            url="https://example.com",
            title="Title",
        )
        page = crawled_page_from_request(body)
        self.assertEqual(page.markdown, "# Title")
        self.assertEqual(page.metadata["source_url"], "https://example.com")
        self.assertEqual(page.metadata["title"], "Title")

    def test_scrape_context_from_request(self):
        body = ProcessSocialRequest(
            platform="linkedin",
            scraper_type="profiles",
            request_url="https://www.linkedin.com/in/jane-doe",
            raw={"name": "Jane"},
        )
        ctx = scrape_context_from_request(body)
        self.assertEqual(ctx.platform, "linkedin")
        self.assertEqual(ctx.scraper_type, "profiles")
        self.assertEqual(ctx.raw, {"name": "Jane"})


class ProcessPageEndpointTest(unittest.TestCase):
    def test_process_page_success(self):
        response = client.post(
            "/process/page",
            json={
                "markdown": "# Hello\n\nWorld",
                "url": "https://example.com/page",
                "title": "Hello",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["url"], "https://example.com/page")
        self.assertEqual(data["metadata"]["title"], "Hello")
        self.assertTrue(data["chunks"])

    def test_process_page_rejects_empty_markdown(self):
        response = client.post(
            "/process/page",
            json={"markdown": "   ", "url": "https://example.com"},
        )
        self.assertEqual(response.status_code, 400)


class ProcessSocialEndpointTest(unittest.TestCase):
    def test_process_social_success(self):
        raw = json.loads((FIXTURES / "linkedin_profile.json").read_text())
        response = client.post(
            "/process/social",
            json={
                "platform": "linkedin",
                "scraper_type": "profiles",
                "request_url": "https://www.linkedin.com/in/jane-doe",
                "raw": raw,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scraper_type"], "profiles")
        self.assertTrue(data["chunks"])

    def test_process_social_no_content(self):
        response = client.post(
            "/process/social",
            json={
                "platform": "facebook",
                "scraper_type": "posts_by_profile",
                "request_url": "https://www.facebook.com/example",
                "raw": [{"url": "https://www.facebook.com/post/1"}],
            },
        )
        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
