from contextlib import asynccontextmanager
from typing import Any

from crawl4ai import AsyncWebCrawler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from crawl import (
    MAX_CRAWL_PAGES,
    browser_config,
    clear_crawler,
    crawl_site,
    init_crawler,
    scrape_page,
)
from process import (
    ProcessPageRequest,
    ProcessSocialRequest,
    crawled_page_from_request,
    page_url,
    process_page_data,
    process_social_data,
    scrape_context_from_request,
)
from social_platforms import (
    scrape_facebook_url,
    scrape_instagram_url,
    scrape_linkedin_url,
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with AsyncWebCrawler(config=browser_config()) as crawler:
        init_crawler(crawler)
        try:
            yield
        finally:
            clear_crawler()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"status": "ok"}


@app.post("/crawl")
async def crawl(url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return process_page_data(await scrape_page(url))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/crawl/site")
async def crawl_site_endpoint(url: str) -> list[dict[str, Any]]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return [process_page_data(page, site_seed_url=url) for page in await crawl_site(url)]
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
                pages.append(process_page_data(page, site_seed_url=url))
            except ValueError as e:
                failures.append({
                    "url": page_url(page.metadata),
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


@app.post("/process/page")
async def process_page(body: ProcessPageRequest) -> dict[str, Any]:
    if not body.markdown.strip():
        raise HTTPException(status_code=400, detail="markdown is required")
    try:
        return process_page_data(
            crawled_page_from_request(body),
            site_seed_url=body.site_seed_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/social")
async def process_social(body: ProcessSocialRequest) -> dict[str, Any]:
    try:
        return process_social_data(scrape_context_from_request(body))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _social_endpoint(url: str, scrape) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return process_social_data(await scrape(url))
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
