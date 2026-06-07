from pydantic import BaseModel, Field


class SummaryModel(BaseModel):
    company_name: str = Field(description="Official or primary brand name of the business")
    business_summary: str = Field(
        description="Concise 2-4 sentence factual summary of what the business does; no fluff or marketing language",
    )


class BusinessProfileRequest(BaseModel):
    context: str = Field(
        min_length=1,
        description="Raw page or site markdown, or other text about the business to summarize",
    )
