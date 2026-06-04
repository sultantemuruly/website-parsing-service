from typing import Any

from crawl.crawler import CrawledPage
from process.mappers import page_url
from shared.chunking import build_rag_chunks


def _metadata_dict(metadata) -> dict[str, Any]:
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    return {k: v for k, v in vars(metadata).items() if v is not None}


def _normalize_page_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("title", "language", "description"):
        if value := raw.get(key):
            out[key] = value
    return out


def process_page_data(
    page: CrawledPage,
    *,
    site_seed_url: str | None = None,
) -> dict[str, Any]:
    if not page.markdown:
        raise ValueError("No markdown")
    raw = _metadata_dict(page.metadata)
    source_url = page_url(page.metadata)
    page_metadata = _normalize_page_metadata(raw)
    return {
        "url": source_url,
        "markdown": page.markdown,
        "metadata": page_metadata,
        "chunks": build_rag_chunks(
            page.markdown,
            source_url=source_url,
            title=page_metadata.get("title"),
            language=page_metadata.get("language"),
            site_seed_url=site_seed_url,
        ),
    }
