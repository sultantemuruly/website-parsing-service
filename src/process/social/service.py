from typing import Any

from social.normalize.extractor import (
    extract_records,
    primary_record_type,
    records_to_chunks,
    top_level_metadata,
)
from social.normalize.models import ScrapeContext


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
