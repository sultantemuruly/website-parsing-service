from typing import Any

from crawl.crawler import CrawledPage
from process.schemas import ProcessPageRequest, ProcessSocialRequest
from social.normalize.models import ScrapeContext


def _metadata_dict(metadata) -> dict[str, Any]:
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    return {k: v for k, v in vars(metadata).items() if v is not None}


def page_url(metadata) -> str:
    md = _metadata_dict(metadata)
    return md.get("source_url") or md.get("sourceURL", "")


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


def crawl_page_payload(page: CrawledPage, *, site_seed_url: str | None = None) -> dict[str, Any]:
    raw = _metadata_dict(page.metadata)
    payload: dict[str, Any] = {
        "markdown": page.markdown,
        "url": page_url(page.metadata),
    }
    for key in ("title", "language", "description"):
        if value := raw.get(key):
            payload[key] = value
    if site_seed_url:
        payload["site_seed_url"] = site_seed_url
    return payload


def social_scrape_payload(ctx: ScrapeContext) -> dict[str, Any]:
    return {
        "platform": ctx.platform,
        "scraper_type": ctx.scraper_type,
        "request_url": ctx.request_url,
        "raw": ctx.raw,
    }
