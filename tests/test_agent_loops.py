"""API-free contract tests for the Agent's real Chat and Responses loops."""
from __future__ import annotations

import json
import threading
import time
import unittest
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from qagent_core.runtime import new_run_id, safe_error_message, safe_for_log
from qagent_core.tool_executor import ToolExecutor
from qagent_core.agent.chat_completions import run_generative_agent_with_chat_completions
from qagent_core.agent.followup import ensure_virtual_patch_followup_tools
from qagent_core.agent.responses import run_generative_agent_with_responses_api


def chat_tool_call(name: str, arguments: str = "{}", call_id: str = "call-1") -> Any:
    return SimpleNamespace(
        id=call_id, type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def chat_completion(*, text: str = "", tool_calls: list[Any] | None = None) -> Any:
    message = SimpleNamespace(content=text, tool_calls=tool_calls or [])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def response_call(name: str, arguments: str = "{}", call_id: str = "call-1") -> dict[str, Any]:
    return {
        "type": "function_call", "id": call_id, "call_id": call_id,
        "name": name, "arguments": arguments,
    }


class QueueEndpoint:
    def __init__(self, responses: list[Any]):
        self.queued = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if not self.queued:
            raise AssertionError("Fake endpoint response queue exhausted")
        return self.queued.pop(0)


class FakeOpenAIClient:
    def __init__(self, *, chat: list[Any] | None = None, responses: list[Any] | None = None):
        self.chat_endpoint = QueueEndpoint(chat or [])
        self.responses_endpoint = QueueEndpoint(responses or [])
        self.chat = SimpleNamespace(completions=self.chat_endpoint)
        self.responses = self.responses_endpoint


class AgentLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.functions = {
            "run_generative_agent_with_chat_completions": run_generative_agent_with_chat_completions,
            "run_generative_agent_with_responses_api": run_generative_agent_with_responses_api,
            "ensure_virtual_patch_followup_tools": ensure_virtual_patch_followup_tools,
        }

    def make_executor(self, tools: dict[str, Any], *, timeout: float = 2, max_calls: int = 10):
        trace: list[dict[str, Any]] = []
        state = {"tool_calls": 0}
        executor = ToolExecutor(
            tool_functions=tools, trace=trace, run_id="RUN-loop-test",
            runtime_state=state, started_at=time.monotonic(),
            max_tool_calls=max_calls, timeout_seconds=timeout,
        )
        return executor, trace, state

    def run_chat(self, client: FakeOpenAIClient, tools: dict[str, Any], **executor_options: Any):
        executor, trace, state = self.make_executor(tools, **executor_options)
        result = self.functions["run_generative_agent_with_chat_completions"](
            client=client, model="fake-model", system_prompt="system", user_goal="goal",
            tool_functions=tools, trace=trace, update_live=lambda *_: None,
            max_turns=10, run_id="RUN-loop-test", started_at=executor.started_at,
            runtime_state=state, tool_executor=executor,
        )
        return result, executor, state

    def run_responses(self, client: FakeOpenAIClient, tools: dict[str, Any], **executor_options: Any):
        executor, trace, state = self.make_executor(tools, **executor_options)
        result = self.functions["run_generative_agent_with_responses_api"](
            client=client, model="fake-model", system_prompt="system", user_goal="goal",
            tool_functions=tools, trace=trace, update_live=lambda *_: None,
            max_turns=10, run_id="RUN-loop-test", started_at=executor.started_at,
            runtime_state=state, tool_executor=executor,
        )
        return result, executor, state

    def test_chat_one_tool_then_final_response(self):
        client = FakeOpenAIClient(chat=[
            chat_completion(tool_calls=[chat_tool_call("echo", '{"value":"one"}')]),
            chat_completion(text="final-chat"),
        ])
        (answer, trace, _), _, state = self.run_chat(
            client, {"echo": lambda value: {"status": "ok", "value": value}}
        )

        self.assertEqual(answer, "final-chat")
        self.assertEqual([step["tool"] for step in trace], ["echo"])
        self.assertEqual(state["tool_calls"], 1)
        self.assertTrue(all(call["timeout"] <= 2 for call in client.chat_endpoint.calls))

    def test_responses_multiple_tools_preserve_order(self):
        client = FakeOpenAIClient(responses=[
            {"id": "r1", "output": [response_call("first", call_id="c1")]},
            {"id": "r2", "output": [response_call("second", call_id="c2")]},
            {"id": "r3", "output_text": "final-responses", "output": []},
        ])
        tools = {
            "first": lambda: {"status": "ok", "order": 1},
            "second": lambda: {"status": "ok", "order": 2},
        }
        (answer, trace, _), _, state = self.run_responses(client, tools)

        self.assertEqual(answer, "final-responses")
        self.assertEqual([step["tool"] for step in trace], ["first", "second"])
        self.assertEqual(state["tool_calls"], 2)
        self.assertEqual(client.responses_endpoint.calls[1]["previous_response_id"], "r1")

    def test_unknown_tool_and_malformed_arguments_are_returned_to_chat_loop(self):
        client = FakeOpenAIClient(chat=[
            chat_completion(tool_calls=[
                chat_tool_call("missing", "{}", "unknown"),
                chat_tool_call("echo", "{bad-json", "malformed"),
            ]),
            chat_completion(text="handled"),
        ])
        (_, trace, messages), _, state = self.run_chat(client, {"echo": lambda: {"status": "ok"}})

        self.assertEqual([step["error_message"] != "" for step in trace], [True, True])
        self.assertEqual([step["result"]["error_type"] for step in trace], ["unknown_tool", "json_parse_error"])
        self.assertEqual(state["tool_calls"], 0)
        self.assertEqual(sum(message.get("role") == "tool" for message in messages), 2)

    def test_empty_responses_object_returns_explicit_empty_answer(self):
        client = FakeOpenAIClient(responses=[{}])
        (answer, trace, _), _, state = self.run_responses(client, {})

        self.assertEqual(answer, "최종 응답이 비어 있습니다.")
        self.assertEqual(trace, [])
        self.assertEqual(state["tool_calls"], 0)

    def test_invalid_chat_response_raises_user_safe_runtime_error(self):
        client = FakeOpenAIClient(chat=[SimpleNamespace(choices=[])])
        with self.assertRaisesRegex(RuntimeError, "외부 AI API 요청에 실패"):
            self.run_chat(client, {})

    def test_tool_exception_is_traced_and_loop_continues(self):
        def fail():
            raise ValueError("internal detail")

        client = FakeOpenAIClient(chat=[
            chat_completion(tool_calls=[chat_tool_call("fail")]),
            chat_completion(text="recovered"),
        ])
        (answer, trace, _), _, state = self.run_chat(client, {"fail": fail})

        self.assertEqual(answer, "recovered")
        self.assertEqual(trace[0]["status"], "error")
        self.assertEqual(trace[0]["result"]["error_type"], "ValueError")
        self.assertEqual(state["tool_calls"], 1)

    def test_tool_timeout_is_traced_without_claiming_cancellation(self):
        completed = threading.Event()

        def slow():
            time.sleep(0.1)
            completed.set()
            return {"status": "ok"}

        client = FakeOpenAIClient(chat=[chat_completion(tool_calls=[chat_tool_call("slow")])])
        (answer, trace, _), _, state = self.run_chat(client, {"slow": slow}, timeout=0.02)

        self.assertIn("제한 시간을 초과", answer)
        self.assertEqual(trace[0]["status"], "timeout")
        self.assertFalse(trace[0]["cancelled"])
        self.assertEqual(state["tool_calls"], 1)
        self.assertTrue(completed.wait(0.5))

    def test_agent_deadline_blocks_api_call(self):
        client = FakeOpenAIClient(chat=[chat_completion(text="must-not-run")])
        (answer, trace, _), _, state = self.run_chat(client, {}, timeout=0)

        self.assertIn("제한 시간을 초과", answer)
        self.assertEqual(client.chat_endpoint.calls, [])
        self.assertEqual(trace, [])
        self.assertEqual(state["tool_calls"], 0)

    def test_max_tool_calls_stops_before_another_api_request(self):
        client = FakeOpenAIClient(chat=[
            chat_completion(tool_calls=[chat_tool_call("echo")]),
            chat_completion(text="must-not-run"),
        ])
        (answer, trace, _), _, state = self.run_chat(
            client, {"echo": lambda: {"status": "ok"}}, max_calls=1
        )

        self.assertIn("안전 제한", answer)
        self.assertEqual(len(client.chat_endpoint.calls), 1)
        self.assertEqual(len(trace), 1)
        self.assertEqual(state["tool_calls"], 1)

    def test_forced_virtual_patch_followups_obey_shared_call_limit(self):
        calls: list[str] = []
        tools = {
            "simulate_virtual_patch_impact": lambda **_: calls.append("simulate") or {"status": "ok"},
            "reflect_on_virtual_patch": lambda **_: calls.append("reflect") or {"status": "ok"},
        }
        executor, trace, state = self.make_executor(tools, max_calls=1)
        state["tool_calls"] = 1
        trace.append({
            "run_id": "RUN-loop-test", "turn": 1, "tool": "generate_virtual_patch_note",
            "result": {"status": "ok", "virtual_patch_note": {
                "player_team": "champion", "base_patch_version": "1.0",
                "virtual_patch_version": "1.1",
            }}, "success": True, "executed": True,
        })

        answer = self.functions["ensure_virtual_patch_followup_tools"](
            "final", trace, tools, lambda *_: None, tool_executor=executor,
        )

        self.assertEqual(calls, [])
        self.assertEqual(state["tool_calls"], 1)
        self.assertEqual([step["result"].get("error_type") for step in trace[1:]], [
            "tool_call_limit", "tool_call_limit",
        ])
        self.assertIn("앱 자동 보완", answer)
        self.assertIn("완료되지 않았습니다", answer)
        self.assertNotIn("시나리오 추정을 보완했습니다", answer)


if __name__ == "__main__":
    unittest.main()
