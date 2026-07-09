from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from qagent_core.config import (
    AGENT_TIMEOUT_SECONDS,
    MAX_AGENT_ITERATIONS,
    MAX_TOOL_CALLS,
    get_secret,
)
from qagent_core.runtime import new_run_id, safe_error_message, safe_for_log
from qagent_core.tool_executor import ToolExecutor
from qagent_core.tool_registry import TOOL_SCHEMAS

from .chat_completions import run_generative_agent_with_chat_completions
from .prompts import build_system_prompt
from .presentation import render_live_trace, summarize_tool_result
from .responses import run_generative_agent_with_responses_api


class OpenAIKeyMissingError(RuntimeError):
    """Raised when the server has no OpenAI API key configured."""


def normalize_reasoning_effort(value: Optional[str]) -> str:
    """UI 입력값을 OpenAI reasoning.effort 값으로 정규화한다."""
    text = str(value or "").strip().lower()
    aliases = {
        "": "none",
        "없음": "none",
        "사용 안 함": "none",
        "off": "none",
        "disable": "none",
        "disabled": "none",
        "no": "none",
        "none": "none",
        "minimal": "minimal",
        "low": "low",
        "medium": "medium",
        "high": "high",
        "xhigh": "xhigh",
    }
    return aliases.get(text, text)


def normalize_api_mode(value: Optional[str]) -> str:
    """UI 표시값을 내부 API mode로 변환한다."""
    text = str(value or "auto").strip().lower()
    if text in {"responses api", "responses", "response", "응답 api"}:
        return "responses"
    if text in {"chat completions", "chat_completions", "chat", "채팅 완성"}:
        return "chat_completions"
    return "auto"


def choose_effective_openai_api(
    api_mode: str, reasoning_effort: str, model: str
) -> str:
    """
    function tools + reasoning_effort 조합은 Chat Completions에서 막히는 모델이 있으므로
    reasoning을 명시한 경우 자동으로 Responses API를 사용한다.
    """
    api_mode = normalize_api_mode(api_mode)
    reasoning_effort = normalize_reasoning_effort(reasoning_effort)

    if api_mode == "responses":
        return "responses"

    if api_mode == "chat_completions":
        return "chat_completions"

    if reasoning_effort != "none":
        return "responses"

    # gpt-5 계열은 Responses API가 reasoning/tool-call 조합에서 더 안전하다.
    if str(model).strip().lower().startswith("gpt-5"):
        return "responses"

    return "chat_completions"


def create_openai_client(api_key: Optional[str] = None):
    """Create an OpenAI client from the server-side API key.

    Args:
        api_key: Optional internal override for tests. Production UI/API callers
            should omit it so ``OPENAI_API_KEY`` is read from the environment.

    Returns:
        An initialized ``openai.OpenAI`` client.

    Raises:
        OpenAIKeyMissingError: ``OPENAI_API_KEY`` is not configured.
        ImportError: The OpenAI SDK is not installed.

    Security:
        The key is never returned, logged, or exposed through Streamlit/API
        responses. Do not pass user-entered keys into this function.
    """
    key = (api_key or get_secret("OPENAI_API_KEY")).strip()
    if not key:
        raise OpenAIKeyMissingError("OPENAI_API_KEY is not configured on the server.")
    from openai import OpenAI

    return OpenAI(api_key=key, timeout=min(60, AGENT_TIMEOUT_SECONDS), max_retries=0)


def run_generative_agent(
    model: str,
    user_goal: str,
    tool_functions: Dict[str, Any],
    max_turns: int = MAX_AGENT_ITERATIONS,
    live_placeholder=None,
    progress_placeholder=None,
    reasoning_effort: str = "none",
    api_mode: str = "auto",
    api_key: Optional[str] = None,
):
    """Run the tool-calling balance analysis Agent.

    Args:
        model: OpenAI model name.
        user_goal: User request or generated analysis prompt.
        tool_functions: Tool registry for the loaded dataset.
        max_turns: Maximum LLM/tool loop turns.
        live_placeholder: Optional Streamlit live trace placeholder.
        progress_placeholder: Optional Streamlit progress placeholder.
        reasoning_effort: OpenAI reasoning effort value.
        api_mode: Requested OpenAI API surface.
        api_key: Optional internal/test override. It must not come from UI or
            external API request bodies.

    Returns:
        ``(final_answer, trace, sanitized_messages)``.

    Raises:
        OpenAIKeyMissingError: The server has no ``OPENAI_API_KEY``.
        RuntimeError: Sanitized OpenAI API failure.

    Security:
        The OpenAI key is read server-side and is not included in tool traces,
        logs, messages, or endpoint responses.
    """
    client = create_openai_client(api_key=api_key)
    run_id = new_run_id()
    started_at = time.monotonic()
    runtime_state = {"tool_calls": 0}
    max_turns = min(max(int(max_turns), 1), MAX_AGENT_ITERATIONS)

    reasoning_effort = normalize_reasoning_effort(reasoning_effort)
    api_mode = normalize_api_mode(api_mode)
    effective_api = choose_effective_openai_api(api_mode, reasoning_effort, model)

    if api_mode == "chat_completions" and reasoning_effort != "none":
        # 사용자가 명시적으로 Chat Completions를 골랐더라도 오류 대신 Responses API로 안전 전환한다.
        effective_api = "responses"

    system_prompt = build_system_prompt()

    trace = []
    tool_executor = ToolExecutor(
        tool_functions=tool_functions,
        trace=trace,
        run_id=run_id,
        runtime_state=runtime_state,
        started_at=started_at,
        max_tool_calls=MAX_TOOL_CALLS,
        timeout_seconds=AGENT_TIMEOUT_SECONDS,
        result_summarizer=summarize_tool_result,
    )

    def update_live(current_message: str = ""):
        """Update optional Streamlit live trace widgets during an Agent run."""
        if live_placeholder is not None:
            live_placeholder.markdown(render_live_trace(trace, current_message))
        if progress_placeholder is not None:
            completed = len([step for step in trace if step.get("finished")])
            progress_placeholder.progress(
                min(completed / 14, 1.0), text=f"완료된 Tool: {completed}개"
            )

    update_live(
        f"LLM Agent가 분석 계획을 세우는 중입니다. API={effective_api}, model={model}, reasoning={reasoning_effort}"
    )

    if effective_api == "responses":
        return run_generative_agent_with_responses_api(
            client=client,
            model=model,
            system_prompt=system_prompt.strip(),
            user_goal=user_goal,
            tool_functions=tool_functions,
            trace=trace,
            update_live=update_live,
            progress_placeholder=progress_placeholder,
            max_turns=max_turns,
            reasoning_effort=reasoning_effort,
            run_id=run_id,
            started_at=started_at,
            runtime_state=runtime_state,
            tool_executor=tool_executor,
        )

    return run_generative_agent_with_chat_completions(
        client=client,
        model=model,
        system_prompt=system_prompt.strip(),
        user_goal=user_goal,
        tool_functions=tool_functions,
        trace=trace,
        update_live=update_live,
        progress_placeholder=progress_placeholder,
        max_turns=max_turns,
        run_id=run_id,
        started_at=started_at,
        runtime_state=runtime_state,
        tool_executor=tool_executor,
    )
