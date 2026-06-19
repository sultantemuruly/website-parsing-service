from typing import Literal

from pydantic import BaseModel, Field, field_validator

CONTEXT_MAX_LENGTH = 200_000
TONE_STYLES = (
    "friendly",
    "professional",
    "formal",
    "casual",
    "empathetic",
    "assertive",
    "humorous",
)
ToneStyle = Literal[
    "friendly",
    "professional",
    "formal",
    "casual",
    "empathetic",
    "assertive",
    "humorous",
]


class SummaryModel(BaseModel):
    tone_style: ToneStyle = Field(
        description=(
            "The single best-fit tone style for the business or brand voice, chosen from the "
            "allowed tone styles based on the context and any provided industry metadata"
        ),
    )
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
            "A third-person description of the customer-facing AI agent — what it is, who it "
            "helps, and what it is for. Write as profile or product copy (e.g. 'A sales assistant "
            "for Acme that helps customers compare plans…'), not as instructions to the agent. "
            "Do not use second person or imperative voice ('You are…', 'Help users…', 'Act as…'). "
            "Do not restate general_description, key_advantages, or main_goal. When agent name "
            "or role metadata is provided in the request, reflect them accurately; otherwise infer "
            "conservatively from the context."
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
    agent_name: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional display name for the customer-facing agent; when provided, use it in "
            "agent_description without inventing a different name"
        ),
    )
    agent_role: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional role label for the agent (e.g. sales, support, appointments); when "
            "provided, tailor agent_description and topics to that role without contradicting "
            "the context"
        ),
    )
    industry: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional business industry label (e.g. healthcare, fintech, retail); when "
            "provided, use it as an additional clue for tone_style and other summary fields"
        ),
    )

    @field_validator("context", mode="before")
    @classmethod
    def strip_and_require_non_empty(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
        if isinstance(value, str) and not value:
            raise ValueError("context is required")
        return value

    @field_validator("agent_name", "agent_role", "industry", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return value
