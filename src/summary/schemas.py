from pydantic import BaseModel, Field, field_validator

CONTEXT_MAX_LENGTH = 200_000


class SummaryModel(BaseModel):
    product_name: str = Field(
        description=(
            "The official product or brand name as stated in the context (company name if no "
            "distinct product name exists). Use the exact wording from the source when "
            "available; do not invent or rebrand."
        ),
    )
    general_description: str = Field(
        description=(
            "1-2 factual sentences describing what the business or product is, who it serves, "
            "and what it does; lead with the brand name when identifiable. Describe the "
            "business itself, not the webpage — no page layout, sections, videos, or UI elements."
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
    agent_description: str = Field(
        description=(
            "Instructions for a customer-facing AI agent: its role, tone, and behavioral "
            "boundaries. Do not restate what the business is, what it sells, or its advantages — "
            "those belong in other fields. Write in second person ('You are…') or imperative "
            "voice ('Act as…', 'Help users…'). Ground every instruction in the context."
        ),
    )
    topics: list[str] = Field(
        description=(
            "Permissible conversation topics the agent may discuss — only subjects clearly "
            "supported by the context (e.g. pricing, features, onboarding, support hours). "
            "Each item is a short noun phrase. Omit anything not evidenced in the source."
        ),
        min_length=1,
    )


class BusinessProfileRequest(BaseModel):
    context: str = Field(
        min_length=1,
        max_length=CONTEXT_MAX_LENGTH,
        description="Raw page or site markdown, or other text about the business to summarize",
    )

    @field_validator("context", mode="before")
    @classmethod
    def strip_and_require_non_empty(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
        if isinstance(value, str) and not value:
            raise ValueError("context is required")
        return value
