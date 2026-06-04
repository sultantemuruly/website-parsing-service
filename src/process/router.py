from typing import Any

from fastapi import APIRouter, HTTPException

from process.mappers import crawled_page_from_request, scrape_context_from_request
from process.page.service import process_page_data
from process.schemas import ProcessPageRequest, ProcessSocialRequest
from process.social.service import process_social_data

router = APIRouter(tags=["process"])


@router.post("/process/page")
async def process_page(body: ProcessPageRequest) -> dict[str, Any]:
    if not body.markdown.strip():
        raise HTTPException(status_code=400, detail="markdown is required")
    try:
        return process_page_data(
            crawled_page_from_request(body),
            site_seed_url=body.site_seed_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/process/social")
async def process_social(body: ProcessSocialRequest) -> dict[str, Any]:
    try:
        return process_social_data(scrape_context_from_request(body))
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
