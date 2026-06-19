import bootstrap  # noqa: F401, E402

import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from main import app
from summary import agent as agent_module
from summary.schemas import CONTEXT_MAX_LENGTH, BusinessProfileRequest, SummaryModel
from summary.service import build_business_profile_user_message, summarize_business_profile

client = TestClient(app)

SAMPLE_CONTEXT = "# Acme Corp\n\nWe build widgets for enterprise customers."
SAMPLE_SUMMARY = SummaryModel(
    tone_style="professional",
    product_name="Acme Corp",
    general_description="Acme Corp builds enterprise widgets.",
    key_advantages="24/7 support. Same-day shipping.",
    main_goal="Request a quote for an enterprise deployment.",
    agent_description=(
        "A sales assistant for Acme Corp that helps enterprise customers learn about widget "
        "offerings and move toward requesting a deployment quote."
    ),
    topics=["Enterprise widgets", "Requesting a quote", "Customer support"],
)


def _mock_agent(response: dict | None = None):
    mock = AsyncMock()
    mock.ainvoke.return_value = response or {"structured_response": SAMPLE_SUMMARY}
    return mock


class BuildBusinessProfileUserMessageTest(unittest.TestCase):
    def test_returns_context_only_when_no_agent_metadata(self):
        self.assertEqual(
            build_business_profile_user_message(SAMPLE_CONTEXT),
            SAMPLE_CONTEXT,
        )

    def test_prepends_agent_metadata_when_provided(self):
        message = build_business_profile_user_message(
            SAMPLE_CONTEXT,
            agent_name="Aria",
            agent_role="sales",
            industry="enterprise software",
        )
        self.assertIn("Agent name: Aria", message)
        self.assertIn("Agent role: sales", message)
        self.assertIn("Industry: enterprise software", message)
        self.assertTrue(message.endswith(SAMPLE_CONTEXT))


class SummarizeBusinessProfileServiceTest(unittest.IsolatedAsyncioTestCase):
    @patch("summary.service.get_agent")
    async def test_returns_structured_response(self, get_agent):
        get_agent.return_value = _mock_agent()

        result = await summarize_business_profile(BusinessProfileRequest(context=SAMPLE_CONTEXT))

        self.assertEqual(result, SAMPLE_SUMMARY)
        get_agent.return_value.ainvoke.assert_awaited_once()

    @patch("summary.service.get_agent")
    async def test_forwards_optional_agent_metadata(self, get_agent):
        get_agent.return_value = _mock_agent()

        await summarize_business_profile(
            BusinessProfileRequest(
                context=SAMPLE_CONTEXT,
                agent_name="Aria",
                agent_role="sales",
                industry="enterprise software",
            ),
        )

        user_message = get_agent.return_value.ainvoke.await_args.args[0]["messages"][0]["content"]
        self.assertIn("Agent name: Aria", user_message)
        self.assertIn("Agent role: sales", user_message)
        self.assertIn("Industry: enterprise software", user_message)

    @patch("summary.service.get_agent")
    async def test_raises_when_structured_response_missing(self, get_agent):
        get_agent.return_value = _mock_agent({"messages": []})

        with self.assertRaisesRegex(ValueError, "LLM did not return structured output"):
            await summarize_business_profile(BusinessProfileRequest(context=SAMPLE_CONTEXT))

    @patch("summary.service.get_agent")
    async def test_raises_when_structured_response_is_none(self, get_agent):
        get_agent.return_value = _mock_agent({"structured_response": None})

        with self.assertRaisesRegex(ValueError, "LLM did not return structured output"):
            await summarize_business_profile(BusinessProfileRequest(context=SAMPLE_CONTEXT))


class BusinessProfileEndpointTest(unittest.TestCase):
    def setUp(self):
        agent_module._agent = None
        self._openai_key = os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self):
        agent_module._agent = None
        if self._openai_key is not None:
            os.environ["OPENAI_API_KEY"] = self._openai_key

    @patch("summary.service.get_agent")
    def test_business_profile_success(self, get_agent):
        get_agent.return_value = _mock_agent()

        response = client.post(
            "/business_profile",
            json={"context": SAMPLE_CONTEXT, "industry": "enterprise software"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["tone_style"], SAMPLE_SUMMARY.tone_style)
        self.assertEqual(data["product_name"], SAMPLE_SUMMARY.product_name)
        self.assertEqual(data["general_description"], SAMPLE_SUMMARY.general_description)
        self.assertEqual(data["key_advantages"], SAMPLE_SUMMARY.key_advantages)
        self.assertEqual(data["main_goal"], SAMPLE_SUMMARY.main_goal)
        self.assertEqual(data["agent_description"], SAMPLE_SUMMARY.agent_description)
        self.assertEqual(data["topics"], SAMPLE_SUMMARY.topics)

    @patch("summary.service.get_agent")
    def test_business_profile_accepts_optional_agent_metadata(self, get_agent):
        get_agent.return_value = _mock_agent()

        response = client.post(
            "/business_profile",
            json={
                "context": SAMPLE_CONTEXT,
                "agent_name": "Aria",
                "agent_role": "sales",
                "industry": "enterprise software",
            },
        )

        self.assertEqual(response.status_code, 200)
        user_message = get_agent.return_value.ainvoke.await_args.args[0]["messages"][0]["content"]
        self.assertIn("Agent name: Aria", user_message)
        self.assertIn("Industry: enterprise software", user_message)

    def test_business_profile_rejects_whitespace_only_context(self):
        response = client.post(
            "/business_profile",
            json={"context": "   "},
        )

        self.assertEqual(response.status_code, 422)

    def test_business_profile_rejects_overlength_context(self):
        response = client.post(
            "/business_profile",
            json={"context": "x" * (CONTEXT_MAX_LENGTH + 1)},
        )

        self.assertEqual(response.status_code, 422)

    @patch("summary.service.get_agent")
    def test_business_profile_llm_failure(self, get_agent):
        get_agent.return_value = _mock_agent({"structured_response": None})

        response = client.post(
            "/business_profile",
            json={"context": SAMPLE_CONTEXT},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("LLM did not return structured output", response.json()["detail"])

    def test_business_profile_missing_openai_api_key(self):
        response = client.post(
            "/business_profile",
            json={"context": SAMPLE_CONTEXT},
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
