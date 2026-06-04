from typing import Any

from fastapi import APIRouter, HTTPException, Request

from crawl.dependencies import run_crawl_endpoint
from crawl.service import crawl_full_site, crawl_single_page, crawl_site_partial

router = APIRouter(tags=["crawl"])


@router.post("/crawl")
async def crawl(request: Request, url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    return await run_crawl_endpoint(request, lambda: crawl_single_page(url))


@router.post("/crawl/site")
async def crawl_site_endpoint(request: Request, url: str) -> list[dict[str, Any]]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    return await run_crawl_endpoint(request, lambda: crawl_full_site(url))


@router.post("/crawl/site/partial")
async def crawl_site_partial_endpoint(request: Request, url: str) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    return await run_crawl_endpoint(request, lambda: crawl_site_partial(url))
