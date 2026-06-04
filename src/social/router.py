from typing import Any

from fastapi import APIRouter, HTTPException

from social.scrape.service import scrape_facebook, scrape_instagram, scrape_linkedin

router = APIRouter(tags=["social"])


async def _social_endpoint(url: str, scrape) -> dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        return await scrape(url)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/linkedin")
async def linkedin(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_linkedin)


@router.post("/instagram")
async def instagram(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_instagram)


@router.post("/facebook")
async def facebook(url: str) -> dict[str, Any]:
    return await _social_endpoint(url, scrape_facebook)
