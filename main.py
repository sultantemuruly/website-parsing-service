from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from crawl import MAX_CRAWL_PAGES, crawl_site, scrape_page
from chunking import build_rag_chunks, chunk_markdown_safe
from social_normalize import (
    ScrapeContext,
    extract_records,
    primary_record_type,
    records_to_chunks,
    top_level_metadata,
)
from social_platforms import (
    scrape_facebook_url,
    scrape_instagram_url,
    scrape_linkedin_url,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _metadata_dict(metadata) -> dict[str, Any]:
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    return {k: v for k, v in vars(metadata).items() if v is not None}


def _page_url(metadata) -> str:
    md = _metadata_dict(metadata)
    return md.get("source_url") or md.get("sourceURL", "")


def _normalize_page_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("title", "language", "description"):
        if value := raw.get(key):
            out[key] = value
    return out


def serialize_page(page, *, site_seed_url: str | None = None) -> dict[str, Any]:
    if not page.markdown:
        raise ValueError("No markdown")
    raw = _metadata_dict(page.metadata)
    source_url = _page_url(page.metadata)
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


@app.get("/")
async def read_root():
    return {"status": "ok"}


@app.post("/crawl")
async def crawl(url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return serialize_page(await scrape_page(url))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawl/site")
async def crawl_site_endpoint(url: str) -> list[dict[str, Any]]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return [serialize_page(page, site_seed_url=url) for page in await crawl_site(url)]
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawl/site/partial")
async def crawl_site_partial(url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    pages: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    try:
        for page in await crawl_site(url, limit=MAX_CRAWL_PAGES):
            try:
                pages.append(serialize_page(page, site_seed_url=url))
            except ValueError as e:
                failures.append({
                    "url": _page_url(page.metadata),
                    "error": str(e),
                })
    except Exception as e:
        if pages or failures:
            return {
                "partial": True,
                "site_seed_url": url,
                "pages": pages,
                "failures": failures,
                "error": str(e),
            }
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "partial": bool(failures),
        "site_seed_url": url,
        "pages": pages,
        "failures": failures,
    }


def serialize_social(ctx: ScrapeContext) -> dict[str, Any]:
    records = extract_records(ctx)
    chunks = records_to_chunks(records, ctx.platform)
    if not chunks:
        raise ValueError("No content extracted")

    return {
        "url": ctx.request_url,
        "platform": ctx.platform,
        "record_type": primary_record_type(ctx),
        "metadata": top_level_metadata(records, ctx),
        "raw": ctx.raw,
        "chunks": chunks,
    }


async def _social_endpoint(url: str, scrape) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return serialize_social(await scrape(url))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/linkedin")
async def linkedin(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_linkedin_url)


@app.post("/instagram")
async def instagram(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_instagram_url)


@app.post("/facebook")
async def facebook(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_facebook_url)


@app.post("/chunk")
def chunk(text: str) -> list[str]:
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        return chunk_markdown_safe(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 