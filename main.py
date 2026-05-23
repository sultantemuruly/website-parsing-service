from typing import Any

from fastapi import FastAPI, HTTPException
from crawl import crawl_page, crawl_page_deep, crawl_page_deep_streaming
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_page(page) -> dict[str, Any]:
    return {
        "url": page.url,
        "raw_markdown": page.markdown.raw_markdown,
        "fit_markdown": page.markdown.fit_markdown,
        "images": page.media.get("images", []),
        "videos": page.media.get("videos", []),
        "audios": page.media.get("audios", []),
        "tables": page.media.get("tables", []),
        "metadata": page.metadata,
    }


@app.get("/")
async def read_root():
    return {"status": "ok"}


@app.post("/crawl")
async def crawl(url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return serialize_page(await crawl_page(url))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawl/site")
async def crawl_site(url: str) -> list[dict[str, Any]]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return [serialize_page(page) for page in await crawl_page_deep(url)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/site/partial")
async def crawl_site_partial(url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    pages: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    try:
        async for page in crawl_page_deep_streaming(url):
            if page.success:
                pages.append(serialize_page(page))
            else:
                failures.append(
                    {"url": page.url, "error": page.error_message or "Unknown error"}
                )
    except Exception as e:
        if pages or failures:
            return {
                "partial": True,
                "pages": pages,
                "failures": failures,
                "error": str(e),
            }
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "partial": bool(failures),
        "pages": pages,
        "failures": failures,
    }
