import os

from dotenv import load_dotenv
from langchain.agents import create_agent

from summary.schemas import SummaryModel

load_dotenv(override=True)

SYSTEM_PROMPT = """You summarize businesses from noisy website markdown or scraped page text.

Extract only facts supported by the provided context. Ignore navigation menus, repeated banners,
promotional widgets, cookie notices, pagination, and image/link markup.

Return structured output with:
- company_name: the official or primary brand name
- industry: the primary industry or sector
- business_summary: 2-4 factual sentences with no marketing fluff"""

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
