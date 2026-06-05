from typing import Any

from pydantic import BaseModel, Field


class ProcessPageRequest(BaseModel):
    markdown: str = Field(min_length=1)
    url: str = Field(min_length=1)
    title: str | None = None
    language: str | None = None
    description: str | None = None
    site_seed_url: str | None = None


class ProcessSocialRequest(BaseModel):
    platform: str = Field(min_length=1)
    scraper_type: str = Field(min_length=1)
    request_url: str = Field(min_length=1)
    raw: Any
