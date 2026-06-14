from summary.agent import get_agent
from summary.schemas import SummaryModel


async def summarize_business_profile(context: str) -> SummaryModel:
    response = await get_agent().ainvoke(
        {"messages": [
            {"role": "user", "content": context}
        ]},
    )
    result = response.get("structured_response")
    if result is None:
        raise ValueError("LLM did not return structured output")
    return result
