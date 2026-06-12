import bootstrap  # noqa: F401, E402

import unittest
from types import SimpleNamespace

from crawl.crawler import (
    CrawledPage,
    _classify_site_result,
    _markdown_text,
    _normalize_image_markdown,
    result_to_page,
)


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

    def test_uses_raw_markdown_from_generation_result(self):
        class MarkdownResult:
            raw_markdown = "[More](https://fbroker.kz/products/its)"
            fit_markdown = "filtered"

            def __str__(self) -> str:
                return self.fit_markdown

        page = result_to_page(_make_result(markdown=MarkdownResult()))

        self.assertEqual(page.markdown, "[More](https://fbroker.kz/products/its)")

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


class NormalizeImageMarkdownTest(unittest.TestCase):
    def test_linked_image_becomes_text_link(self):
        text = "[![thumb](img.png)](https://fbroker.kz/products/its)"
        self.assertEqual(
            _normalize_image_markdown(text),
            "[thumb](https://fbroker.kz/products/its)",
        )

    def test_strips_bare_images_but_preserves_links(self):
        text = (
            "![slide-0](https://fbroker.kz/file/x.png)\n\n"
            "[More](https://fbroker.kz/products/its)"
        )
        self.assertEqual(
            _normalize_image_markdown(text),
            "\n\n[More](https://fbroker.kz/products/its)",
        )

    def test_markdown_text_applies_normalization(self):
        result = _make_result(
            markdown=(
                "![slide-0](https://fbroker.kz/file/x.png)\n\n"
                "[More](https://fbroker.kz/products/its)"
            )
        )
        self.assertEqual(
            _markdown_text(result),
            "\n\n[More](https://fbroker.kz/products/its)",
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
