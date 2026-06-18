from summary.agent import get_agent
from summary.schemas import BusinessProfileRequest, SummaryModel


def build_business_profile_user_message(
    context: str,
    agent_name: str | None = None,
    agent_role: str | None = None,
) -> str:
    metadata_lines: list[str] = []
    if agent_name:
        metadata_lines.append(f"- Agent name: {agent_name}")
    if agent_role:
        metadata_lines.append(f"- Agent role: {agent_role}")

    if not metadata_lines:
        return context

    metadata = "\n".join(metadata_lines)
    return (
        "Optional agent metadata (use when generating agent_description and topics; "
        "do not invent a conflicting name or role):\n"
        f"{metadata}\n\n---\n\n{context}"
    )


async def summarize_business_profile(request: BusinessProfileRequest) -> SummaryModel:
    user_message = build_business_profile_user_message(
        request.context,
        agent_name=request.agent_name,
        agent_role=request.agent_role,
    )
    response = await get_agent().ainvoke(
        {"messages": [
            {"role": "user", "content": user_message}
        ]},
    )
    result = response.get("structured_response")
    if result is None:
        raise ValueError("LLM did not return structured output")
    return result
