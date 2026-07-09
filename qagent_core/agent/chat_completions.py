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


def run_generative_agent_with_chat_completions(
    client: Any,
    model: str,
    system_prompt: str,
    user_goal: str,
    tool_functions: Dict[str, Any],
    trace: List[Dict[str, Any]],
    update_live,
    progress_placeholder=None,
    max_turns: int = MAX_AGENT_ITERATIONS,
    run_id: str = "",
    started_at: float = 0.0,
    runtime_state: Optional[Dict[str, int]] = None,
    tool_executor: Optional[ToolExecutor] = None,
):
    """기존 Chat Completions 기반 Tool loop. reasoning_effort는 전달하지 않는다."""
    messages = [
        {"role": "system", "content": system_prompt, "run_id": run_id},
        {"role": "user", "content": user_goal.strip()},
    ]

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
            return safe_error_message("timeout"), trace, safe_for_log(messages)
        if runtime_state["tool_calls"] >= tool_executor.max_tool_calls:
            return safe_error_message("limit"), trace, safe_for_log(messages)
        update_live(
            f"Turn {turn + 1}: Chat Completions에서 다음 Tool을 선택하는 중입니다."
        )

        try:
            request_timeout = tool_executor.deadline.bounded_timeout(60.0)
            if request_timeout <= 0:
                return safe_error_message("timeout"), trace, safe_for_log(messages)
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
                timeout=request_timeout,
            )
        except Exception as error:
            raise RuntimeError(safe_error_message("api", error)) from error

        try:
            msg = completion.choices[0].message
        except (AttributeError, IndexError, TypeError) as error:
            raise RuntimeError(safe_error_message("api", error)) from error
        assistant_message = {"role": "assistant", "content": msg.content or ""}

        if msg.tool_calls:
            assistant_message["tool_calls"] = []
            for tc in msg.tool_calls:
                assistant_message["tool_calls"].append(
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                )
            messages.append(assistant_message)

            tool_timed_out = False
            for tc in msg.tool_calls:
                name = tc.function.name
                raw_args = tc.function.arguments or "{}"
                info = TOOL_DISPLAY_INFO.get(name, {"label": name, "analysis": ""})
                update_live(f"{info.get('label', name)} 실행 중")
                result = tool_executor.execute_raw(name, raw_args, turn=turn + 1)
                tool_timed_out = tool_timed_out or result.get("status") == "timeout"
                update_live(f"{info.get('label', name)} 완료")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            if tool_timed_out:
                return safe_error_message("timeout"), trace, safe_for_log(messages)
            continue

        final_answer = msg.content or "최종 응답이 비어 있습니다."
        messages.append({"role": "assistant", "content": final_answer})
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
        return final_answer, trace, safe_for_log(messages)

    fallback_answer = (
        "최대 tool 호출 턴에 도달했습니다. 다시 실행하거나 지시문을 더 구체화하세요."
    )
    fallback_answer = ensure_virtual_patch_followup_tools(
        fallback_answer, trace, tool_functions, update_live, tool_executor=tool_executor
    )
    return fallback_answer, trace, safe_for_log(messages)
