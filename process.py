"""Transform crawled or scraped payloads into RAG-ready chunk responses."""

from typing import Any

from pydantic import BaseModel, Field

from chunking import build_rag_chunks
from crawl import CrawledPage
from social_normalize import (
    ScrapeContext,
    extract_records,
    primary_record_type,
    records_to_chunks,
    top_level_metadata,
)


def _metadata_dict(metadata) -> dict[str, Any]:
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    return {k: v for k, v in vars(metadata).items() if v is not None}


def page_url(metadata) -> str:
    md = _metadata_dict(metadata)
    return md.get("source_url") or md.get("sourceURL", "")


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


def process_social_data(ctx: ScrapeContext) -> dict[str, Any]:
    records = extract_records(ctx)
    chunks = records_to_chunks(records, ctx.platform)
    if not chunks:
        raise ValueError("No content extracted")

    return {
        "url": ctx.request_url,
        "platform": ctx.platform,
        "scraper_type": ctx.scraper_type,
        "record_type": primary_record_type(ctx),
        "metadata": top_level_metadata(records, ctx),
        "raw": ctx.raw,
        "chunks": chunks,
    }


class ProcessPageRequest(BaseModel):
    markdown: str = Field(min_length=1)
    url: str = Field(min_length=1)
    title: str | None = None
    language: str | None = None
    description: str | None = None
    site_seed_url: str | None = None


class ProcessSocialRequest(BaseModel):
    platform: str = Field(min_length=1)
    scraper_type: str = Field(min_length=1)
    request_url: str = Field(min_length=1)
    raw: Any


def crawled_page_from_request(body: ProcessPageRequest) -> CrawledPage:
    metadata: dict[str, Any] = {"source_url": body.url}
    for key in ("title", "language", "description"):
        if value := getattr(body, key):
            metadata[key] = value
    return CrawledPage(markdown=body.markdown, metadata=metadata)


def scrape_context_from_request(body: ProcessSocialRequest) -> ScrapeContext:
    return ScrapeContext(
        platform=body.platform,
        scraper_type=body.scraper_type,
        request_url=body.request_url,
        raw=body.raw,
    )
