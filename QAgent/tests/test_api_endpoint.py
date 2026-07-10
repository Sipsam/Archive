import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import api


class AgentApiEndpointTests(unittest.TestCase):
    """Regression tests for the external FastAPI endpoint security boundary."""

    def setUp(self) -> None:
        self.previous_agent_key = os.environ.get("AGENT_API_KEY")
        self.previous_openai_key = os.environ.get("OPENAI_API_KEY")
        os.environ["AGENT_API_KEY"] = "test-agent-key"
        self.client = TestClient(api.app)

    def tearDown(self) -> None:
        if self.previous_agent_key is None:
            os.environ.pop("AGENT_API_KEY", None)
        else:
            os.environ["AGENT_API_KEY"] = self.previous_agent_key
        if self.previous_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = self.previous_openai_key

    def test_wrong_agent_api_key_returns_401_before_agent_run(self):
        response = self.client.post(
            "/api/agent/run",
            headers={"X-API-Key": "wrong"},
            json={"query": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["error"], "unauthorized")

    def test_missing_agent_api_key_header_returns_401_before_agent_run(self):
        response = self.client.post(
            "/api/agent/run",
            json={"query": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["error"], "unauthorized")

    def test_missing_openai_key_returns_503(self):
        os.environ["OPENAI_API_KEY"] = ""

        response = self.client.post(
            "/api/agent/run",
            headers={"Authorization": "Bearer test-agent-key"},
            json={"query": "test", "model": "gpt-4.1-mini", "stream": False},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["error"], "openai_api_key_missing")

    def test_empty_query_returns_400(self):
        response = self.client.post(
            "/api/agent/run",
            headers={"Authorization": "Bearer test-agent-key"},
            json={"query": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["error"], "empty_query")

    def test_too_long_query_returns_400(self):
        response = self.client.post(
            "/api/agent/run",
            headers={"Authorization": "Bearer test-agent-key"},
            json={"query": "x" * 12001},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["error"], "query_too_long")

    def test_rag_metadata_and_output_redaction_are_returned(self):
        os.environ["OPENAI_API_KEY"] = "sk-testsecret123456"

        with patch.object(
            api,
            "run_generative_agent",
            return_value=(
                "answer with sk-testsecret123456",
                [{"tool": "get_dataset_overview", "status": "ok"}],
                [],
            ),
        ):
            response = self.client.post(
                "/api/agent/run",
                headers={"Authorization": "Bearer test-agent-key"},
                json={
                    "query": "README API endpoint RAG guardrail",
                    "model": "gpt-4.1-mini",
                    "reasoning_effort": "medium",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("sk-testsecret123456", body["answer"])
        self.assertEqual(body["answer"], "answer with [REDACTED]")
        self.assertIn(body["metadata"]["rag_status"], {"ok", "insufficient_evidence"})
        self.assertIn("input_validation", body["metadata"]["execution_nodes"])
        self.assertIn("rag_search", body["metadata"]["execution_nodes"])


if __name__ == "__main__":
    unittest.main()
