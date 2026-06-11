from pydantic import BaseModel, Field


class SummaryModel(BaseModel):
    general_description: str = Field(
        description=(
            "1-2 factual sentences describing what the business or product is, who it serves, "
            "and what it does; lead with the brand name when identifiable"
        ),
    )
    key_advantages: str = Field(
        description=(
            "Concise list of the main competitive advantages or selling points supported by the "
            "context, written as short phrases separated by periods"
        ),
    )
    main_goal: str = Field(
        description=(
            "The primary business objective inferred from the site, such as signing up for a "
            "trial, booking a demo, making a purchase, or contacting sales; one clear sentence"
        ),
    )


class BusinessProfileRequest(BaseModel):
    context: str = Field(
        min_length=1,
        description="Raw page or site markdown, or other text about the business to summarize",
    )
