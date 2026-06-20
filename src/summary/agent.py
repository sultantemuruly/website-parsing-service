import os

from dotenv import load_dotenv
from langchain.agents import create_agent

from summary.schemas import SummaryModel, TONE_STYLES

load_dotenv(override=True)

SYSTEM_PROMPT = """You summarize businesses from noisy website markdown or scraped page text.

Extract only facts supported by the provided context. Ignore navigation menus, repeated banners,
promotional widgets, cookie notices, pagination, and image/link markup.

The user message may include optional business metadata (name, role, and/or industry) before the
business context. When present, use those values to improve tone_style, agent_description, and
topics — do not invent a conflicting name, role, or industry. When absent, infer conservatively
from the context only.

Return structured output with:
- tone_style: choose exactly one value from the allowed tone styles:
  {tone_styles}. Base this on the business's brand voice, audience, and industry. If the context
  is sparse, default to "professional".
- product_name: the official product or brand name exactly as it appears in the context. If only
  a company name is given and no distinct product name, use the company name. Never invent or
  rebrand.
- general_description: 1-2 factual sentences describing what the business or product is, who it
  serves, and what it does. Start with the brand name when identifiable. Write as if explaining
  the company to someone who has never seen the website. Infer the offering from headings, CTAs,
  and customer quotes when needed, but phrase it as what the company offers — not what a page
  shows. Do not mention page structure or UI (e.g. "on this page", "the site contains",
  "video testimonials are presented", sections, menus, sliders, or lists of links).
- key_advantages: the main competitive advantages or selling points, as short factual phrases
  separated by periods (e.g. "Works 24/7. Setup in 5 minutes. CRM integration.").
- main_goal: the primary conversion or business objective implied by the site, in one clear
  sentence (e.g. sign up for a trial, book a demo, request a quote, contact sales).
- agent_description: a third-person description of the customer-facing AI agent — what it is,
  who it helps, and what it is for. Write as profile or product copy (e.g. "A sales assistant
  for Acme that helps customers compare enterprise widget plans…"). This is NOT a system prompt
  or instruction block — never use second person or imperative voice ("You are…", "Help users…",
  "Act as…", "Do not…"). Do NOT repeat or paraphrase general_description, key_advantages, or
  main_goal. When agent name metadata is provided, refer to the agent by that name. When agent
  role metadata is provided, describe the agent's purpose in terms of that role. Ground every
  claim in the context; if scope is unclear, keep the description short and conservative.
- topics: a list of permissible conversation topics the agent may discuss. Include only subjects
  clearly evidenced in the context (e.g. "Pricing and plans", "Product features", "Shipping and
  returns", "Account setup", "Contacting support"). When agent role metadata is provided, prefer
  topics aligned with that role but still only if supported by the context. Each item is a short
  noun phrase. Do not add topics the business might plausibly cover but that are absent from the
  source. Include at least one topic when any business subject is identifiable.

Language rule — follow exactly:
1. Identify the single dominant language of the source content by looking at the majority of
   body text (headings, descriptions, CTAs). Ignore isolated foreign words, proper nouns,
   brand names, and navigation labels when determining the dominant language.
2. Write every output field entirely in that one language. Never mix languages within a field
   or across fields.
3. If the dominant language cannot be determined with confidence, default to English.
4. Do not translate proper nouns, brand names, or product names — keep them as-is regardless
   of the output language.

Do not invent features, integrations, goals, policies, or topics that are not supported by the
context."""

_agent = None


def get_agent():
    global _agent
    if _agent is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set")
        _agent = create_agent(
            model="openai:gpt-5.5",
            system_prompt=SYSTEM_PROMPT.format(tone_styles=", ".join(f'"{style}"' for style in TONE_STYLES)),
            response_format=SummaryModel,
        )
    return _agent
