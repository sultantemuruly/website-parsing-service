import unittest
from types import SimpleNamespace

from crawl import CrawledPage, _classify_site_result, result_to_page


def _make_result(**kwargs):
    defaults = {
        "url": "https://example.com/page",
        "success": True,
        "markdown": "# Hello\n\nWorld",
        "metadata": {
            "title": "Example Page",
            "description": "A test page",
            "language": "en",
        },
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class ResultToPageTest(unittest.TestCase):
    def test_maps_url_and_metadata(self):
        page = result_to_page(_make_result())

        self.assertIsInstance(page, CrawledPage)
        self.assertEqual(page.markdown, "# Hello\n\nWorld")
        self.assertEqual(page.metadata["source_url"], "https://example.com/page")
        self.assertEqual(page.metadata["title"], "Example Page")
        self.assertEqual(page.metadata["description"], "A test page")
        self.assertEqual(page.metadata["language"], "en")

    def test_stringifies_markdown_object(self):
        class MarkdownResult:
            raw_markdown = "# From object"

            def __str__(self) -> str:
                return self.raw_markdown

        page = result_to_page(_make_result(markdown=MarkdownResult()))

        self.assertEqual(page.markdown, "# From object")

    def test_empty_markdown(self):
        page = result_to_page(_make_result(markdown=None))

        self.assertEqual(page.markdown, "")

    def test_omits_missing_metadata_fields(self):
        page = result_to_page(_make_result(metadata={"title": "Only title"}))

        self.assertEqual(
            page.metadata,
            {
                "source_url": "https://example.com/page",
                "title": "Only title",
            },
        )


class ClassifySiteResultTest(unittest.TestCase):
    def test_success_with_markdown(self):
        page, failure = _classify_site_result(_make_result(), "https://example.com")

        self.assertIsNotNone(page)
        self.assertIsNone(failure)

    def test_failed_crawl(self):
        page, failure = _classify_site_result(
            _make_result(success=False, error_message="Timeout"),
            "https://example.com",
        )

        self.assertIsNone(page)
        self.assertEqual(failure, {"url": "https://example.com/page", "error": "Timeout"})

    def test_empty_markdown(self):
        page, failure = _classify_site_result(
            _make_result(markdown="  "),
            "https://example.com",
        )

        self.assertIsNone(page)
        self.assertEqual(failure["error"], "No markdown")


if __name__ == "__main__":
    unittest.main()
