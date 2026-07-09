from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from qagent_core.config import (
    AGENT_TIMEOUT_SECONDS,
    MAX_AGENT_ITERATIONS,
    MAX_TOOL_CALLS,
)
from qagent_core.runtime import new_run_id, safe_error_message, safe_for_log
from qagent_core.tool_executor import ToolExecutor
from qagent_core.tool_registry import TOOL_SCHEMAS

from .followup import ensure_virtual_patch_followup_tools

from .presentation import TOOL_DISPLAY_INFO, summarize_tool_result


def convert_chat_tools_to_responses_tools(
    chat_tools: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Chat Completions 형식의 function tool schema를 Responses API 형식으로 변환한다."""
    response_tools = []
    for tool in chat_tools:
        if tool.get("type") != "function":
            continue
        fn = tool.get("function", {})
        if not fn.get("name"):
            continue
        response_tools.append(
            {
                "type": "function",
                "name": fn.get("name"),
                "description": fn.get("description", ""),
                "parameters": fn.get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            }
        )
    return response_tools


def obj_get(obj: Any, key: str, default: Any = None) -> Any:
    """Read an attribute or dictionary key from OpenAI SDK response objects."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_response_text(response: Any) -> str:
    """Responses API 응답에서 최종 텍스트를 최대한 안정적으로 추출한다."""
    output_text = obj_get(response, "output_text", None)
    if output_text:
        return str(output_text)

    parts = []
    for item in obj_get(response, "output", []) or []:
        if obj_get(item, "type") == "message":
            for content in obj_get(item, "content", []) or []:
                ctype = obj_get(content, "type")
                if ctype in {"output_text", "text"}:
                    text = obj_get(content, "text", "")
                    if text:
                        parts.append(str(text))
    return "\n".join(parts).strip()


def extract_response_function_calls(response: Any) -> List[Dict[str, Any]]:
    """Responses API output에서 function_call item을 추출한다."""
    calls = []
    for item in obj_get(response, "output", []) or []:
        if obj_get(item, "type") == "function_call":
            calls.append(
                {
                    "id": obj_get(item, "id", ""),
                    "call_id": obj_get(item, "call_id", ""),
                    "name": obj_get(item, "name", ""),
                    "arguments": obj_get(item, "arguments", "{}") or "{}",
                }
            )
    return calls


def run_generative_agent_with_responses_api(
    client: Any,
    model: str,
    system_prompt: str,
    user_goal: str,
    tool_functions: Dict[str, Any],
    trace: List[Dict[str, Any]],
    update_live,
    progress_placeholder=None,
    max_turns: int = MAX_AGENT_ITERATIONS,
    reasoning_effort: str = "none",
    run_id: str = "",
    started_at: float = 0.0,
    runtime_state: Optional[Dict[str, int]] = None,
    tool_executor: Optional[ToolExecutor] = None,
):
    """Responses API 기반 Tool loop. reasoning_effort와 function tools를 함께 사용할 때 사용한다."""
    response_tools = convert_chat_tools_to_responses_tools(TOOL_SCHEMAS)
    messages_for_log: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt, "run_id": run_id},
        {"role": "user", "content": user_goal.strip()},
    ]

    previous_response_id = None
    next_input: Any = user_goal.strip()

    runtime_state = runtime_state or {"tool_calls": 0}
    tool_executor = tool_executor or ToolExecutor(
        tool_functions=tool_functions,
        trace=trace,
        run_id=run_id,
        runtime_state=runtime_state,
        started_at=started_at,
        max_tool_calls=MAX_TOOL_CALLS,
        timeout_seconds=AGENT_TIMEOUT_SECONDS,
        result_summarizer=summarize_tool_result,
    )
    for turn in range(max_turns):
        if tool_executor.is_timed_out():
            return safe_error_message("timeout"), trace, safe_for_log(messages_for_log)
        if runtime_state["tool_calls"] >= tool_executor.max_tool_calls:
            return safe_error_message("limit"), trace, safe_for_log(messages_for_log)
        update_live(
            f"Turn {turn + 1}: Responses API에서 다음 Tool을 선택하는 중입니다."
        )

        request_kwargs: Dict[str, Any] = {
            "model": model,
            "instructions": system_prompt,
            "input": next_input,
            "tools": response_tools,
            "tool_choice": "auto",
        }
        if previous_response_id:
            request_kwargs["previous_response_id"] = previous_response_id
        if reasoning_effort and reasoning_effort != "none":
            request_kwargs["reasoning"] = {"effort": reasoning_effort}

        try:
            request_timeout = tool_executor.deadline.bounded_timeout(60.0)
            if request_timeout <= 0:
                return (
                    safe_error_message("timeout"),
                    trace,
                    safe_for_log(messages_for_log),
                )
            request_kwargs["timeout"] = request_timeout
            response = client.responses.create(**request_kwargs)
        except Exception as error:
            raise RuntimeError(safe_error_message("api", error)) from error
        previous_response_id = obj_get(response, "id", previous_response_id)

        response_text = extract_response_text(response)
        function_calls = extract_response_function_calls(response)

        assistant_log = {
            "role": "assistant",
            "content": response_text,
            "response_id": previous_response_id,
            "api": "responses",
        }
        if function_calls:
            assistant_log["tool_calls"] = [
                {
                    "id": call.get("id", ""),
                    "call_id": call.get("call_id", ""),
                    "type": "function",
                    "function": {
                        "name": call.get("name", ""),
                        "arguments": call.get("arguments", "{}"),
                    },
                }
                for call in function_calls
            ]
        messages_for_log.append(assistant_log)

        if not function_calls:
            final_answer = response_text or "최종 응답이 비어 있습니다."
            update_live("최종 분석 보고서 생성 완료")
            if progress_placeholder is not None:
                progress_placeholder.progress(1.0, text="Agent 분석 완료")
            final_answer = ensure_virtual_patch_followup_tools(
                final_answer,
                trace,
                tool_functions,
                update_live,
                tool_executor=tool_executor,
            )
            return final_answer, trace, safe_for_log(messages_for_log)

        tool_outputs = []
        tool_timed_out = False
        for call in function_calls:
            name = call.get("name", "")
            raw_args = call.get("arguments", "{}") or "{}"
            info = TOOL_DISPLAY_INFO.get(name, {"label": name, "analysis": ""})
            update_live(f"{info.get('label', name)} 실행 중")
            result = tool_executor.execute_raw(name, raw_args, turn=turn + 1)
            tool_timed_out = tool_timed_out or result.get("status") == "timeout"
            update_live(f"{info.get('label', name)} 완료")

            output_text = json.dumps(result, ensure_ascii=False)
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.get("call_id") or call.get("id"),
                    "output": output_text,
                }
            )
            messages_for_log.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("call_id") or call.get("id"),
                    "name": name,
                    "content": output_text,
                }
            )

        if tool_timed_out:
            return safe_error_message("timeout"), trace, safe_for_log(messages_for_log)
        next_input = tool_outputs

    return (
        "최대 Agent 반복 횟수에 도달했습니다. 지시문을 더 구체화하세요.",
        trace,
        safe_for_log(messages_for_log),
    )
