from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from crawl import MAX_CRAWL_PAGES, crawl_site, scrape_page
from chunking import chunk_nlp_sentence

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
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


def serialize_page(page) -> dict[str, Any]:
    if not page.markdown:
        raise ValueError("No markdown content for page")
    metadata = _metadata_dict(page.metadata)
    return {
        "url": metadata.get("sourceURL", ""),
        "markdown": page.markdown,
        "metadata": metadata,
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
        return [serialize_page(page) for page in await crawl_site(url)]
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
                pages.append(serialize_page(page))
            except ValueError as e:
                failures.append({
                    "url": _metadata_dict(page.metadata).get("sourceURL", ""),
                    "error": str(e),
                })
    except Exception as e:
        if pages or failures:
            return {"partial": True, "pages": pages, "failures": failures, "error": str(e)}
        raise HTTPException(status_code=500, detail=str(e))

    return {"partial": bool(failures), "pages": pages, "failures": failures}


@app.post("/chunk")
def chunk(text: str) -> list[str]:
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        return chunk_nlp_sentence(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
