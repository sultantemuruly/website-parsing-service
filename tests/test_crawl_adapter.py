import unittest
from types import SimpleNamespace

from crawl import CrawledPage, result_to_page


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


if __name__ == "__main__":
    unittest.main()
