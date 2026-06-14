from fastapi import APIRouter, HTTPException

from summary.schemas import BusinessProfileRequest, SummaryModel
from summary.service import summarize_business_profile

router = APIRouter(tags=["summary"])


@router.post("/business_profile")
async def business_profile(body: BusinessProfileRequest) -> SummaryModel:
    try:
        return await summarize_business_profile(body.context)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
