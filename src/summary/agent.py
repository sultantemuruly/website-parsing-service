import os

from dotenv import load_dotenv
from langchain.agents import create_agent

from summary.schemas import SummaryModel

load_dotenv(override=True)

SYSTEM_PROMPT = """You summarize businesses from noisy website markdown or scraped page text.

Extract only facts supported by the provided context. Ignore navigation menus, repeated banners,
promotional widgets, cookie notices, pagination, and image/link markup.

Return structured output with:
- general_description: 1-2 factual sentences describing what the business or product is, who it
  serves, and what it does. Start with the brand name when identifiable.
- key_advantages: the main competitive advantages or selling points, as short factual phrases
  separated by periods (e.g. "Works 24/7. Setup in 5 minutes. CRM integration.").
- main_goal: the primary conversion or business objective implied by the site, in one clear
  sentence (e.g. sign up for a trial, book a demo, request a quote, contact sales).

Use the same language as the source content when it is clearly identifiable; otherwise use English.
Do not invent features, integrations, or goals that are not supported by the context."""

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set")
        _agent = create_agent(
            model="openai:gpt-5.2",
            system_prompt=SYSTEM_PROMPT,
            response_format=SummaryModel,
        )
    return _agent
