import bootstrap  # noqa: F401, E402

import unittest

from crawl.crawler import (
    CrawledPage,
    _classify_site_record,
    _markdown_text,
    _normalize_image_markdown,
    record_to_page,
)


def _make_record(**kwargs):
    defaults = {
        "url": "https://example.com/page",
        "status": "completed",
        "markdown": "# Hello\n\nWorld",
        "metadata": {
            "title": "Example Page",
            "description": "A test page",
            "language": "en",
        },
    }
    defaults.update(kwargs)
    return defaults


class RecordToPageTest(unittest.TestCase):
    def test_maps_url_and_metadata(self):
        page = record_to_page(_make_record())

        self.assertIsInstance(page, CrawledPage)
        self.assertEqual(page.markdown, "# Hello\n\nWorld")
        self.assertEqual(page.metadata["source_url"], "https://example.com/page")
        self.assertEqual(page.metadata["title"], "Example Page")
        self.assertEqual(page.metadata["description"], "A test page")
        self.assertEqual(page.metadata["language"], "en")

    def test_uses_top_level_metadata_fallbacks(self):
        page = record_to_page(
            _make_record(
                metadata={},
                title="Top title",
                language="fr",
                description="Top description",
            )
        )

        self.assertEqual(page.metadata["title"], "Top title")
        self.assertEqual(page.metadata["language"], "fr")
        self.assertEqual(page.metadata["description"], "Top description")

    def test_empty_markdown(self):
        page = record_to_page(_make_record(markdown=None))

        self.assertEqual(page.markdown, "")

    def test_omits_missing_metadata_fields(self):
        page = record_to_page(_make_record(metadata={"title": "Only title"}))

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

    def test_markdown_text_handles_nested_payloads(self):
        self.assertEqual(
            _markdown_text({"raw_markdown": "[More](https://fbroker.kz/products/its)"}),
            "[More](https://fbroker.kz/products/its)",
        )


class ClassifySiteRecordTest(unittest.TestCase):
    def test_success_with_markdown(self):
        page, failure = _classify_site_record(_make_record(), "https://example.com")

        self.assertIsNotNone(page)
        self.assertIsNone(failure)

    def test_failed_crawl(self):
        page, failure = _classify_site_record(
            _make_record(status="errored", error="Timeout"),
            "https://example.com",
        )

        self.assertIsNone(page)
        self.assertEqual(failure, {"url": "https://example.com/page", "error": "Timeout"})

    def test_empty_markdown(self):
        page, failure = _classify_site_record(
            _make_record(markdown="  "),
            "https://example.com",
        )

        self.assertIsNone(page)
        self.assertEqual(failure["error"], "No markdown")


if __name__ == "__main__":
    unittest.main()
